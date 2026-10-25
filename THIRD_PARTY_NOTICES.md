# Third-party notices

The original code, documentation, and LaTeX assembly templates in this repository are available under the root [MIT License](./LICENSE).

## Upstream workflow

The ten-stage workflow, state schema, feedback layers and gate scripts derive from `handsomeZR-netizen/mathmodel-skill` (MIT) via `zhy-ai0626/shumoskill` (MIT). The competition layer (rules, templates, compliance checks, AI disclosure, empirical statistics, writing guides) was rewritten for MCM/ICM in this repository.

## Code templates

`code-templates/` (Python/MATLAB templates and playbooks) comes from `Lupynow/math-modeling-skills` (MIT) and is redistributed unchanged under its license.

## MCM/ICM LaTeX template

`templates/latex/mcm/main.tex` and `smoke.tex` were written for this repository. The Summary Sheet header follows the public layout of COMAP's official summary-sheet template (Problem Chosen / Year MCM/ICM Summary Sheet / Team Control Number) but does not copy its source. Community templates such as `QTH1225/LaTeX-in-ICM-MCM` (LPPL) and `mcmthesis` are referenced only and not included. The template is an assembly aid, not an official COMAP template; COMAP's current instructions always take precedence.

## Empirical corpus

`competitions/mcm/empirical.json` contains descriptive statistics derived from 279 MCM/ICM Outstanding papers (2018–2025). The papers themselves are copyrighted by COMAP and their authors and are **not** redistributed. Sources used for analysis: locally owned copies, and the public collection `Jackksonns/MCM-ICM-Outstanding-Papers` (MIT, for the repository; paper copyrights remain with their owners). Scanned PDFs were parsed with the MinerU document-parsing service for analysis only. Short quotations in the guides are used for commentary and are attributed by control number.

## Runtime dependencies

Tools and libraries such as Python, Pandoc, TeX Live, MiKTeX, pdfLaTeX, newtx, and the Python packages listed in `templates/shared/requirements.txt` are installed separately by the user. They are not vendored by this repository and remain subject to their own licenses.

## External material

Contest rules, problem statements, datasets, websites, trademarks (MCM, ICM, COMAP), and other external sources are not relicensed by this repository's MIT License. Links, provenance notes, and derived statistics do not transfer ownership or redistribution rights.
