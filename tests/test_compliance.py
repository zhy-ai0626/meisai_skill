#!/usr/bin/env python3
"""Regression tests for scripts/check_compliance.py (MCM/ICM rules).

不造真 PDF：pypdf 只被用来取「每页文本 + 字号 + metadata」，用一个假 reader
就能把所有判定分支覆盖到。真 PDF 上的实测见 tests/test_render_guard.py（编译模板后跑）
与开发时在 O 奖论文上的手动验证。
"""

from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"mcm_compliance_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


cc = load_script("check_compliance")
CN = "2712345"


class FakePage:
    def __init__(self, text, font_size=12.0):
        self._text = text
        self._size = font_size

    def extract_text(self, visitor_text=None):
        if visitor_text is not None:
            identity = [1, 0, 0, 1, 0, 0]
            visitor_text(self._text, identity, identity, {}, self._size)
        return self._text


class FakeReader:
    def __init__(self, pages, metadata=None, font_size=12.0):
        self.pages = [FakePage(t, font_size) for t in pages]
        self.metadata = metadata


def header(n, total):
    return "Team # %s Page %d of %d\n" % (CN, n, total)


def good_pages(total=8, ai=False, letter=False):
    body = "The model predicts a value of 9.4 h under mixed use. " * 20
    pages = [
        "Team # %s\nProblem Chosen\nA\n2027\nMCM/ICM\nSummary Sheet\nTeam Control Number\n%s\n"
        "Charging Ahead\nSummary\nWe develop a model.\nKeywords: SOC; ODE" % (CN, CN),
        header(2, total) + "Contents\n1 Introduction 3\n2 Assumptions 4",
        header(3, total) + "1 Introduction\n" + body,
        header(4, total) + "2 Model\n" + body,
        header(5, total) + "3 Sensitivity Analysis\n" + body,
    ]
    if letter:
        pages.append(header(len(pages) + 1, total) + "Letter to the MCM Agency\nDear MCM Agency,\nWe recommend ...")
    refs = "References\n[1] A. Author. Battery modeling. 2020."
    if ai:
        refs += "\n[2] OpenAI. ChatGPT (GPT-5, Jan 30, 2027 version)."
    pages.append(header(len(pages) + 1, total) + refs)
    if ai:
        pages.append(header(len(pages) + 1, total) + "Report on Use of AI\n1. OpenAI ChatGPT\nQuery: ...\nOutput: ...")
    return pages


def run(pages, metadata=None, size_bytes=1024, control=CN, required=(), ai_used=None,
        font_size=12.0, path=None):
    rep = cc.Report()
    reader = FakeReader(pages, metadata, font_size)
    with mock.patch("pypdf.PdfReader", return_value=reader), \
         mock.patch("os.path.getsize", return_value=size_bytes):
        info = cc.check_paper(path or ("%s.pdf" % CN), rep, control_number=control,
                              required=list(required), ai_used=ai_used)
    return {i["id"]: i["level"] for i in rep.items}, rep, info


class PaperCheckTest(unittest.TestCase):
    def test_clean_paper_passes(self):
        levels, rep, _ = run(good_pages())
        self.assertEqual(rep.count("FAIL"), 0, rep.items)
        self.assertEqual(levels["summary_first"], "PASS")
        self.assertEqual(levels["header_control"], "PASS")
        self.assertEqual(levels["page_limit"], "PASS")

    def test_missing_summary_sheet_fails(self):
        pages = good_pages()
        pages[0] = "Team # %s\nCover page with a nice picture" % CN
        levels, _, _ = run(pages)
        self.assertEqual(levels["summary_first"], "FAIL")

    def test_toc_on_first_page_means_overflow(self):
        pages = good_pages()
        pages[0] += "\nContents\n1 Introduction"
        levels, _, _ = run(pages)
        self.assertEqual(levels["summary_one_page"], "FAIL")

    def test_keywords_pushed_to_page_two_warns(self):
        pages = good_pages()
        pages[0] = pages[0].replace("Keywords: SOC; ODE", "")
        pages[1] = "Keywords: SOC; ODE\n" + pages[1]
        levels, _, _ = run(pages)
        self.assertEqual(levels["summary_fits"], "WARN")

    def test_page_without_control_number_fails(self):
        pages = good_pages()
        pages[3] = pages[3].replace(CN, "")
        levels, rep, _ = run(pages)
        self.assertEqual(levels["header_control"], "FAIL")

    def test_26_solution_pages_fail(self):
        pages = good_pages()
        filler = [header(i, 26) + "More results." for i in range(len(pages) + 1, 27)]
        levels, _, info = run(pages[:-1] + filler + pages[-1:])
        self.assertEqual(info["solution_pages"], 26)
        self.assertEqual(levels["page_limit"], "FAIL")

    def test_ai_report_does_not_count_toward_25(self):
        """25 页解答 + 3 页 AI 报告 = 28 页 PDF，仍然合规。"""
        pages = good_pages(ai=True)
        report = pages.pop()
        body = pages + [header(i, 25) + "More results." for i in range(len(pages) + 1, 26)]
        tail = [report, header(27, 28) + "Query: ...", header(28, 28) + "Output: ..."]
        levels, _, info = run(body + tail, ai_used=True)
        self.assertEqual(info["solution_pages"], 25)
        self.assertEqual(levels["page_limit"], "PASS")
        self.assertEqual(levels["ai_report"], "PASS")

    def test_ai_report_title_in_contents_is_not_the_report(self):
        """目录里也写着 Report on Use of AI——不能把目录页当成报告起点。"""
        pages = good_pages(ai=True)
        pages[1] += "\nReport on Use of AI 8"
        _, _, info = run(pages, ai_used=True)
        self.assertEqual(info["solution_pages"], len(pages) - 1)

    def test_small_font_fails(self):
        levels, _, _ = run(good_pages(), font_size=10.5)
        self.assertEqual(levels["font_size"], "FAIL")

    def test_chinese_residue_fails(self):
        pages = good_pages()
        pages[3] += "\n" + "中文标签" * 10
        levels, _, _ = run(pages)
        self.assertEqual(levels["english"], "FAIL")

    def test_required_letter_missing_fails(self):
        levels, _, _ = run(good_pages(), required=["letter"])
        self.assertEqual(levels["deliverable_letter"], "FAIL")

    def test_required_letter_present_passes(self):
        levels, _, _ = run(good_pages(letter=True), required=["letter"])
        self.assertEqual(levels["deliverable_letter"], "PASS")

    def test_ai_used_without_report_fails(self):
        pages = good_pages()
        levels, _, _ = run(pages, ai_used=True)
        self.assertEqual(levels["ai_report"], "FAIL")

    def test_ai_mentioned_in_text_triggers_report_requirement(self):
        """台账缺失时，正文提到 ChatGPT 也要求有 AI 报告。"""
        pages = good_pages()
        pages[3] += "\nThe text was polished with ChatGPT [2]."
        levels, _, _ = run(pages, ai_used=None)
        self.assertEqual(levels["ai_report"], "FAIL")

    def test_identity_field_fails(self):
        pages = good_pages()
        pages[2] += "\nAdvisor: Prof. Zhang"
        levels, _, _ = run(pages)
        self.assertEqual(levels["identity_hard"], "FAIL")

    def test_university_in_references_is_not_a_leak(self):
        pages = good_pages()
        pages[-1] += "\n[3] B. Author. Cambridge University Press, 2019."
        levels, _, _ = run(pages)
        self.assertEqual(levels["identity_soft"], "PASS")

    def test_university_in_body_warns(self):
        pages = good_pages()
        pages[2] += "\nData were collected at Some University laboratory."
        levels, _, _ = run(pages)
        self.assertEqual(levels["identity_soft"], "WARN")

    def test_pdf_author_metadata_fails(self):
        levels, _, _ = run(good_pages(), metadata={"/Author": "Zhang San"})
        self.assertEqual(levels["identity_meta"], "FAIL")

    def test_oversize_pdf_fails(self):
        levels, _, _ = run(good_pages(), size_bytes=26 * 1024 * 1024)
        self.assertEqual(levels["size"], "FAIL")

    def test_wrong_filename_fails(self):
        levels, _, _ = run(good_pages(), path="paper_final.pdf")
        self.assertEqual(levels["filename"], "FAIL")

    def test_template_placeholder_fails(self):
        pages = good_pages()
        pages[0] = pages[0].replace("Charging Ahead", "TITLE OF YOUR PAPER")
        levels, _, _ = run(pages)
        self.assertEqual(levels["no_placeholder"], "FAIL")

    def test_missing_references_fails(self):
        pages = good_pages()[:-1]
        levels, _, _ = run(pages)
        self.assertEqual(levels["references"], "FAIL")


class Stage9FieldsTest(unittest.TestCase):
    def test_manual_yields_null_not_false(self):
        rep = cc.Report()
        rep.add("identity_hard", "x", True)
        rep.add("identity_meta", "x", True)
        rep.add("page_limit", "x", True)
        rep.add("size", "x", True)
        rep.add("font_size", "x", None)
        rep.add("summary_first", "x", True)
        fields = cc.stage9_fields(rep)
        self.assertTrue(fields["anonymity_passed"])
        self.assertIsNone(fields["page_limit_passed"],
                          "没测到必须是 null，写成 false 会让人去修不存在的问题")

    def test_fail_yields_false(self):
        rep = cc.Report()
        rep.add("identity_hard", "x", False)
        rep.add("identity_meta", "x", True)
        self.assertFalse(cc.stage9_fields(rep)["anonymity_passed"])

    def test_deliverables_prefix_match(self):
        rep = cc.Report()
        rep.add("deliverable_letter", "x", True)
        rep.add("deliverable_memo", "x", False)
        self.assertFalse(cc.stage9_fields(rep)["deliverables_passed"])


class CliTest(unittest.TestCase):
    def test_other_competition_refused(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cc.main(["--paper", "fake.pdf", "--competition", "cumcm"])
        self.assertEqual(rc, 2, "只编码了 MCM/ICM 规则，不能冒充检查别的赛事")

    def test_missing_paper_refused(self):
        rc = cc.main(["--paper", "does-not-exist-xyz.pdf"])
        self.assertEqual(rc, 2)


class CheckNumbersThousandsTest(unittest.TestCase):
    r"""LaTeX 千分位 `\,` 必须先合并再取数，否则 119\,120 被切成 119 与 120。"""

    def setUp(self):
        self.cn = load_script("check_numbers")

    def test_thin_space_thousands_merged(self):
        vals = [v for v, _ in self.cn.extract_numbers(r"total area 119\,120 m$^2$")]
        self.assertIn(119120.0, vals)
        self.assertNotIn(119.0, vals)

    def test_plain_number_untouched(self):
        vals = [v for v, _ in self.cn.extract_numbers("efficiency 0.5038")]
        self.assertIn(0.5038, vals)

    def test_not_a_thousands_separator(self):
        vals = [v for v, _ in self.cn.extract_numbers(r"power 60.01\,MW")]
        self.assertIn(60.01, vals)

    def test_bare_long_number_extracted(self):
        vals = [v for v, _ in self.cn.extract_numbers("a total of 119120 square meters")]
        self.assertIn(119120.0, vals)

    def test_comma_thousands_still_work(self):
        vals = [v for v, _ in self.cn.extract_numbers("total 1,234.56 USD")]
        self.assertIn(1234.56, vals)


class GatesSmokeTest(unittest.TestCase):
    """doctor 的 gates-smoke：真跑提交门，而不是只确认文件存在。"""

    def setUp(self):
        self.doctor = load_script("doctor")

    def test_healthy_tree_passes(self):
        ok, detail = self.doctor._smoke_gates()
        self.assertTrue(ok, detail)
        for name in ("selfaudit", "numbers", "compliance"):
            self.assertIn(name, detail)

    def test_check_is_registered(self):
        checks = self.doctor.run_checks(competition="mcm", check_tools=False)
        self.assertIn("gates-smoke", {c.name for c in checks})


if __name__ == "__main__":
    unittest.main()
