#!/usr/bin/env python3
"""Render competition-ready AI usage disclosures from ``decision_log.json``.

The source ledger is ``decision_log.compliance.ai_usage``.  Its deliberately
small schema is:

    {
      "compliance": {
        "ai_usage": [
          {
            "tool": "OpenAI ChatGPT",
            "model": "GPT-5",
            "version": "21 July 2026 version",
            "used_at": "2026-07-21T14:30:00+08:00",  # optional
            "use_stage": "Stage 7 / model evaluation",
            "purpose": "Language polishing",
            "paper_sections": ["Abstract", "Section 7"],
            "query": "Complete, exact input",       # see alternative below
            "output": "Complete, exact output",
            "human_review": "How the team checked and corrected it",
            "adoption": "What was ultimately retained",  # optional
            "evidence": ["state/ai/AI-001.txt"]            # optional
          }
        ]
      }
    }

``tool``, ``model``, ``version``, ``use_stage``, ``purpose``,
``paper_sections`` and ``human_review`` are required. A conversational or
generative entry must also
contain both ``query`` and ``output``.  Translation, code completion, or other
non-conversational use may instead contain one plain-language ``disclosure``.
Ledger order is retained as chronological order.  An explicit empty list means
that no AI-assisted tool was used; a missing path is treated as an error.

Outputs are placed where the paper renderer expects them (COMAP policy
"Use of AI Tools in COMAP Contests", v102025):

  * AI used: ``paper_workspace/12_ai_use_report.md`` — the body of the
    **Report on Use of AI** that follows the 25-page solution (not counted).
    Plus ``paper_workspace/ai_tool_references.md``: one reference-list entry
    per tool, because COMAP also requires inline citations and listing every
    AI tool in the reference section *inside* the 25 pages.
  * AI not used (explicit ``[]``): no report is required; any stale report is
    removed so the template drops the section. Answer "No" to the AI-use
    question on the COMAP submission form.

No third-party Python dependency.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _console  # noqa: E402


MCM_MARKDOWN_FILENAME = "12_ai_use_report.md"
MCM_REFERENCES_FILENAME = "ai_tool_references.md"


class LedgerValidationError(ValueError):
    """The decision log does not contain a usable, explicit AI usage ledger."""


@dataclass(frozen=True)
class AIUsageEntry:
    tool: str
    model: str
    version: str
    purpose: str
    use_stage: str
    paper_sections: Sequence[str]
    human_review: str
    used_at: str = ""
    brief_purpose: str = ""   # 正文内联引用处的短语，如 "language polishing"
    query: str = ""
    output: str = ""
    disclosure: str = ""
    adoption: str = ""
    evidence: Sequence[str] = ()

    @property
    def display_name(self) -> str:
        return f"{self.tool} ({self.model})"


def resolve_decision_log_path(cli_arg: Optional[str] = None) -> Path:
    """Resolve CLI > MATHMODEL_STATE_DIR > cwd/state."""
    if cli_arg:
        return Path(cli_arg)
    state_dir = os.environ.get("MATHMODEL_STATE_DIR")
    if state_dir:
        return Path(state_dir) / "decision_log.json"
    return Path.cwd() / "state" / "decision_log.json"


def _require_nonempty_string(raw: Dict[str, Any], key: str, entry_no: int) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise LedgerValidationError(
            f"compliance.ai_usage[{entry_no}] 的 {key!r} 必须是非空字符串"
        )
    return value.strip()


def _optional_string(raw: Dict[str, Any], key: str, entry_no: int) -> str:
    value = raw.get(key, "")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise LedgerValidationError(
            f"compliance.ai_usage[{entry_no}] 的 {key!r} 必须是字符串"
        )
    return value.strip()


def _string_list(
    raw: Dict[str, Any], key: str, entry_no: int, *, required: bool
) -> Sequence[str]:
    value = raw.get(key)
    if isinstance(value, str):
        items = [value.strip()] if value.strip() else []
    elif isinstance(value, list):
        items = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise LedgerValidationError(
                    f"compliance.ai_usage[{entry_no}] 的 {key!r} 只能包含非空字符串"
                )
            items.append(item.strip())
    elif value is None and not required:
        items = []
    else:
        expected = "非空字符串或字符串数组" if required else "字符串或字符串数组"
        raise LedgerValidationError(
            f"compliance.ai_usage[{entry_no}] 的 {key!r} 必须是{expected}"
        )
    if required and not items:
        raise LedgerValidationError(
            f"compliance.ai_usage[{entry_no}] 的 {key!r} 不能为空"
        )
    return tuple(items)


def validate_entries(raw_entries: Any) -> List[AIUsageEntry]:
    """Validate and normalize the raw ``compliance.ai_usage`` list."""
    if not isinstance(raw_entries, list):
        raise LedgerValidationError("decision_log.compliance.ai_usage 必须是数组")

    entries: List[AIUsageEntry] = []
    for index, raw in enumerate(raw_entries):
        if not isinstance(raw, dict):
            raise LedgerValidationError(
                f"compliance.ai_usage[{index}] 必须是 JSON 对象"
            )

        query = _optional_string(raw, "query", index)
        output = _optional_string(raw, "output", index)
        disclosure = _optional_string(raw, "disclosure", index)
        if bool(query) != bool(output):
            raise LedgerValidationError(
                f"compliance.ai_usage[{index}] 的 'query' 与 'output' 必须同时填写"
            )
        if disclosure and query:
            raise LedgerValidationError(
                f"compliance.ai_usage[{index}] 不能同时填写 'query'/'output' 与 'disclosure'"
            )
        if not disclosure and not (query and output):
            raise LedgerValidationError(
                f"compliance.ai_usage[{index}] 必须填写完整 'query' + 'output'，"
                "或为非对话式工具填写 'disclosure'"
            )

        entries.append(
            AIUsageEntry(
                tool=_require_nonempty_string(raw, "tool", index),
                model=_require_nonempty_string(raw, "model", index),
                version=_require_nonempty_string(raw, "version", index),
                used_at=_optional_string(raw, "used_at", index),
                use_stage=_require_nonempty_string(raw, "use_stage", index),
                purpose=_require_nonempty_string(raw, "purpose", index),
                brief_purpose=_optional_string(raw, "brief_purpose", index),
                paper_sections=_string_list(
                    raw, "paper_sections", index, required=True
                ),
                query=query,
                output=output,
                disclosure=disclosure,
                human_review=_require_nonempty_string(raw, "human_review", index),
                adoption=_optional_string(raw, "adoption", index),
                evidence=_string_list(raw, "evidence", index, required=False),
            )
        )
    return entries


def load_ledger(path: Path) -> tuple[Dict[str, Any], List[AIUsageEntry]]:
    """Load a decision log and require an explicit compliance ledger path."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LedgerValidationError(f"找不到 decision log：{path}") from exc
    except json.JSONDecodeError as exc:
        raise LedgerValidationError(
            f"decision log 不是有效 JSON：{path}（{exc}）"
        ) from exc

    if not isinstance(data, dict):
        raise LedgerValidationError("decision log 根节点必须是 JSON 对象")
    compliance = data.get("compliance")
    if not isinstance(compliance, dict) or "ai_usage" not in compliance:
        raise LedgerValidationError(
            "decision log 缺少 compliance.ai_usage；"
            "请明确记录 [] 表示未使用 AI 工具，不能据缺失字段推断未使用"
        )
    return data, validate_entries(compliance["ai_usage"])


def resolve_competition(cli_arg: Optional[str], decision_log: Dict[str, Any]) -> str:
    """Resolve CLI > MATHMODEL_COMPETITION > decision log."""
    competition = (
        cli_arg
        or os.environ.get("MATHMODEL_COMPETITION")
        or decision_log.get("competition")
        or "mcm"
    )
    if competition != "mcm":
        raise LedgerValidationError(
            f"本 skill 只支持 competition='mcm'（MCM/ICM）；当前值为 {competition!r}"
        )
    return str(competition)


def _escape_table_cell(text: str) -> str:
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


def _fenced_block(text: str, language: str = "text") -> str:
    """Return a Markdown fence longer than any backtick run in the payload."""
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}{language}\n{text}\n{fence}"


def _problem_context(decision_log: Dict[str, Any]) -> str:
    meta = decision_log.get("problem_meta")
    if not isinstance(meta, dict):
        return ""
    parts = [str(meta.get(key)).strip() for key in ("year", "letter", "title") if meta.get(key)]
    if not parts:
        return ""
    return f"**Problem:** {' · '.join(parts)}\n\n"


def render_mcm_markdown(
    entries: Sequence[AIUsageEntry], decision_log: Dict[str, Any]
) -> str:
    # The MCM LaTeX template supplies the Report on Use of AI heading.
    lines: List[str] = []
    context = _problem_context(decision_log)
    if context:
        lines.append(context.rstrip())
        lines.append("")
    lines.extend(
        [
            "The entries below are listed in order of use. The team verified the accuracy, validity, appropriateness, and originality of all AI-assisted material and remains responsible for the submitted work.",
            "",
        ]
    )
    for index, entry in enumerate(entries, 1):
        lines.extend(
            [
                # COMAP example format: "OpenAI ChatGPT (Nov 5, 2023 version, ChatGPT-4)"
                f"## {index}. {entry.tool} ({entry.version}, {entry.model})",
                "",
                f"**Purpose:** {entry.purpose}",
                "",
                f"**Workflow stage:** {entry.use_stage}",
                "",
                f"**Sections affected:** {', '.join(entry.paper_sections)}",
                "",
            ]
        )
        if entry.used_at:
            lines.extend([f"**Date/time used:** {entry.used_at}", ""])
        if entry.query and entry.output:
            lines.extend(
                [
                    "**Query:**",
                    "",
                    _fenced_block(entry.query),
                    "",
                    "**Output:**",
                    "",
                    _fenced_block(entry.output),
                    "",
                ]
            )
        else:
            lines.extend(["**Disclosure:**", "", entry.disclosure, ""])
        lines.extend(["**Human verification and revisions:**", "", entry.human_review, ""])
        if entry.adoption:
            lines.extend(["**Material incorporated:**", "", entry.adoption, ""])
    return "\n".join(lines).rstrip() + "\n"


def render_reference_entries(entries: Sequence[AIUsageEntry]) -> str:
    """One reference-list line per distinct tool/model/version, for 10_references.md."""
    seen = []
    for entry in entries:
        key = (entry.tool, entry.model, entry.version)
        if key not in seen:
            seen.append(key)
    lines = [
        "<!-- Paste into 10_references.md. COMAP requires every AI tool to be",
        "     cited inline and listed in the reference section of the 25-page solution. -->",
        "",
    ]
    for tool, model, version in seen:
        lines.append(f"- {tool}. {model} ({version}). AI tool; see Report on Use of AI.")
    return "\n".join(lines) + "\n"


def render_reports(
    decision_log_path: Path,
    paper_workspace: Path,
    competition: Optional[str] = None,
) -> List[Path]:
    """Render the MCM/ICM AI disclosure files and return their paths."""
    decision_log, entries = load_ledger(decision_log_path)
    resolve_competition(competition, decision_log)
    paper_workspace.mkdir(parents=True, exist_ok=True)
    md_path = paper_workspace / MCM_MARKDOWN_FILENAME
    ref_path = paper_workspace / MCM_REFERENCES_FILENAME
    if not entries:
        # COMAP only asks for the report when AI was used. Remove stale files so
        # the template drops the section instead of printing an outdated one.
        md_path.unlink(missing_ok=True)
        ref_path.unlink(missing_ok=True)
        return []
    md_path.write_text(render_mcm_markdown(entries, decision_log), encoding="utf-8")
    ref_path.write_text(render_reference_entries(entries), encoding="utf-8")
    return [md_path, ref_path]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="从 decision_log.compliance.ai_usage 生成 MCM/ICM Report on Use of AI",
        epilog=(
            "最小字段：tool, model, version, use_stage, purpose, paper_sections, human_review；"
            "并填写 query+output，或对翻译/代码补全等非对话式用途填写 disclosure。"
            "显式 [] 表示未使用，字段缺失会报错。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--decision-log",
        help="decision_log.json 路径（默认 state/decision_log.json）",
    )
    parser.add_argument(
        "--competition",
        choices=("mcm",),
        help="覆盖日志中的 competition（只支持 mcm）",
    )
    parser.add_argument(
        "--paper-workspace",
        default="paper_workspace",
        help="论文装配目录（默认 paper_workspace）",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    _console.init()
    args = build_parser().parse_args(argv)
    try:
        outputs = render_reports(
            resolve_decision_log_path(args.decision_log),
            Path(args.paper_workspace),
            args.competition,
        )
    except LedgerValidationError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    if not outputs:
        print("[OK] compliance.ai_usage = []：未使用 AI，不生成 Report on Use of AI。"
              "提交表单的 AI uses statement 选 No。")
    for path in outputs:
        print(f"[OK] {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
