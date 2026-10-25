#!/usr/bin/env python3
"""维护期工具：从 O 奖论文的文本层统计 competitions/mcm/empirical.json。

输入是一个语料目录：
    <corpus>/<cid>.txt       pdftotext 输出（页之间用 \\f 分隔）
    <corpus>/<cid>.md        可选，MinerU 解析结果（扫描版论文）；存在时优先于 .txt
    <corpus>/_index*.json    [{cid, year, problem, src}, ...] 多个索引文件会合并

论文 PDF 本身**不随 skill 分发**（版权属于 COMAP 与作者），只分发统计结果。

用法:
    python scripts/build_empirical.py --corpus /path/to/corpus --out competitions/mcm/empirical.json
    python scripts/build_empirical.py --corpus /path/to/corpus --dump-summaries summaries.jsonl

统计口径（都是启发式，写进 empirical.json 的 _method 字段）：
- figure/table 数：正文里 "Figure N" / "Table N" 题注的最大编号
- references：References 标题之后的条目数（[n] 或 n. 开头的行）
- summary_words：第 1 页 "Summary" 到 "Keywords"（或页尾）之间的英文词数
- sections：目录页（或正文）里的一级标题，归一化后统计出现率
"""

from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import statistics
import sys
from collections import Counter, defaultdict

# 图题格式五花八门（"Figure 1:" "Figure 1 Our Work" "Figure 1Wildlife" "Fig. 1."），
# 而正文只会引用存在的图——所以取全文任意位置 "Figure N" 的最大编号。
FIG_RX = re.compile(r"\b(?:Figure|Fig\.)\s*(\d{1,3})(?!\d)", re.I)
TAB_RX = re.compile(r"\bTable\s*(\d{1,3})(?!\d)", re.I)
REF_HEAD_RX = re.compile(r"^\s*(?:#+\s*)?(?:\d+(?:\.\d+)*\.?\s*)?(References|Bibliography|Works\s+Cited)\s*$",
                         re.I | re.M)
REF_ITEM_RX = re.compile(r"^\s*(?:\[\d{1,3}\]|\d{1,3}\.\s+[A-Z])", re.M)
AI_RX = re.compile(r"Report\s+on\s+(?:the\s+)?Use\s+of\s+AI", re.I)
LETTER_RX = re.compile(r"^\s*(?:#+\s*)?Dear\b", re.I | re.M)
MEMO_RX = re.compile(r"^\s*(?:#+\s*)?(?:MEMO(?:RANDUM)?\b|To\s*:|From\s*:|Subject\s*:|Re\s*:)", re.I | re.M)
TOC_RX = re.compile(r"^\s*(?:#+\s*)?(?:Table\s+of\s+)?Contents\s*$", re.I | re.M)
KEYWORDS_RX = re.compile(r"Key\s*words?\s*[:：]?", re.I)
EQ_TAG_RX = re.compile(r"\((\d{1,3})\)\s*$", re.M)
WORD_RX = re.compile(r"[A-Za-z][A-Za-z\-']+")
NUM_RX = re.compile(r"(?<![A-Za-z])\d+(?:\.\d+)?\s*%?")

# 一级章节名归一化：左边正则命中 → 右边规范名
SECTION_CANON = [
    (r"introduction", "Introduction"),
    (r"background", "Background"),
    (r"restatement|problem\s+analysis|analysis\s+of\s+the\s+problem", "Problem Restatement/Analysis"),
    (r"assumption", "Assumptions"),
    (r"notation|symbol|nomenclature|variable", "Notations"),
    (r"data", "Data"),
    (r"sensitiv", "Sensitivity Analysis"),
    (r"robust|stabilit", "Robustness/Stability"),
    (r"validat|verif|test", "Model Validation"),
    (r"strength|weakness|evaluation\s+of|advantage|limitation", "Strengths & Weaknesses"),
    (r"extension|further|improvement|future", "Extensions/Future Work"),
    (r"conclusion|summary\s+of", "Conclusion"),
    (r"letter|memo|policy\s+brief|recommendation|advice|report\s+to|guide", "Letter/Memo/Report"),
    (r"reference|bibliograph", "References"),
    (r"appendix|appendices", "Appendix"),
    (r"report\s+on\s+(the\s+)?use\s+of\s+ai|use\s+of\s+ai", "Report on Use of AI"),
]
SECTION_CANON = [(re.compile(p, re.I), n) for p, n in SECTION_CANON]
# 目录里的一级标题行："1 Introduction" / "1. Introduction ....... 3" / "2 Assumptions\n\n2"
TOC_LINE_RX = re.compile(r"^\s*(\d{1,2})\.?\s+([A-Z][^\n]{2,120})$", re.M)
LEADER_RX = re.compile(r"[\s.·…]*\d{0,3}\s*$")
# MinerU 会把标题层级压平（多数都是 ##），所以一级标题按编号判断："## 3 Assumptions"；
# 没有编号的标题（"## Summary"）不当一级标题，但仍进任意层级统计。
MD_H1_RX = re.compile(r"^#{1,3}\s+\d{1,2}\.?\s+([A-Z][^\n]{2,80})$", re.M)


# Summary 里的方法关键词 → 方法类。只统计"提到了"，不判断用得对不对。
METHODS = {
    "ODE/微分方程": r"differential equation|\bODEs?\b|dynamical system|Runge|logistic (growth|model)",
    "PDE/有限元": r"\bPDEs?\b|partial differential|finite (element|volume|difference)|heat (equation|conduction)",
    "Lotka-Volterra/种群": r"Lotka|predator|population dynamic|Leslie",
    "物理/力学": r"Newton|kinetic|thermodynamic|energy (balance|conservation)|fluid|Archard|mechanic",
    "元胞自动机": r"cellular automat",
    "Agent 仿真": r"agent-based|multi-agent|\bABM\b",
    "蒙特卡洛": r"Monte Carlo|stochastic simulation|random simulation",
    "排队/离散事件": r"queu|discrete[- ]event",
    "线性/整数规划": r"linear programming|integer programming|\bMILP\b|\bILP\b|0-1 programming",
    "多目标/Pareto": r"multi-?objective|NSGA|Pareto",
    "启发式(GA/PSO/SA/蚁群)": r"genetic algorithm|\bGA\b|particle swarm|\bPSO\b|simulated annealing|ant colony|heuristic",
    "控制/动态规划": r"dynamic programming|optimal control|model predictive|\bMPC\b|feedback control|\bPID\b",
    "图论/网络": r"\bnetwork\b|\bgraphs?\b|graph theory|PageRank|centrality|shortest path|Dijkstra",
    "博弈论": r"game theor|Nash|Stackelberg",
    "系统动力学": r"system dynamics",
    "AHP": r"\bAHP\b|analytic hierarchy",
    "熵权/CRITIC": r"entropy weight|\bEWM\b|CRITIC",
    "TOPSIS": r"TOPSIS",
    "模糊综合评价": r"fuzzy",
    "灰色模型": r"\bgrey\b|\bgray (prediction|relational|model|forecast)|GM\(1,\s*1\)",
    "PCA/因子分析": r"\bPCA\b|principal component|factor analysis",
    "聚类": r"K-?means|cluster",
    "时间序列": r"ARIMA|SARIMA|time series|exponential smoothing|Holt",
    "回归": r"regression",
    "随机森林/XGBoost": r"random forest|XGBoost|LightGBM|GBDT|gradient boosting|CatBoost",
    "神经网络/LSTM": r"neural network|LSTM|\bGRU\b|\bRNN\b|\bCNN\b|Transformer|deep learning|BP network",
    "SHAP/可解释性": r"SHAP|interpretab|feature importance",
    "贝叶斯": r"Bayes",
    "马尔可夫/HMM": r"Markov|\bHMM\b",
    "因果推断 DID/PSM": r"difference-in-differences|\bDID\b|propensity|causal",
    "假设检验": r"hypothesis test|t-test|chi-square|Ljung|runs test|ANOVA|K-S test|p-value",
    "灵敏度分析": r"sensitivity",
    "鲁棒性/稳定性": r"robust|stability",
    "交叉验证/误差指标": r"cross-validation|RMSE|MAPE|R\^?2|R²|accuracy",
}
METHODS = {k: re.compile(v, re.I) for k, v in METHODS.items()}


def load_index(corpus: str) -> list[dict]:
    rows, seen = [], set()
    for path in sorted(glob.glob(os.path.join(corpus, "_index*.json"))):
        for row in json.load(io.open(path, encoding="utf-8")):
            if row["cid"] in seen or not row.get("year") or not row.get("problem"):
                continue
            seen.add(row["cid"])
            rows.append(row)
    return rows


def read_paper(corpus: str, cid: str) -> tuple[str, list[str], str]:
    """返回 (全文, 页列表, 来源类型)。MinerU 的 md 没有分页，页列表按 \\f 无法切，退化为单页。"""
    md = os.path.join(corpus, cid + ".md")
    txt = os.path.join(corpus, cid + ".txt")
    if os.path.exists(md) and os.path.getsize(md) > 3000:
        text = io.open(md, encoding="utf-8", errors="ignore").read()
        return text, [text], "mineru"
    text = io.open(txt, encoding="utf-8", errors="ignore").read() if os.path.exists(txt) else ""
    return text, text.split("\f"), "pdftotext"


def summary_block(text: str, pages: list[str]) -> str:
    first = pages[0] if len(pages) > 1 else text[:9000]
    m = re.search(r"\bSummary\b", first)
    start = m.end() if m else 0
    k = KEYWORDS_RX.search(first, start)
    end = k.start() if k else len(first)
    return first[start:end].strip()


def canon_section(title: str) -> str | None:
    for rx, name in SECTION_CANON:
        if rx.search(title):
            return name
    return None


TOC_ANY_RX = re.compile(r"^\s*\d{1,2}(?:\.\d{1,2}){0,3}\.?\s+([A-Z][^\n]{2,120})$", re.M)
MD_ANY_RX = re.compile(r"^#{1,4}\s+(?:[\d.]+\s*)?([A-Z][^\n]{2,80})$", re.M)


def _canon_list(titles: list[str]) -> list[str]:
    out = []
    for t in titles:
        c = canon_section(t)
        if c and c not in out:
            out.append(c)
    return out


def sections_of(text: str, pages: list[str], source: str) -> tuple[list[str], list[str]]:
    """返回 (一级标题规范名, 任意层级标题规范名)。"""
    top: list[str] = []
    anyl: list[str] = []
    if source == "mineru":
        top = [m.group(1).strip() for m in MD_H1_RX.finditer(text)]
        anyl = [m.group(1).strip() for m in MD_ANY_RX.finditer(text)]
    else:
        idx = next((i for i, p in enumerate(pages[:4]) if TOC_RX.search(p)), None)
        if idx is not None:
            # 目录跨页时，下一页也满是点线引导符
            nxt = pages[idx + 1] if idx + 1 < len(pages) else ""
            block = pages[idx] + "\n" + (nxt if nxt.count("....") > 3 else "")
            top = [LEADER_RX.sub("", m.group(2)).strip() for m in TOC_LINE_RX.finditer(block)]
            anyl = [LEADER_RX.sub("", m.group(1)).strip() for m in TOC_ANY_RX.finditer(block)]
    return _canon_list(top), _canon_list(anyl)


def analyse(row: dict, corpus: str) -> dict | None:
    text, pages, source = read_paper(corpus, row["cid"])
    if len(text) < 8000:
        return None
    figs = [int(n) for n in FIG_RX.findall(text) if 0 < int(n) < 200]
    tabs = [int(n) for n in TAB_RX.findall(text) if 0 < int(n) < 100]
    eqs = [int(n) for n in EQ_TAG_RX.findall(text) if 0 < int(n) < 400]
    refs = 0
    heads = list(REF_HEAD_RX.finditer(text))
    if heads:
        tail = text[heads[-1].end():]
        stop = re.search(r"^\s*(?:#+\s*)?(?:Appendix|Appendices|Report\s+on\s+Use\s+of\s+AI)", tail, re.I | re.M)
        refs = len(REF_ITEM_RX.findall(tail[:stop.start()] if stop else tail[:20000]))
    summ = summary_block(text, pages)
    words = WORD_RX.findall(summ)
    # pdftotext 在每页末尾输出一个 \f（最后一页也有），所以页数 = \f 的个数
    n_pages = text.count("\f") if source == "pdftotext" else row.get("pages") or None
    sections, sections_any = sections_of(text, pages, source)
    return {
        "cid": row["cid"], "year": row["year"], "problem": row["problem"], "source": source,
        "pages": n_pages if n_pages and n_pages > 1 else None,
        "figure_count": max(figs) if figs else 0,
        "table_count": max(tabs) if tabs else 0,
        "equation_tags": max(eqs) if eqs else 0,
        "reference_count": refs,
        "summary_words": len(words),
        "summary_numbers": len(NUM_RX.findall(summ)),
        "has_keywords": bool(KEYWORDS_RX.search(pages[0] if len(pages) > 1 else text[:9000])),
        "has_toc": bool(TOC_RX.search("\n".join(pages[:3]) if len(pages) > 1 else text[:15000])),
        "has_letter": bool(LETTER_RX.search(text)),
        "has_memo": bool(MEMO_RX.search(text)),
        "has_ai_report": bool(AI_RX.search(text)),
        "sections": sections,
        "sections_any": sections_any,
        "summary_text": summ[:6000],
    }


def quant(values: list[float]) -> dict:
    v = sorted(x for x in values if x is not None)
    if len(v) < 3:
        return {"n": len(v)}
    qs = statistics.quantiles(v, n=20, method="inclusive")
    return {"n": len(v), "p10": round(qs[1], 1), "p25": round(qs[4], 1),
            "p50": round(statistics.median(v), 1), "p75": round(qs[14], 1),
            "p90": round(qs[17], 1)}


NUMERIC = ("pages", "figure_count", "table_count", "equation_tags", "reference_count",
           "summary_words", "summary_numbers")
BOOLS = ("has_keywords", "has_toc", "has_letter", "has_memo", "has_ai_report")


def aggregate(rows: list[dict]) -> dict:
    node = {k: quant([r[k] for r in rows if r[k] is not None and (k != "reference_count" or r[k] > 0)])
            for k in NUMERIC}
    node["n_papers"] = len(rows)
    for b in BOOLS:
        node[b + "_rate"] = round(sum(r[b] for r in rows) / len(rows), 3) if rows else None
    with_sec = [r for r in rows if r["sections"]]
    cnt = Counter(s for r in with_sec for s in r["sections"])
    node["section_rate"] = {k: round(v / len(with_sec), 3) for k, v in cnt.most_common()} if with_sec else {}
    node["section_rate_n"] = len(with_sec)
    cnt_any = Counter(s for r in with_sec for s in r["sections_any"])
    node["section_any_level_rate"] = ({k: round(v / len(with_sec), 3) for k, v in cnt_any.most_common()}
                                      if with_sec else {})
    node["method_mention_rate"] = {
        k: round(sum(bool(rx.search(r["summary_text"])) for r in rows) / len(rows), 2)
        for k, rx in METHODS.items()} if rows else {}
    return node


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", help="写 empirical.json")
    ap.add_argument("--dump-summaries", help="把每篇的 Summary 原文与指标写成 jsonl（供人工蒸馏，不分发）")
    args = ap.parse_args(argv)

    rows = [r for r in (analyse(x, args.corpus) for x in load_index(args.corpus)) if r]
    if not rows:
        print("语料为空", file=sys.stderr)
        return 2
    by_topic = defaultdict(list)
    by_year = defaultdict(list)
    for r in rows:
        by_topic[r["problem"]].append(r)
        by_year[str(r["year"])].append(r)
    out = {
        "_doc": "MCM/ICM O 奖论文的观察分位。**不是评分线，不预测获奖**；只用于提示'这篇是不是明显异常'。"
                "生成工具 scripts/build_empirical.py；论文原件不随 skill 分发。",
        "_method": {k: v for k, v in (
            ("figure_count", "正文 'Figure N:' 题注的最大编号"),
            ("table_count", "正文 'Table N:' 题注的最大编号"),
            ("equation_tags", "行尾 '(N)' 公式编号的最大值；pdftotext 对公式提取不全，偏低"),
            ("reference_count", "References 标题后的 [n] / n. 条目数；0 视为未识别、不进分位"),
            ("summary_words", "第 1 页 'Summary' 到 'Keywords' 之间的英文词数"),
            ("summary_numbers", "Summary 里出现的数字个数（定量结论的粗代理）"),
            ("sections", "目录页一级标题（MinerU 来源按带编号的 # 标题），按 SECTION_CANON 归一化；"
                         "section_any_level_rate 含二、三级标题。pdftotext 来源只读目录页，"
                         "MinerU 来源读全部标题，两者口径略有差异"),
            ("method_mention_rate", "Summary 中出现该类方法关键词的论文占比（METHODS 表）；只表示'提到'"),
        )},
        "sample": {"n_papers": len(rows),
                   "by_year": {y: len(v) for y, v in sorted(by_year.items())},
                   "by_problem": {p: len(v) for p, v in sorted(by_topic.items())},
                   "sources": dict(Counter(r["source"] for r in rows))},
        "dims": aggregate(rows),
        "by_topic": {p: aggregate(v) for p, v in sorted(by_topic.items())},
        "by_year": {y: aggregate(v) for y, v in sorted(by_year.items())},
    }
    if args.out:
        with io.open(args.out, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print("[OK] %s（%d 篇）" % (args.out, len(rows)))
    if args.dump_summaries:
        with io.open(args.dump_summaries, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("[OK] %s" % args.dump_summaries)
    if not args.out and not args.dump_summaries:
        print(json.dumps(out["dims"], ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
