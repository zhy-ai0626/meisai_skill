---
name: mcm-icm
description: Discovery shim for the mcm-icm workflow (美赛 MCM/ICM). Use when Codex invokes this skill for a COMAP MCM or ICM Problem A–F task, including problem selection, modeling, sensitivity analysis, English paper and Summary Sheet writing, letter/memo, AI-use report, or final 25-page compliance review. Do not use for CUMCM, generic data analysis, or non-competition paper review.
---

# mcm-icm shim

This wrapper exists so Codex can discover the skill from the `./skills/` layout.

Before doing any work, read `../../SKILL.md` and treat it as the primary workflow. Resolve `references/`, `competitions/`, `templates/`, `scripts/`, `figures/` and `config/` relative to `../..`.

Do not duplicate workflow rules here; the root `SKILL.md` is the source of truth.
