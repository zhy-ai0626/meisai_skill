#!/usr/bin/env python3
"""提交前合规自查（MCM/ICM）：机器能判定的格式与规则项，一次跑完。

为什么需要这个脚本
------------------
COMAP 的硬性条款几乎都是**违规不报错、后果却是降级或取消资格**的类型：
超 25 页、页眉缺控制号、出现学校/队员姓名、用了 AI 却没有
Report on Use of AI、题面要的 letter/memo 漏交。这些在 LaTeX 编译时一条都不会报错，
只能在 PDF 成品上查。本脚本把能机器判定的部分变成一条命令。

规则来源：`competitions/mcm/current_rules.md`（COMAP 2027 instructions +
"Use of AI Tools in COMAP Contests" v102025 + 当届题面）。规则每年可能变，
Stage 0 必须重新核对官方页面；本脚本只编码核对过的那一版。

用法
----
    python scripts/check_compliance.py --paper paper_output/2612345.pdf
    python scripts/check_compliance.py --paper 2612345.pdf --decision-log state/decision_log.json
    python scripts/check_compliance.py --paper 2612345.pdf --require letter --json

退出码：0 = 无 FAIL（WARN 与人工项不影响退出码）；1 = 有 FAIL，不要提交；2 = 无法运行。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _console  # noqa: E402

PAGE_LIMIT = 25
SIZE_LIMIT_MB = 25
MIN_FONT_PT = 12

CJK = re.compile(r"[一-鿿]")
AI_REPORT_RX = re.compile(r"Report\s+on\s+(the\s+)?Use\s+of\s+AI", re.I)
REFERENCES_RX = re.compile(r"^\s*(?:\d+(?:\.\d+)*\.?\s*)?(References|Bibliography|Works\s+Cited)\s*$",
                           re.I | re.M)
CONTENTS_RX = re.compile(r"^\s*(Table\s+of\s+)?Contents\s*$", re.I | re.M)
# 这些措辞一出现就是在报身份（不在参考文献里也不会是题面原文）
IDENTITY_HARD = re.compile(
    r"\b(Advisor|Adviser|Supervisor|Instructor|Team\s+members?|Student\s+ID|Coach)\s*[:：]", re.I)
# 机构词：参考文献里很常见（"University Press"），只查参考文献之前的正文，报 WARN
IDENTITY_SOFT = re.compile(r"\b(University|College|Institute\s+of\s+Technology|School\s+of)\b")

# 题面要求的额外交付物 → 在 PDF 里识别它的特征
DELIVERABLE_PATTERNS = {
    "letter": re.compile(r"^\s*(Dear\b|Letter\b|To\s*:)", re.I | re.M),
    "memo": re.compile(r"^\s*(MEMO(RANDUM)?\b|To\s*:|From\s*:|Subject\s*:)", re.I | re.M),
    "policy_brief": re.compile(r"(Policy\s+Brief|Policy\s+Recommendation)", re.I),
    "report": re.compile(r"(Non-?technical|Report\s+to|Executive\s+Summary)", re.I),
}

KNOWN_AI_TOOLS = re.compile(
    r"\b(ChatGPT|GPT-?\d|OpenAI|Claude|Gemini|Copilot|DeepSeek|Kimi|Ernie|Qwen|"
    r"Grammarly|DeepL|Baidu\s+(Translate|Fanyi))\b", re.I)

# 只能人工判断的项。脚本每升级一条为机器判定，就从这里删掉一条。
MANUAL_ITEMS = (
    "Summary Sheet 是否给出了每一问的方法 + 关键数值结论（而不是复述题目）",
    "letter/memo 是否写给题面指定的读者、用对方能懂的语言、给出可执行建议",
    "图表的坐标轴含义与单位是否齐全，灰度打印是否可读",
    "摘要与正文里每个数字能否在结果文件里查到同一个值"
    "（可先跑 scripts/check_numbers.py，它只查可追溯性，不查语义）",
    "每张非自制图片/表格是否在原位置标注了出处（COMAP 规则）",
    "AI 生成的参考文献是否逐条打开核对过",
)


class Report:
    """收集检查项。level: FAIL / WARN / MANUAL；ok=True 一律记 PASS。"""

    def __init__(self) -> None:
        self.items: list[dict] = []

    def add(self, cid: str, name: str, ok: bool | None,
            note: str = "", level: str = "FAIL", detail: str = "") -> None:
        """note 只在没通过时显示（解释怎么错、怎么修）；
        detail 无论通过与否都显示（观测到的值）。"""
        if ok is True:
            lvl = "PASS"
        elif ok is None:
            lvl = "MANUAL"
        else:
            lvl = level
        self.items.append({"id": cid, "name": name, "ok": ok,
                           "level": lvl, "note": note, "detail": detail})

    def count(self, level: str) -> int:
        return sum(1 for i in self.items if i["level"] == level)


def _page_index(pages: list[str], rx: re.Pattern, start: int = 1) -> int:
    """返回从 start 页起首次匹配的页码（1 起）；找不到返回 0。"""
    for i, text in enumerate(pages[start - 1:], start):
        if rx.search(text):
            return i
    return 0


def _body_font_size(reader, first: int = 1, max_pages: int = 8) -> float | None:
    """正文字号的众数（按字符数加权）。从第 first 页（0 起）取几页正文，
    调用方负责跳过 Summary Sheet 与目录——目录行多字少，会把众数拉偏。"""
    sizes: Counter = Counter()

    def visitor(text, cm, tm, font_dict, font_size):
        if not text or not text.strip() or not font_size:
            return
        scale = (tm[0] ** 2 + tm[1] ** 2) ** 0.5 * (cm[0] ** 2 + cm[1] ** 2) ** 0.5
        size = round(font_size * (scale or 1.0), 1)
        if 4 <= size <= 40:
            sizes[size] += len(text.strip())

    for page in reader.pages[first:first + max_pages]:
        try:
            page.extract_text(visitor_text=visitor)
        except Exception:  # pypdf 对个别字体会抛异常，字号检查降级为人工
            return None
    if not sizes:
        return None
    return sizes.most_common(1)[0][0]


def load_decision_log(path: str | None) -> dict:
    candidates = [Path(path)] if path else [Path.cwd() / "state" / "decision_log.json"]
    for p in candidates:
        if p.is_file():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                return data if isinstance(data, dict) else {}
            except (OSError, json.JSONDecodeError):
                if path:
                    raise
    return {}


def check_paper(pdf_path: str, rep: Report, *, control_number: str | None,
                required: list[str], ai_used: bool | None) -> dict:
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    pages = [(p.extract_text() or "") for p in reader.pages]
    n_pages = len(pages)
    all_text = "\n".join(pages)
    first = pages[0] if pages else ""
    size_mb = os.path.getsize(pdf_path) / 1024 / 1024

    # —— 文件 ——
    rep.add("size", "PDF < 25 MB", size_mb < SIZE_LIMIT_MB, detail="%.2f MB" % size_mb)
    stem = Path(pdf_path).stem
    if control_number:
        rep.add("filename", "文件名 = 控制号.pdf", stem == control_number,
                "COMAP 要求用 team control number 命名 PDF（例 %s.pdf）" % control_number,
                detail=Path(pdf_path).name)
    else:
        rep.add("filename", "文件名 = 控制号.pdf", bool(re.fullmatch(r"\d{7}", stem)) or None,
                "未提供控制号（--control-number 或 decision_log.paper_metadata），请人工确认",
                detail=Path(pdf_path).name)

    # —— Summary Sheet ——
    rep.add("summary_first", "第 1 页是 Summary Sheet",
            bool(re.search(r"Summary", first, re.I))
            and bool(re.search(r"Control\s+Number|Team\s*#", first, re.I))
            and bool(re.search(r"Problem\s+Chosen", first, re.I)),
            "第 1 页应是 COMAP Summary Sheet：含 Problem Chosen、Team Control Number 与 Summary；"
            "不要加封面")
    overflow = bool(CONTENTS_RX.search(first)) or bool(
        re.search(r"^\s*1\.?\s+Introduction\s*$", first, re.M))
    rep.add("summary_one_page", "Summary 未溢出/未混入正文", not overflow,
            "第 1 页出现了 Contents 或 Introduction：Summary Sheet 后应 \\clearpage")
    kw_first = bool(re.search(r"Key\s*words?\s*[:：]", first, re.I))
    kw_second = n_pages > 1 and bool(re.search(r"Key\s*words?\s*[:：]", pages[1], re.I))
    rep.add("summary_fits", "Summary 在一页内（Keywords 未被挤到第 2 页）",
            not (kw_second and not kw_first),
            "Keywords 出现在第 2 页 = Summary 溢出。删背景句、合并每问的方法句，"
            "不要缩字号（<12pt 违规）", level="WARN")

    # —— 页眉：每页控制号 + 页码 ——
    if control_number:
        missing = [i for i, t in enumerate(pages, 1) if control_number not in t]
        rep.add("header_control", "每页页眉有控制号", not missing,
                "缺控制号的页：%s。COMAP 要求每页页眉写 'Team # %s, Page N of M'"
                % (missing[:10], control_number),
                detail="%d/%d 页含 %s" % (n_pages - len(missing), n_pages, control_number))
    else:
        rep.add("header_control", "每页页眉有控制号", None, "未提供控制号，无法逐页核对")
    # 官方 Summary Sheet 模板第 1 页只印控制号不印页码，所以从第 2 页查起
    no_pageno = [i for i, t in enumerate(pages[1:], 2) if not re.search(r"Page\s+\d+", t, re.I)]
    rep.add("header_page", "第 2 页起每页有页码（Page N）", not no_pageno,
            "无 'Page N' 的页：%s" % no_pageno[:10], level="WARN")

    # —— 25 页上限：解答 = 第 1 页到 Report on Use of AI 之前 ——
    ai_report_page = _page_index(pages, AI_REPORT_RX, start=2)
    # 目录里也会出现 "Report on Use of AI"，要跳过目录页
    toc_page = _page_index(pages[:4], CONTENTS_RX)
    if ai_report_page and ai_report_page == toc_page:
        ai_report_page = _page_index(pages, AI_REPORT_RX, start=toc_page + 1)
    solution_pages = (ai_report_page - 1) if ai_report_page else n_pages
    rep.add("page_limit", "解答 ≤ 25 页", solution_pages <= PAGE_LIMIT,
            "Summary、目录、正文、letter/memo、参考文献、附录、代码全部计入；"
            "只有 Report on Use of AI 不计入。先砍附录代码，再压图",
            detail="解答 %d 页（PDF 共 %d 页%s）" % (
                solution_pages, n_pages,
                "，AI 报告从第 %d 页起" % ai_report_page if ai_report_page else ""))

    # —— 字号 ≥ 12pt ——
    body_pt = _body_font_size(reader, first=max(1, toc_page))
    if body_pt is None:
        rep.add("font_size", "正文字号 ≥ 12pt", None, "无法从 PDF 读出字号，请人工确认")
    else:
        rep.add("font_size", "正文字号 ≥ 12pt", body_pt >= MIN_FONT_PT - 0.6,
                "COMAP: readable font of at least 12-point type。缩字号换页数是违规",
                detail="正文字号众数 ≈ %.1f pt" % body_pt)

    # —— 英文 ——
    cjk = len(CJK.findall(all_text))
    rep.add("english", "论文为英文（无中文残留）", cjk == 0,
            "提取到 %d 个中文字符：图里的中文标签、表头、代码注释最常见" % cjk,
            level="FAIL" if cjk > 20 else "WARN")

    # —— 目录 / 参考文献 ——
    rep.add("contents", "有目录（Table of Contents）", bool(toc_page),
            "近年题面把 Table of Contents 列为应含部分；它计入 25 页", level="WARN")
    ref_page = 0
    for i in range(n_pages, 0, -1):  # 取最后一个 References 标题，避开目录里那条
        if REFERENCES_RX.search(pages[i - 1]) and i != toc_page:
            ref_page = i
            break
    rep.add("references", "有参考文献列表", bool(ref_page),
            "COMAP 要求记录所有外部来源（inline citation + reference list）")

    # —— 题面要求的交付物（letter / memo / policy brief ……）——
    for kind in required:
        rx = DELIVERABLE_PATTERNS.get(kind)
        body = "\n".join(pages[:solution_pages])
        if rx is None:
            rep.add("deliverable_" + kind, "题面交付物：%s" % kind, None,
                    "未知类型，请人工确认它在 25 页之内")
            continue
        rep.add("deliverable_" + kind, "题面交付物：%s" % kind, bool(rx.search(body)),
                "题面要求的 %s 没找到（它必须在 25 页解答之内）。漏交 = 没完成题目要求" % kind)

    # —— AI 披露 ——
    mentioned = sorted({m.group(0) for m in KNOWN_AI_TOOLS.finditer(
        "\n".join(pages[:solution_pages]))})
    if ai_used is None:
        ai_used = bool(mentioned) or bool(ai_report_page)
    if ai_used:
        rep.add("ai_report", "用了 AI → 有 Report on Use of AI", bool(ai_report_page),
                "COMAP AI 政策：在 25 页解答之后追加 'Report on Use of AI'（不计页数），"
                "逐条列工具、版本、query 与 output")
        ref_text = "\n".join(pages[ref_page - 1:solution_pages]) if ref_page else ""
        rep.add("ai_in_refs", "AI 工具列在参考文献里",
                bool(ref_text) and bool(KNOWN_AI_TOOLS.search(ref_text)),
                "COMAP 还要求 inline citation + 在参考文献里列出所用 AI 工具"
                "（render_ai_usage.py 生成的 ai_tool_references.md 可直接粘贴）",
                level="WARN")
    else:
        rep.add("ai_report", "未用 AI → 无需 AI 报告", True,
                detail="提交表单的 AI uses statement 选 No")

    # —— 匿名 ——
    pre_ref = "\n".join(pages[:ref_page - 1] if ref_page else pages[:solution_pages])
    hard = sorted({m.group(0) for m in IDENTITY_HARD.finditer(all_text)})
    rep.add("identity_hard", "无队员/导师身份字段", not hard,
            "命中 %s。学生、导师、学校名称不得出现在任何一页" % hard)
    soft = []
    for m in IDENTITY_SOFT.finditer(pre_ref):
        ctx = pre_ref[max(0, m.start() - 25):m.end() + 25].replace("\n", " ")
        soft.append(ctx)
    rep.add("identity_soft", "正文无机构名痕迹", not soft,
            "参考文献之前出现机构词，逐处确认不是本队学校：%s" % soft[:4], level="WARN")
    meta = reader.metadata or {}
    dirty = []
    for key in ("/Author", "/Creator", "/Subject", "/Keywords"):
        val = str(meta.get(key) or "").strip()
        if key == "/Author" and val:
            dirty.append("%s=%r" % (key, val))
        elif val and (IDENTITY_SOFT.search(val) or CJK.search(val)):
            dirty.append("%s=%r" % (key, val))
    rep.add("identity_meta", "PDF 元数据无身份信息", not dirty,
            "；".join(dirty) + "。Word 导出最常见：文件属性里的作者是本机用户名",
            detail="已检查 /Author /Creator /Subject /Keywords")

    # —— 编译残留 ——
    unresolved = len(re.findall(r"\?\?", all_text))
    rep.add("no_unresolved_ref", "无未解析的交叉引用", unresolved == 0,
            note="全文出现 %d 处 `??`，需要再编译一遍" % unresolved, level="WARN")
    placeholders = sorted(set(re.findall(r"MATHMODEL_[A-Z_]+|TITLE OF YOUR PAPER|1111111", all_text)))
    rep.add("no_placeholder", "无模板占位符", not placeholders, "残留：%s" % placeholders)

    return {"pages": n_pages, "solution_pages": solution_pages,
            "size_mb": round(size_mb, 2), "ai_used": ai_used,
            "ai_tools_mentioned": mentioned}


def stage9_fields(rep: Report) -> dict:
    """映射到 decision_log.stages.9.compliance_checks，避免手填。

    有贡献项落在『人工』上时返回 None(JSON null) 而不是 false——
    「没测到」和「测了没过」是两回事。null 会在 Stage 9 的 exit condition 上卡住。
    """
    def ok(*ids: str) -> bool | None:
        levels = [i["level"] for i in rep.items if i["id"] in ids
                  or any(i["id"].startswith(x) for x in ids if x.endswith("_"))]
        if any(l == "MANUAL" for l in levels):
            return None
        return all(l == "PASS" for l in levels)

    return {
        "rules_verified": rep.count("FAIL") == 0,
        "anonymity_passed": ok("identity_hard", "identity_meta"),
        "page_limit_passed": ok("page_limit", "size", "font_size", "summary_first"),
        "ai_disclosure_passed": ok("ai_report"),
        "deliverables_passed": ok("deliverable_"),
    }


def main(argv: list[str] | None = None) -> int:
    _console.init()
    ap = argparse.ArgumentParser(description="MCM/ICM 提交前合规自查（机器可判定项）")
    ap.add_argument("--paper", required=True, help="最终 PDF")
    ap.add_argument("--decision-log", help="默认 state/decision_log.json（存在时读取）")
    ap.add_argument("--control-number", help="覆盖 decision_log.paper_metadata.mcm_control_number")
    ap.add_argument("--require", action="append", default=None,
                    choices=sorted(DELIVERABLE_PATTERNS),
                    help="题面要求的额外交付物，可多次给；默认读 problem_meta.required_deliverables")
    ap.add_argument("--competition", default="mcm")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args(argv)

    if args.competition.lower() != "mcm":
        print("本脚本只编码 MCM/ICM 规则，不检查 %s。" % args.competition, file=sys.stderr)
        return 2
    if not os.path.exists(args.paper):
        print("找不到 %s" % args.paper, file=sys.stderr)
        return 2
    try:
        import pypdf  # noqa: F401
    except ImportError:
        print("需要 pypdf：pip install pypdf", file=sys.stderr)
        return 2
    try:
        log = load_decision_log(args.decision_log)
    except (OSError, json.JSONDecodeError) as exc:
        print("decision log 无法读取：%s" % exc, file=sys.stderr)
        return 2

    meta = log.get("paper_metadata") or {}
    control = args.control_number or (str(meta["mcm_control_number"])
                                      if meta.get("mcm_control_number") else None)
    required = args.require
    if required is None:
        required = list((log.get("problem_meta") or {}).get("required_deliverables") or [])
    ai_ledger = (log.get("compliance") or {}).get("ai_usage")
    ai_used = (len(ai_ledger) > 0) if isinstance(ai_ledger, list) else None

    rep = Report()
    info = check_paper(args.paper, rep, control_number=control,
                       required=required, ai_used=ai_used)
    fields = stage9_fields(rep)

    if args.json:
        print(json.dumps({"paper": args.paper, **info,
                          "checks": rep.items,
                          "compliance_checks": fields,
                          "manual": list(MANUAL_ITEMS),
                          "fails": rep.count("FAIL"),
                          "warns": rep.count("WARN")},
                         ensure_ascii=False, indent=2))
        return 1 if rep.count("FAIL") else 0

    print(_console.sym("=== %s 合规自查（MCM/ICM）===\n" % os.path.basename(args.paper)))
    for item in rep.items:
        tag = {"PASS": "✓ PASS", "FAIL": "✗ FAIL",
               "WARN": "⚠ WARN", "MANUAL": "  人工"}[item["level"]]
        line = "  %s  %s" % (tag, item["name"])
        if item["detail"]:
            line += "  (%s)" % item["detail"]
        if item["note"] and item["level"] != "PASS":
            line += "\n          " + item["note"]
        print(_console.sym(line))

    n_auto = sum(1 for i in rep.items if i["level"] != "MANUAL")
    print("\n机器可判定 %d 项：%d PASS，%d FAIL，%d WARN"
          % (n_auto, rep.count("PASS"), rep.count("FAIL"), rep.count("WARN")))
    print("\nStage 9 compliance_checks（可直接写入 decision_log）：")
    print("  " + json.dumps(fields, ensure_ascii=False))
    print("\n以下仍需人工确认：")
    for m in MANUAL_ITEMS:
        print("  [ ] " + m)
    if rep.count("FAIL"):
        print(_console.sym("\n★ 有 FAIL 项，不要提交。"))
    return 1 if rep.count("FAIL") else 0


if __name__ == "__main__":
    sys.exit(main())
