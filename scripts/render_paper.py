"""
render_paper.py — markdown 中间产物 → 最终 PDF (MCM/ICM)

功能:
1. 读 stage 8 各节 markdown 产出 (<cwd>/paper_workspace/)
2. 模板与编译器: templates/latex/mcm/main.tex + pdflatex
3. md → tex (正式编译使用 Pandoc；手工正则只供 structural dry-run)
4. 三编生成 PDF，并从 main.aux 报告**解答页数**（Summary Sheet 起到附录止，
   不含 Report on Use of AI）——这才是 COMAP 25 页上限针对的数字

用法:
    python <skill>/scripts/render_paper.py --workspace paper_workspace/
    python scripts/render_paper.py --workspace ws/ --output-dir out/ \
      --control-number 2612345 --problem B --year 2027 --title "Paper Title" \
      --keywords "space elevator; logistics; optimization"
    python scripts/render_paper.py --workspace ws/ --no-compile  (dry-run)
"""

import argparse
import json
import os
import re
import subprocess
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _console  # noqa: E402
import _toolpath  # noqa: E402


_SKILL_ROOT = Path(__file__).resolve().parent.parent

TEMPLATE_MAP = {
    "mcm": {
        "template_dir": _SKILL_ROOT / "templates" / "latex" / "mcm",
        "engine": "pdflatex",
        "main_filename": "main.tex",
        "mode": "main_template",
        "_doc": "mcm 使用仓库原创 article 模板（COMAP Summary Sheet 版式）与 section marker 装配",
    },
}

# COMAP: 整份解答 ≤ 25 页（Summary Sheet、目录、正文、信件/备忘录、参考文献、
# 附录、代码全部计入）；Report on Use of AI 不计入。
PAGE_LIMIT = 25
SOLUTION_END_LABEL = "MathmodelSolutionEnd"


SECTION_TO_FILE = {
    "abstract": "01_summary.md",
    "1_problem_restate": "02_introduction.md",
    "2_problem_analysis": "03_analysis.md",
    "3_assumptions": "04_assumptions.md",
    "4_notation": "05_notation.md",
    "5_models": "06_models.md",
    "6_sensitivity": "07_sensitivity.md",
    "7_evaluation": "08_evaluation.md",
    "8_references": "10_references.md",
    "appendix_code": "11_appendix.md",
}

MEMO_FILENAME = "09_memo_letter.md"
AI_REPORT_FILENAME = "12_ai_use_report.md"
OPTIONAL_SECTION_TO_FILE = {
    # 题面要求 letter / memo / policy brief 时必须存在（Stage 1 写入
    # problem_meta.required_deliverables，check_compliance 据此 fail closed）。
    "memo_letter": MEMO_FILENAME,
    "ai_use_report": AI_REPORT_FILENAME,
}

# 只用 [ \t]：`\s*` 在 MULTILINE 下会吞掉 marker 前后的换行与空行，段落分隔随之
# 消失——Summary 标题与正文、正文与 Keywords 会粘成一段，且编译不报错。
SECTION_MARKER_RE = re.compile(
    r"^[ \t]*%[ \t]*MATHMODEL:SECTION[ \t]+([A-Za-z0-9_]+)[ \t]*$", re.MULTILINE)
OPTIONAL_BLOCK_RE = re.compile(
    r"^[ \t]*%\s*MATHMODEL:OPTIONAL\s+(?P<name>[A-Za-z0-9_]+)\s+BEGIN\s*$\n"
    r"(?P<body>.*?)"
    r"^[ \t]*%\s*MATHMODEL:OPTIONAL\s+(?P=name)\s+END\s*$\n?",
    re.MULTILINE | re.DOTALL,
)

PAPER_FIELD_TOKENS = {
    "mcm": {
        "mcm_control_number": "MATHMODEL_MCM_CONTROL_NUMBER",
        "problem": "MATHMODEL_MCM_PROBLEM",
        "year": "MATHMODEL_MCM_YEAR",
        "title": "MATHMODEL_MCM_TITLE",
        "keywords": "MATHMODEL_MCM_KEYWORDS",
    },
}

PAPER_FIELD_LABELS = {
    "mcm_control_number": "team control number/队伍控制号",
    "problem": "problem chosen/题号",
    "year": "contest year/竞赛年份",
    "title": "title/论文题目",
    "keywords": "keywords/关键词",
}

# 字段格式：控制号是 COMAP 发放的 7 位数字（例 2500001），题号 A–F，年份 4 位。
FIELD_PATTERNS = {
    "mcm_control_number": re.compile(r"\d{7}"),
    "problem": re.compile(r"[A-F]"),
    "year": re.compile(r"20\d{2}"),
}

_LATEX_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


# ============================================================================
# 路径与配置
# ============================================================================

def resolve_competition(cli_arg: str = None, decision_log_path: Path = None) -> str:
    """优先级: CLI > env MATHMODEL_COMPETITION > decision_log.competition > 'mcm'"""
    if cli_arg:
        return cli_arg
    env = os.environ.get("MATHMODEL_COMPETITION")
    if env:
        return env
    if decision_log_path and decision_log_path.exists():
        try:
            with open(decision_log_path, "r", encoding="utf-8") as f:
                log = json.load(f)
            if log.get("competition"):
                return log["competition"]
        except (json.JSONDecodeError, KeyError):
            pass
    return "mcm"


def resolve_decision_log_path(workspace: Path, explicit_path: str = None) -> Path:
    """Bind state to the user's workspace before falling back to the process cwd."""
    if explicit_path:
        return Path(explicit_path)
    candidates = (
        workspace.resolve().parent / "state" / "decision_log.json",
        Path.cwd() / "state" / "decision_log.json",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def load_decision_log(path: Path, required: bool = False) -> dict:
    """Load render state strictly; an existing but malformed state is never ignored."""
    if not path.is_file():
        if required:
            raise FileNotFoundError(f"decision log {path} 不存在")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"decision log {path} 无法读取或不是合法 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"decision log {path} 根节点必须是 object")
    return value


def resolve_paper_metadata(decision_log: dict = None, overrides: dict = None) -> dict:
    """Resolve final-paper metadata with explicit CLI values taking precedence."""
    decision_log = decision_log or {}
    overrides = overrides or {}
    paper_metadata = decision_log.get("paper_metadata") or {}
    if not isinstance(paper_metadata, dict):
        raise ValueError("decision_log.paper_metadata 必须是 object")
    problem_meta = decision_log.get("problem_meta") or {}
    if not isinstance(problem_meta, dict):
        raise ValueError("decision_log.problem_meta 必须是 object")

    def choose(key: str, *fallbacks):
        if key in overrides and overrides[key] is not None:
            return overrides[key]
        if key in paper_metadata and paper_metadata[key] is not None:
            return paper_metadata[key]
        return next((value for value in fallbacks if value is not None), None)

    return {
        "mcm_control_number": choose("mcm_control_number"),
        "problem": choose(
            "problem", problem_meta.get("letter"), decision_log.get("problem")
        ),
        "year": choose("year", problem_meta.get("year")),
        # A paper title and final keyword set are submission-facing fields. Do
        # not silently substitute the problem statement title or scan keywords.
        "title": choose("title"),
        "keywords": choose("keywords"),
    }


def _normalize_scalar(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    normalized = " ".join(str(value).split())
    return normalized or None


def _normalize_keywords(value) -> list[str] | None:
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = re.split(r"[,;；\n]+", value)
    elif isinstance(value, (list, tuple)):
        raw_items = list(value)
    else:
        return None
    items = []
    for item in raw_items:
        if not isinstance(item, str):
            return None
        normalized = _normalize_scalar(item)
        if normalized:
            items.append(normalized)
        elif item not in (None, ""):
            return None
    return items


def _is_placeholder(field: str, value: str) -> bool:
    compact = " ".join(value.strip().split())
    folded = compact.casefold()
    if folded.startswith("mathmodel_"):
        return True
    if re.fullmatch(r"x+", folded):
        return True
    if folded in {"todo", "tbd", "待定", "待填写", "placeholder"}:
        return True
    # COMAP 官方模板与收据示例里的默认值
    if field == "mcm_control_number" and folded in {"0000000", "1111111", "2500001"}:
        return True
    if field == "problem" and folded in {"abcdef", "x"}:
        return True
    if field == "title" and folded in {
        "title of your paper",
        "paper title",
        "untitled",
        "论文标题",
    }:
        return True
    if field == "keywords":
        if re.fullmatch(r"keyword\s*\d*", folded):
            return True
        if re.fullmatch(r"关键词\s*\d*", compact):
            return True
    return False


def prepare_paper_metadata(
    competition: str,
    metadata: dict = None,
    allow_placeholders: bool = False,
) -> tuple[dict, list[str]]:
    """Normalize required fields and fail closed on missing/template values."""
    tokens = PAPER_FIELD_TOKENS.get(competition)
    if tokens is None:
        return {}, []
    metadata = metadata or {}
    normalized = {}
    issues = []
    for field in tokens:
        raw_value = metadata.get(field)
        if field == "keywords":
            value = _normalize_keywords(raw_value)
            if value is None:
                issues.append(f"{PAPER_FIELD_LABELS[field]} 类型无效")
                continue
            if not value:
                issues.append(f"缺少 {PAPER_FIELD_LABELS[field]}")
                continue
            placeholders = [item for item in value if _is_placeholder(field, item)]
            if placeholders:
                issues.append(
                    f"{PAPER_FIELD_LABELS[field]} 仍含占位符: "
                    + ", ".join(placeholders)
                )
                continue
            normalized[field] = value
            continue

        value = _normalize_scalar(raw_value)
        if value is not None and field == "problem":
            value = value.upper()
        if value is None:
            issues.append(f"缺少 {PAPER_FIELD_LABELS[field]}")
        elif _is_placeholder(field, value):
            issues.append(f"{PAPER_FIELD_LABELS[field]} 仍是占位符: {value}")
        elif field in FIELD_PATTERNS and not FIELD_PATTERNS[field].fullmatch(value):
            issues.append(f"{PAPER_FIELD_LABELS[field]} 格式无效: {value}")
        else:
            normalized[field] = value

    if issues and not allow_placeholders:
        source_hint = (
            "请填写 state/decision_log.json 的 paper_metadata，或使用 "
            "--control-number、--problem、--year、--title、--keywords。"
        )
        raise ValueError(
            f"{competition} 正式渲染已停止：" + "；".join(issues) + "。" + source_hint
        )
    return normalized, issues


def _latex_escape(value: str) -> str:
    return "".join(_LATEX_ESCAPES.get(char, char) for char in value)


def fill_paper_metadata(
    template_text: str,
    competition: str,
    metadata: dict = None,
    allow_placeholders: bool = False,
) -> str:
    """Replace every front-matter token, leaving obvious tokens only in preview mode."""
    tokens = PAPER_FIELD_TOKENS.get(competition)
    if tokens is None:
        return template_text
    missing_template_tokens = [
        token for token in tokens.values() if token not in template_text
    ]
    if missing_template_tokens:
        raise ValueError(
            "模板缺少提交元数据 token: " + ", ".join(missing_template_tokens)
        )

    normalized, issues = prepare_paper_metadata(
        competition, metadata, allow_placeholders=allow_placeholders
    )
    for field, value in normalized.items():
        if field == "keywords":
            rendered = "; ".join(_latex_escape(item) for item in value)
        else:
            rendered = _latex_escape(value)
        template_text = template_text.replace(tokens[field], rendered)

    if issues:
        print(
            "[WARN] 模板预览保留显式 MATHMODEL_* token: " + "；".join(issues)
        )
    return template_text


def find_unresolved_front_matter_placeholders(tex_text: str) -> list[str]:
    """Detect both current fail-closed tokens and placeholders in older outputs."""
    unresolved = []
    for competition, fields in PAPER_FIELD_TOKENS.items():
        for field, token in fields.items():
            if token in tex_text:
                unresolved.append(f"{competition}:{PAPER_FIELD_LABELS[field]}")

    # COMAP 官方 Summary Sheet 模板的默认值：直接拿官方模板改的稿子最常漏掉这几处。
    if "Summary Sheet" in tex_text:
        legacy_checks = {
            "mcm:team control number/队伍控制号": (
                r"\\newcommand\{\\Team\}\{1111111\}", r"Team \\#\s*XXXX",
            ),
            "mcm:problem chosen/题号": (r"\\newcommand\{\\Problem\}\{ABCDEF\}",),
            "mcm:title/论文题目": ("TITLE OF YOUR PAPER",),
            "mcm:summary/摘要": (r"Use this template to begin typing the first page",),
        }
        for label, patterns in legacy_checks.items():
            if any(re.search(pattern, tex_text, re.IGNORECASE) for pattern in patterns):
                unresolved.append(label)
    return sorted(set(unresolved))


# ============================================================================
# md → tex 转换
# ============================================================================

def has_pandoc() -> bool:
    try:
        r = subprocess.run(["pandoc", "--version"], capture_output=True, text=True)
        return r.returncode == 0
    except FileNotFoundError:
        return False


def md_to_tex_pandoc(md_text: str) -> str:
    r = subprocess.run(
        ["pandoc", "-f", "markdown+tex_math_dollars+pipe_tables+raw_tex",
         "-t", "latex", "--no-highlight"],
        input=md_text, capture_output=True, text=True, encoding="utf-8"
    )
    if r.returncode != 0:
        raise RuntimeError(f"pandoc 失败: {r.stderr}")
    return r.stdout


def md_to_tex_fallback(md_text: str) -> str:
    """5 类 markdown → LaTeX 手工正则 (代码块 / 公式块 / 图片 / 表格 / 列表 / 标题 / 行内)"""
    tex = md_text

    def replace_code_block(m):
        lang = m.group(1) or "text"
        body = m.group(2)
        return f"\\begin{{lstlisting}}[language={lang}]\n{body}\n\\end{{lstlisting}}"
    tex = re.sub(r"```(\w+)?\n(.*?)\n```", replace_code_block, tex, flags=re.DOTALL)

    def replace_eq(m):
        body = m.group(1).strip()
        if "\\\\" in body or "&" in body:
            return f"\\begin{{align}}\n{body}\n\\end{{align}}"
        return f"\\begin{{equation}}\n{body}\n\\end{{equation}}"
    tex = re.sub(r"\$\$(.+?)\$\$", replace_eq, tex, flags=re.DOTALL)

    def replace_img(m):
        alt = m.group(1)
        path = m.group(2)
        return (f"\\begin{{figure}}[H]\n\\centering\n"
                f"\\includegraphics[width=0.8\\textwidth]{{{path}}}\n"
                f"\\caption{{{alt}}}\n\\end{{figure}}")
    tex = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace_img, tex)

    def replace_table(m):
        rows = [r.strip() for r in m.group(0).splitlines() if r.strip()]
        if len(rows) < 2:
            return m.group(0)
        cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
        header = cells[0]
        data = cells[2:] if len(cells) > 2 else []
        n_cols = len(header)
        col_spec = "l" * n_cols
        out = [f"\\begin{{table}}[H]\n\\centering",
               f"\\begin{{tabular}}{{{col_spec}}}\n\\toprule",
               " & ".join(header) + " \\\\",
               "\\midrule"]
        for row in data:
            out.append(" & ".join(row) + " \\\\")
        out.append("\\bottomrule\n\\end{tabular}\n\\end{table}")
        return "\n".join(out)
    tex = re.sub(r"^\|.+\|\s*$\n^\|[-:\s|]+\|\s*$\n(?:^\|.+\|\s*$\n?)+",
                  replace_table, tex, flags=re.MULTILINE)

    def replace_ol(m):
        items = re.findall(r"^\s*\d+\.\s+(.+)$", m.group(0), re.MULTILINE)
        if not items:
            return m.group(0)
        body = "\n".join(f"\\item {it}" for it in items)
        return f"\\begin{{enumerate}}\n{body}\n\\end{{enumerate}}"
    tex = re.sub(r"(?:^\s*\d+\.\s+.+\n?){2,}", replace_ol, tex, flags=re.MULTILINE)

    def replace_ul(m):
        items = re.findall(r"^\s*-\s+(.+)$", m.group(0), re.MULTILINE)
        if not items:
            return m.group(0)
        body = "\n".join(f"\\item {it}" for it in items)
        return f"\\begin{{itemize}}\n{body}\n\\end{{itemize}}"
    tex = re.sub(r"(?:^\s*-\s+.+\n?){2,}", replace_ul, tex, flags=re.MULTILINE)

    tex = re.sub(r"^# (.+)$", r"\\section{\1}", tex, flags=re.MULTILINE)
    tex = re.sub(r"^## (.+)$", r"\\subsection{\1}", tex, flags=re.MULTILINE)
    tex = re.sub(r"^### (.+)$", r"\\subsubsection{\1}", tex, flags=re.MULTILINE)

    tex = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", tex)
    tex = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"\\textit{\1}", tex)
    tex = re.sub(r"`([^`]+?)`", r"\\texttt{\1}", tex)
    tex = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", tex)

    return tex


def md_to_tex(md_text: str, prefer_pandoc: bool = True) -> str:
    if prefer_pandoc:
        if not has_pandoc():
            raise RuntimeError("Pandoc 未安装，正式论文转换已停止")
        return md_to_tex_pandoc(md_text)
    return md_to_tex_fallback(md_text)


def validate_workspace_sections(workspace: Path) -> None:
    """Require every mandatory workspace section to exist and contain content."""
    missing = []
    empty = []
    for filename in SECTION_TO_FILE.values():
        path = workspace / filename
        if not path.is_file():
            missing.append(filename)
        elif not path.read_text(encoding="utf-8").strip():
            empty.append(filename)
    problems = []
    if missing:
        problems.append(f"缺失: {', '.join(missing)}")
    if empty:
        problems.append(f"空文件: {', '.join(empty)}")
    if problems:
        raise FileNotFoundError(
            "paper workspace 不完整（" + "；".join(problems) + "）。"
            "为避免生成正文缺失但看似成功的 PDF，已停止。"
        )


# ============================================================================
# 模板填充: 三竞赛统一 marker 装配
# ============================================================================


def fill_template_main(
    workspace: Path,
    template_dir: Path,
    output_dir: Path,
    main_filename: str,
    prefer_pandoc: bool = True,
    competition: str = None,
    paper_metadata: dict = None,
    allow_placeholders: bool = False,
) -> Path:
    """Render section files and wire them into a competition main.tex template."""
    validate_workspace_sections(workspace)
    main_src = template_dir / main_filename
    if not main_src.exists():
        raise FileNotFoundError(f"模板 {main_src} 不存在")
    main_text = fill_paper_metadata(
        main_src.read_text(encoding="utf-8"),
        competition,
        metadata=paper_metadata,
        allow_placeholders=allow_placeholders,
    )

    # Validate submission metadata before creating an output that could be
    # mistaken for a ready paper.
    output_dir.mkdir(parents=True, exist_ok=True)
    sections_dir = output_dir / "sections"
    sections_dir.mkdir(exist_ok=True)
    main_dst = output_dir / main_filename

    # 复制其他 sty / cls 文件
    for ext in ("*.cls", "*.sty", "*.bib"):
        for f in template_dir.glob(ext):
            shutil.copy(f, output_dir)

    # 复制 figures
    if (template_dir / "figures").exists():
        shutil.copytree(template_dir / "figures", output_dir / "figures",
                         dirs_exist_ok=True)
    if (workspace.parent / "figures").exists():
        shutil.copytree(workspace.parent / "figures", output_dir / "figures",
                         dirs_exist_ok=True)

    optional_included = set()

    def resolve_optional_block(match: re.Match) -> str:
        name = match.group("name")
        if name not in OPTIONAL_SECTION_TO_FILE:
            raise ValueError(f"模板包含未知 optional block: {name}")
        path = workspace / OPTIONAL_SECTION_TO_FILE[name]
        if not path.is_file():
            return ""
        if not path.read_text(encoding="utf-8").strip():
            raise ValueError(f"可选节 {path.name} 存在但为空")
        optional_included.add(name)
        return match.group("body")

    main_text = OPTIONAL_BLOCK_RE.sub(resolve_optional_block, main_text)
    markers = SECTION_MARKER_RE.findall(main_text)
    duplicate_markers = sorted({name for name in markers if markers.count(name) > 1})
    if duplicate_markers:
        raise ValueError(f"模板包含重复 section marker: {duplicate_markers}")
    unknown_markers = sorted(
        set(markers) - set(SECTION_TO_FILE) - set(OPTIONAL_SECTION_TO_FILE)
    )
    if unknown_markers:
        raise ValueError(f"模板包含未知 section marker: {unknown_markers}")
    orphan_optional = sorted(
        set(markers).intersection(OPTIONAL_SECTION_TO_FILE) - optional_included
    )
    if orphan_optional:
        raise ValueError(
            f"可选 section marker 必须位于同名 OPTIONAL block 内: {orphan_optional}"
        )

    missing_markers = sorted(set(SECTION_TO_FILE) - set(markers))
    if missing_markers:
        raise ValueError(
            f"模板缺少 MATHMODEL section marker: {missing_markers}; "
            "为避免生成看似成功但正文为空的 PDF, 已停止"
        )

    section_files = dict(SECTION_TO_FILE)
    section_files.update({
        marker: OPTIONAL_SECTION_TO_FILE[marker]
        for marker in markers if marker in optional_included
    })

    # md → sections/<sec>.tex
    for sec, fname in section_files.items():
        md_path = workspace / fname
        sec_tex_path = sections_dir / f"{sec}.tex"
        tex = md_to_tex(md_path.read_text(encoding="utf-8"), prefer_pandoc)
        sec_tex_path.write_text(tex, encoding="utf-8")

    main_text = SECTION_MARKER_RE.sub(
        lambda m: f"\\input{{sections/{m.group(1)}}}",
        main_text,
    )
    main_dst.write_text(main_text, encoding="utf-8")

    print(
        f"[OK] 已生成 {main_dst}, 渲染并自动连接 "
        f"{len(section_files)} 个 sections/*.tex"
    )
    return main_dst


def fill_template(
    competition: str,
    workspace: Path,
    output_dir: Path,
    prefer_pandoc: bool = True,
    paper_metadata: dict = None,
    allow_placeholders: bool = None,
) -> tuple[Path, str]:
    """竞赛分发: 返回 (main_tex_path, engine)"""
    cfg = TEMPLATE_MAP.get(competition)
    if cfg is None:
        raise ValueError(f"未知 competition: {competition}; 支持 {list(TEMPLATE_MAP.keys())}")

    template_dir = cfg["template_dir"]
    if not template_dir.exists():
        raise FileNotFoundError(f"模板目录 {template_dir} 不存在")

    if cfg["mode"] == "main_template":
        # Backward-compatible programmatic structural preview: callers that
        # explicitly select the fallback converter already opted out of formal
        # rendering. CLI callers always pass an explicit boolean instead.
        if allow_placeholders is None:
            allow_placeholders = not prefer_pandoc
        main_tex_path = fill_template_main(workspace, template_dir, output_dir,
                                            cfg["main_filename"], prefer_pandoc,
                                            competition=competition,
                                            paper_metadata=paper_metadata,
                                            allow_placeholders=allow_placeholders)
    else:
        raise ValueError(f"未知 template mode: {cfg['mode']}")

    return main_tex_path, cfg["engine"]


# ============================================================================
# 编译
# ============================================================================

def solution_page_count(aux_text: str) -> int | None:
    """Page of the MathmodelSolutionEnd label = pages counted against the limit."""
    match = re.search(
        r"\\newlabel\{" + SOLUTION_END_LABEL + r"\}\{\{[^{}]*\}\{(\d+)\}", aux_text
    )
    return int(match.group(1)) if match else None


def compile_pdf(tex_path: Path, engine: str = "pdflatex", runs: int = 3) -> bool:
    try:
        unresolved = find_unresolved_front_matter_placeholders(
            tex_path.read_text(encoding="utf-8")
        )
    except OSError as exc:
        print(f"[FAIL] 无法读取待编译 TeX: {exc}")
        return False
    if unresolved:
        print(
            "[FAIL] 正式编译已停止，封面/摘要页仍含提交占位符: "
            + ", ".join(unresolved)
        )
        return False

    workdir = tex_path.parent
    for i in range(runs):
        print(f"\n--- {engine} 第 {i+1}/{runs} 次 ---")
        result = subprocess.run(
            [engine, "-interaction=nonstopmode", "-halt-on-error", str(tex_path.name)],
            cwd=workdir, capture_output=True, text=True, encoding="utf-8", errors="ignore"
        )
        if result.returncode != 0:
            print(f"[FAIL] {engine} 失败 (返回码 {result.returncode})")
            print(result.stdout[-2000:])
            print("--- stderr ---")
            print(result.stderr[-1000:])
            return False
    pdf_path = tex_path.with_suffix(".pdf")
    if not pdf_path.exists():
        print(f"[FAIL] PDF 未生成")
        return False

    # "PDF 存在"不等于"编译成功"。TeX 引擎会一边报错一边输出残缺 PDF——
    # 2026-09-03 实测：正文里一个无标题 markdown 表格让整篇论文只剩 1 页，
    # 退出码非 0 才拦住；换成没有 -halt-on-error 的手工编译就完全是静默的。
    # 所以这里把页数和报错数一起报出来，让人有个可核对的数字。
    log_path = tex_path.with_suffix(".log")
    pages, errors = None, None
    if log_path.exists():
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        errors = sum(1 for line in log_text.splitlines() if line.startswith("!"))
        match = re.search(r"Output written on .*?\((\d+) pages?", log_text)
        if match:
            pages = int(match.group(1))

    size_kb = pdf_path.stat().st_size // 1024
    detail = f"{size_kb} KB"
    if pages is not None:
        detail += f", {pages} 页"
    print(f"\n[OK] PDF 已生成: {pdf_path} ({detail})")
    if errors:
        print(f"[WARN] {log_path.name} 里有 {errors} 条 TeX 报错（以 '!' 开头）。"
              "页数与预期不符时，去 log 里找**第一条** '!'——从那里往后的内容都可能已经丢了。")
    if pages is not None and pages <= 2:
        print(f"[WARN] 只输出了 {pages} 页。除非本来就这么短，否则大概率是中途丢内容了。")

    aux_path = tex_path.with_suffix(".aux")
    solution_pages = None
    if aux_path.exists():
        solution_pages = solution_page_count(
            aux_path.read_text(encoding="utf-8", errors="replace")
        )
    if solution_pages is not None:
        print(f"[INFO] 计入 25 页上限的解答页数: {solution_pages}"
              f"（PDF 总页数 {pages}，差额是 Report on Use of AI）")
        if solution_pages > PAGE_LIMIT:
            print(f"[FAIL] 解答 {solution_pages} 页，超过 COMAP 的 {PAGE_LIMIT} 页上限。"
                  "附录和代码也计入——先砍附录代码，再压图表。")
            return False
    return True


# ============================================================================
# CLI
# ============================================================================

def main():
    _console.init()
    # 与 doctor.py 保持一致：装了但当前终端 PATH 是旧快照时自动补上。
    # 必须在任何工具探测（has_pandoc）之前做，否则会出现
    # "doctor 说编译链就绪、render_paper 却说 Pandoc 没装"的矛盾。
    for tool in ("pandoc", "pdflatex"):
        found = _toolpath.ensure_on_path(tool)
        if found.recovered:
            print(f"[INFO] {tool} 不在本进程 PATH 上，已补入: {found.directory}")

    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=str, required=True,
                        help="<cwd>/paper_workspace/ 目录, 含 01..11_*.md 节文件")
    parser.add_argument("--competition", type=str, default=None,
                        help="mcm (默认从 decision_log 读, 缺失则 mcm)")
    parser.add_argument("--decision-log", type=str, default=None,
                        help="可选: 指定 decision_log.json 路径用于自动检测 competition")
    parser.add_argument("--control-number", "--mcm-control-number",
                        dest="mcm_control_number", default=None,
                        help="MCM/ICM team control number, 7 位（覆盖 decision log）")
    parser.add_argument("--problem", default=None,
                        help="Problem Chosen, A–F（覆盖 decision log）")
    parser.add_argument("--year", default=None,
                        help="竞赛年份, 印在 Summary Sheet 上（覆盖 decision log）")
    parser.add_argument("--title", default=None,
                        help="最终论文题目（覆盖 decision log）")
    parser.add_argument("--keywords", default=None,
                        help="最终关键词，以逗号、分号或中文分号分隔（覆盖 decision log）")
    parser.add_argument("--output-dir", type=str, default="paper_output")
    parser.add_argument("--no-pandoc", action="store_true",
                        help="禁用 pandoc, 直接用手工正则 (调试用)")
    parser.add_argument("--no-compile", action="store_true",
                        help="只填充模板, 不调用 LaTeX 引擎 (dry-run)")
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="仅模板预览: 允许保留醒目的 MATHMODEL_* token；必须与 --no-compile 同用",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace)
    output_dir = Path(args.output_dir)

    if not workspace.exists():
        print(f"[FAIL] workspace {workspace} 不存在")
        return 1

    if args.allow_placeholders and not args.no_compile:
        print("[FAIL] --allow-placeholders 只能与 --no-compile 一起使用，禁止生成占位 PDF")
        return 1

    decision_log_path = resolve_decision_log_path(workspace, args.decision_log)
    try:
        decision_log = load_decision_log(
            decision_log_path, required=bool(args.decision_log)
        )
        paper_metadata = resolve_paper_metadata(
            decision_log,
            {
                "mcm_control_number": args.mcm_control_number,
                "problem": args.problem,
                "year": args.year,
                "title": args.title,
                "keywords": args.keywords,
            },
        )
    except (ValueError, FileNotFoundError) as e:
        print(f"[FAIL] {e}")
        return 1

    competition = resolve_competition(args.competition, decision_log_path)
    print(f"competition: {competition}")

    prefer_pandoc = not args.no_pandoc
    if args.no_pandoc and not args.no_compile:
        print("[FAIL] --no-pandoc 仅用于 --no-compile structural dry-run；正式编译必须使用 Pandoc")
        return 1
    if prefer_pandoc and not has_pandoc():
        if not args.no_compile:
            print("[FAIL] 正式论文转换需要 Pandoc: https://pandoc.org/installing.html")
            return 1
        print("[WARN] Pandoc 未安装；本次 --no-compile 仅检查结构，使用简化转换器")
        prefer_pandoc = False

    try:
        tex_path, engine = fill_template(
            competition,
            workspace,
            output_dir,
            prefer_pandoc,
            paper_metadata=paper_metadata,
            allow_placeholders=args.allow_placeholders,
        )
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        print(f"[FAIL] {e}")
        return 1

    if args.no_compile:
        print(f"[OK] dry-run 完成 (--no-compile). engine={engine}, tex={tex_path}")
        return 0

    return 0 if compile_pdf(tex_path, engine=engine, runs=3) else 1


if __name__ == "__main__":
    sys.exit(main())
