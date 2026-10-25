#!/usr/bin/env python3
"""Unit tests for scripts/render_ai_usage.py."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "render_ai_usage.py"
SPEC = importlib.util.spec_from_file_location("render_ai_usage", MODULE_PATH)
assert SPEC and SPEC.loader
render_ai_usage = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = render_ai_usage
SPEC.loader.exec_module(render_ai_usage)


class AIUsageReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.entry = {
            "tool": "OpenAI ChatGPT",
            "model": "GPT-5",
            "version": "21 July 2026 version",
            "used_at": "2026-07-21T14:30:00+08:00",
            "use_stage": "Stage 7 / model evaluation",
            "purpose": "Check whether the sensitivity discussion is understandable.",
            "paper_sections": ["Abstract", "Section 7"],
            "query": "Review this sentence exactly: x | y and ```nested```.",
            "output": "The sentence needs a defined baseline and one quantified result.",
            "human_review": "We recomputed the result, checked the cited source, and rewrote the sentence ourselves.",
            "adoption": "Only the suggestion to state the baseline was retained.",
            "evidence": ["state/ai/AI-001.txt"],
        }

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_log(self, competition: str, entries: list[dict]) -> Path:
        path = self.root / "state" / "decision_log.json"
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps(
                {
                    "competition": competition,
                    "problem_meta": {
                        "year": 2026,
                        "letter": "A",
                        "title": "A Test Problem",
                    },
                    "compliance": {"ai_usage": entries},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return path

    def test_mcm_report_preserves_complete_query_and_output(self) -> None:
        log = self.write_log("mcm", [self.entry])
        paper_workspace = self.root / "paper_workspace"

        outputs = render_ai_usage.render_reports(log, paper_workspace)

        self.assertEqual(outputs, [paper_workspace / "12_ai_use_report.md",
                                   paper_workspace / "ai_tool_references.md"])
        report = outputs[0].read_text(encoding="utf-8")
        # The MCM template supplies the "Report on Use of AI" heading.
        self.assertFalse(report.startswith("#"))
        self.assertNotIn("# Report on Use of AI", report)
        self.assertIn(self.entry["query"], report)
        self.assertIn(self.entry["output"], report)
        self.assertIn("Human verification and revisions", report)
        # COMAP example format: "Tool (version, model)".
        self.assertIn("OpenAI ChatGPT (21 July 2026 version, GPT-5)", report)
        # The payload contains a triple-backtick run; the outer fence must grow.
        self.assertIn("````text", report)

    def test_reference_entries_are_generated_once_per_tool(self) -> None:
        log = self.write_log("mcm", [self.entry, dict(self.entry)])
        outputs = render_ai_usage.render_reports(log, self.root / "paper_workspace")
        refs = outputs[1].read_text(encoding="utf-8")
        self.assertEqual(refs.count("OpenAI ChatGPT. GPT-5"), 1)
        self.assertIn("reference section", refs)

    def test_non_conversational_disclosure_does_not_require_query(self) -> None:
        entry = {
            "tool": "DeepL",
            "model": "Translator",
            "version": "Jan 30, 2027 version",
            "use_stage": "Stage 8 / writing",
            "purpose": "Translate team notes from Chinese into English.",
            "paper_sections": "Section 3",
            "disclosure": "Uploaded our Chinese notes for Section 3 to be translated into English.",
            "human_review": "The team rewrote the translated text and checked every technical term.",
        }
        log = self.write_log("mcm", [entry])

        output = render_ai_usage.render_reports(log, self.root / "paper_workspace")[0]

        report = output.read_text(encoding="utf-8")
        self.assertIn("**Disclosure:**", report)
        self.assertIn(entry["disclosure"], report)

    def test_explicit_empty_ledger_removes_stale_report(self) -> None:
        """COMAP 只在用了 AI 时要求报告；[] 时删除旧文件，模板就会跳过该节。"""
        log = self.write_log("mcm", [])
        paper_workspace = self.root / "paper_workspace"
        paper_workspace.mkdir()
        (paper_workspace / "12_ai_use_report.md").write_text("stale", encoding="utf-8")
        (paper_workspace / "ai_tool_references.md").write_text("stale", encoding="utf-8")

        outputs = render_ai_usage.render_reports(log, paper_workspace)

        self.assertEqual(outputs, [])
        self.assertFalse((paper_workspace / "12_ai_use_report.md").exists())
        self.assertFalse((paper_workspace / "ai_tool_references.md").exists())

    def test_other_competition_is_rejected(self) -> None:
        log = self.write_log("cumcm", [self.entry])
        with self.assertRaisesRegex(render_ai_usage.LedgerValidationError, "mcm"):
            render_ai_usage.render_reports(log, self.root / "paper_workspace")

    def test_missing_ledger_is_not_silently_treated_as_no_use(self) -> None:
        log = self.root / "decision_log.json"
        log.write_text(json.dumps({"competition": "mcm"}), encoding="utf-8")

        with self.assertRaisesRegex(
            render_ai_usage.LedgerValidationError, "compliance.ai_usage"
        ):
            render_ai_usage.load_ledger(log)

    def test_query_and_output_must_be_recorded_together(self) -> None:
        broken = dict(self.entry)
        broken.pop("output")
        log = self.write_log("mcm", [broken])

        with self.assertRaisesRegex(
            render_ai_usage.LedgerValidationError, "必须同时填写"
        ):
            render_ai_usage.load_ledger(log)

    def test_use_stage_is_required(self) -> None:
        broken = dict(self.entry)
        broken.pop("use_stage")
        log = self.write_log("mcm", [broken])

        with self.assertRaisesRegex(
            render_ai_usage.LedgerValidationError, "use_stage"
        ):
            render_ai_usage.load_ledger(log)

    def test_interaction_and_disclosure_are_mutually_exclusive(self) -> None:
        broken = dict(self.entry)
        broken["disclosure"] = "A second, ambiguous disclosure path."
        log = self.write_log("mcm", [broken])

        with self.assertRaisesRegex(
            render_ai_usage.LedgerValidationError, "不能同时填写"
        ):
            render_ai_usage.load_ledger(log)


if __name__ == "__main__":
    unittest.main()
