#!/usr/bin/env python3
"""Regression tests for fail-closed MCM/ICM paper rendering."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "latex" / "mcm" / "main.tex"


def load_render_paper():
    path = ROOT / "scripts" / "render_paper.py"
    spec = importlib.util.spec_from_file_location("render_guard_render_paper", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


render_paper = load_render_paper()

GOOD_META = {
    "mcm_control_number": "2712345",
    "problem": "b",
    "year": "2027",
    "title": "Lifting Off: Space Elevator & Rocket_Logistics",
    "keywords": ["space elevator", "logistics & cost", "optimization"],
}


def has_mcm_latex_toolchain() -> bool:
    """Only run integration tests when pdflatex and the newtx fonts are available."""
    if not shutil.which("pdflatex") or not shutil.which("kpsewhich"):
        return False
    try:
        result = subprocess.run(["kpsewhich", "newtxtext.sty"], capture_output=True,
                                text=True, check=False, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


def write_workspace(path: Path, *, memo: bool = False, ai: bool = False) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for section, filename in render_paper.SECTION_TO_FILE.items():
        label = section.replace("_", " ")   # 下划线在 LaTeX 正文里非法
        content = f"Rendered {label}.\n" if section == "abstract" else (
            f"# {label}\n\nRendered {label}.\n"
        )
        (path / filename).write_text(content, encoding="utf-8")
    if memo:
        (path / render_paper.MEMO_FILENAME).write_text(
            "# Letter to the MCM Agency\n\nDear MCM Agency,\n", encoding="utf-8")
    if ai:
        (path / render_paper.AI_REPORT_FILENAME).write_text(
            "## 1. OpenAI ChatGPT (Jan 30, 2027 version, GPT-5)\n", encoding="utf-8")


class RenderMetadataTests(unittest.TestCase):
    def test_state_metadata_fills_summary_sheet_and_escapes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "paper_workspace"
            write_workspace(workspace)
            metadata = render_paper.resolve_paper_metadata({
                "competition": "mcm", "paper_metadata": GOOD_META})

            main_path, engine = render_paper.fill_template(
                "mcm", workspace, root / "out", prefer_pandoc=False,
                paper_metadata=metadata, allow_placeholders=False)
            text = main_path.read_text(encoding="utf-8")

            self.assertEqual(engine, "pdflatex")
            self.assertIn(r"Space Elevator \& Rocket\_Logistics", text)
            self.assertIn(r"space elevator; logistics \& cost; optimization", text)
            self.assertIn(r"\newcommand{\TeamNumber}{2712345}", text)
            self.assertIn(r"\newcommand{\ProblemChosen}{B}", text, "题号应规范成大写")
            self.assertIn(r"\newcommand{\ContestYear}{2027}", text)
            self.assertNotIn("MATHMODEL_MCM_", text)
            self.assertEqual(render_paper.find_unresolved_front_matter_placeholders(text), [])

    def test_problem_letter_falls_back_to_problem_meta(self) -> None:
        meta = render_paper.resolve_paper_metadata({
            "problem_meta": {"letter": "C", "year": 2027},
            "paper_metadata": {"mcm_control_number": "2712345"}})
        self.assertEqual(meta["problem"], "C")
        self.assertEqual(meta["year"], 2027)

    def test_missing_placeholder_or_malformed_values_fail_closed(self) -> None:
        bad_cases = (
            ({}, "缺少"),
            ({**GOOD_META, "title": "TITLE OF YOUR PAPER"}, "仍是占位符"),
            ({**GOOD_META, "keywords": ["keyword1"]}, "仍含占位符"),
            ({**GOOD_META, "mcm_control_number": "1111111"}, "仍是占位符"),
            ({**GOOD_META, "problem": "ABCDEF"}, "仍是占位符"),
            ({**GOOD_META, "mcm_control_number": "27123"}, "格式无效"),
            ({**GOOD_META, "problem": "G"}, "格式无效"),
            ({**GOOD_META, "year": "27"}, "格式无效"),
        )
        for metadata, message in bad_cases:
            with self.subTest(metadata=metadata):
                with self.assertRaisesRegex(ValueError, message):
                    render_paper.prepare_paper_metadata("mcm", metadata, allow_placeholders=False)

    def test_preview_tokens_cannot_reach_compile_process(self) -> None:
        preview = render_paper.fill_paper_metadata(
            TEMPLATE.read_text(encoding="utf-8"), "mcm", {}, allow_placeholders=True)
        self.assertIn("MATHMODEL_MCM_TITLE", preview)
        with tempfile.TemporaryDirectory() as temp:
            tex_path = Path(temp) / "main.tex"
            tex_path.write_text(preview, encoding="utf-8")
            with mock.patch.object(render_paper.subprocess, "run") as run:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertFalse(render_paper.compile_pdf(tex_path, "pdflatex"))
                run.assert_not_called()

    def test_official_template_defaults_are_caught(self) -> None:
        """直接拿 COMAP 官方 Summary 模板改的稿子，最常漏改这几处。"""
        legacy = (r"\newcommand{\Problem}{ABCDEF}" "\n" r"\newcommand{\Team}{1111111}"
                  "\nSummary Sheet\nUse this template to begin typing the first page")
        unresolved = render_paper.find_unresolved_front_matter_placeholders(legacy)
        self.assertIn("mcm:team control number/队伍控制号", unresolved)
        self.assertIn("mcm:problem chosen/题号", unresolved)
        self.assertIn("mcm:summary/摘要", unresolved)

    def test_formal_render_requires_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "paper_workspace"
            write_workspace(workspace)
            with self.assertRaisesRegex(ValueError, "缺少 team control number"):
                render_paper.fill_template("mcm", workspace, root / "out", prefer_pandoc=False,
                                           paper_metadata={}, allow_placeholders=False)


class TemplateContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.template = TEMPLATE.read_text(encoding="utf-8")

    def test_rules_aligned_layout(self) -> None:
        t = self.template
        self.assertIn(r"\documentclass[12pt,letterpaper]{article}", t, "COMAP: >=12 pt")
        self.assertIn(r"\usepackage{newtxtext}", t)
        self.assertIn(r"\fancyhead[L]{Team \# \TeamNumber}", t, "每页页眉要有控制号")
        self.assertIn(r"Page \thepage\ of \pageref{LastPage}", t)
        self.assertIn("Problem Chosen", t)
        self.assertIn("Summary Sheet", t)
        self.assertIn(r"\tableofcontents", t)
        self.assertNotIn(r"{\small\tableofcontents}", t, "目录也不能缩到 12pt 以下")
        self.assertNotIn(r"\author", t, "匿名：模板里不能有作者字段")

    def test_marker_set_and_order(self) -> None:
        markers = render_paper.SECTION_MARKER_RE.findall(self.template)
        self.assertEqual(set(markers), set(render_paper.SECTION_TO_FILE)
                         | set(render_paper.OPTIONAL_SECTION_TO_FILE))
        self.assertEqual(len(markers), len(set(markers)))
        t = self.template
        # letter/memo 计入 25 页，必须在参考文献之前；AI 报告在解答结束标签之后
        self.assertLess(t.index("MATHMODEL:SECTION memo_letter"), t.index("MATHMODEL:SECTION 8_references"))
        self.assertLess(t.index("MATHMODEL:SECTION appendix_code"), t.index(r"\label{MathmodelSolutionEnd}"))
        self.assertLess(t.index(r"\label{MathmodelSolutionEnd}"), t.index("MATHMODEL:SECTION ai_use_report"))
        self.assertIn("MATHMODEL:OPTIONAL memo_letter BEGIN", t)
        self.assertIn("MATHMODEL:OPTIONAL ai_use_report BEGIN", t)

    def test_marker_regex_keeps_blank_lines(self) -> None:
        """`\\s*` 曾吞掉 marker 前的空行，Summary 标题和正文粘成一段。"""
        text = "\\noindent\\textbf{Summary}\n\n% MATHMODEL:SECTION abstract\n\nKeywords"
        out = render_paper.SECTION_MARKER_RE.sub(lambda m: "\\input{x}", text)
        self.assertIn("Summary}\n\n\\input{x}\n\nKeywords", out)

    def test_optional_blocks_follow_workspace_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for memo, ai in ((False, False), (True, True)):
                workspace = root / ("ws_%d%d" % (memo, ai))
                write_workspace(workspace, memo=memo, ai=ai)
                with contextlib.redirect_stdout(io.StringIO()):
                    main_path, _ = render_paper.fill_template(
                        "mcm", workspace, root / ("out_%d%d" % (memo, ai)), prefer_pandoc=False,
                        paper_metadata=GOOD_META, allow_placeholders=False)
                text = main_path.read_text(encoding="utf-8")
                self.assertEqual(r"\input{sections/memo_letter}" in text, memo)
                self.assertEqual(r"\input{sections/ai_use_report}" in text, ai)
                self.assertEqual(r"\section*{Report on Use of AI}" in text, ai)

    def test_solution_page_count_reads_aux_label(self) -> None:
        aux = r"\newlabel{MathmodelSolutionEnd}{{}{24}{}{section*.9}{}}"
        self.assertEqual(render_paper.solution_page_count(aux), 24)
        self.assertIsNone(render_paper.solution_page_count(r"\newlabel{other}{{}{3}}"))


@unittest.skipUnless(has_mcm_latex_toolchain(), "pdflatex with newtx is not installed")
class McmLatexIntegrationTests(unittest.TestCase):
    def render_and_compile(self, root: Path, *, body_extra: str = "", ai: bool = False) -> tuple[bool, str]:
        workspace = root / "paper_workspace"
        write_workspace(workspace, ai=ai)
        if body_extra:
            path = workspace / render_paper.SECTION_TO_FILE["5_models"]
            path.write_text(path.read_text(encoding="utf-8") + body_extra, encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            main_path, _ = render_paper.fill_template(
                "mcm", workspace, root / "out", prefer_pandoc=False,
                paper_metadata=GOOD_META, allow_placeholders=False)
            ok = render_paper.compile_pdf(main_path, "pdflatex", runs=2)
        return ok, buf.getvalue()

    def test_template_compiles_and_reports_solution_pages(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ok, out = self.render_and_compile(Path(temp), ai=True)
            self.assertTrue(ok, out)
            self.assertIn("计入 25 页上限的解答页数", out)

    def test_solution_over_25_pages_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            overflow = "".join("\n\\newpage\nMore results.\n" for _ in range(26))
            ok, out = self.render_and_compile(Path(temp), body_extra=overflow)
            self.assertFalse(ok)
            self.assertIn("超过 COMAP 的 25 页上限", out)


class RenderCliTests(unittest.TestCase):
    def run_cli(self, workspace: Path, output: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "render_paper.py"),
             "--workspace", str(workspace), "--output-dir", str(output),
             "--no-pandoc", "--no-compile", *extra],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8")

    def test_no_compile_is_still_strict_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "paper_workspace"
            output = root / "out"
            write_workspace(workspace)
            result = self.run_cli(workspace, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("正式渲染已停止", result.stdout)
            self.assertFalse(output.exists())

    def test_explicit_cli_metadata_renders_a_clean_structural_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "paper_workspace"
            output = root / "out"
            write_workspace(workspace)
            result = self.run_cli(workspace, output, "--control-number", "2712345", "--problem", "D",
                                  "--year", "2027", "--title", "Robust Networks",
                                  "--keywords", "network;robustness;simulation")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            text = (output / "main.tex").read_text(encoding="utf-8")
            self.assertIn("Robust Networks", text)
            self.assertNotIn("MATHMODEL_MCM_", text)

    def test_placeholder_preview_requires_explicit_switch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "paper_workspace"
            output = root / "out"
            write_workspace(workspace)
            result = self.run_cli(workspace, output, "--allow-placeholders")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("模板预览保留显式", result.stdout)
            self.assertIn("MATHMODEL_MCM_TITLE", (output / "main.tex").read_text(encoding="utf-8"))

    def test_default_state_is_bound_to_workspace_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "paper_workspace"
            write_workspace(workspace)
            state_path = root / "state" / "decision_log.json"
            state_path.parent.mkdir()
            state_path.write_text(json.dumps({
                "competition": "mcm",
                "paper_metadata": {**GOOD_META, "title": "Workspace Bound State"}}), encoding="utf-8")
            output = root / "out"
            result = self.run_cli(workspace, output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Workspace Bound State", (output / "main.tex").read_text(encoding="utf-8"))


class DecisionLogSchemaTests(unittest.TestCase):
    def test_dynamic_counts_and_unobservable_token_usage_default_to_null(self) -> None:
        state = json.loads((ROOT / "templates" / "shared" / "decision_log.json").read_text(encoding="utf-8"))
        self.assertEqual(state["competition"], "mcm")
        self.assertIsNone(state["budget"]["tokens_used"])
        self.assertIsNone(state["budget"]["tokens_cap"])
        self.assertIsNone(state["stages"]["9"]["anti_patterns_check"]["total"])
        self.assertIn("mcm_control_number", state["paper_metadata"])
        self.assertIn("year", state["paper_metadata"])
        self.assertEqual(state["problem_meta"]["required_deliverables"], [])


if __name__ == "__main__":
    unittest.main()
