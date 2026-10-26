# 项目记忆（Claude Code 与 Codex 共用）

> 这是**开发这个 skill** 时的交接记录，不是 skill 运行时文档（运行时看 `SKILL.md`）。
> Claude Code 通过根目录 `CLAUDE.md` 自动加载本文件；Codex 通过 `AGENTS.md` 的指引读取本文件。
> **每次开发会话结束前更新"当前状态"和"下一步"两节**，并把日期写成绝对日期。

最后更新：2026-10-26

## 项目是什么

- 仓库：<https://github.com/zhy-ai0626/meisai_skill>（公开），skill 名 `mcm-icm`，面向 COMAP 美赛 MCM/ICM（A–F 六题）。
- 由国赛 skill `zhy-ai0626/shumoskill`（CUMCM）改造而来：保留十阶段工作流、`decision_log.json` 状态、L1–L4 反馈层、合规闸门的骨架，规则/模板/实证层全部换成美赛。
- 维护规则与验证命令在 `AGENTS.md`，这里不重复。

## 当前状态（2026-10-26）

已完成并推送到 `origin/main`（首个提交 `4290fad`，139 个文件）：

- **规则层** `competitions/mcm/`：2027 届说明 + AI 政策 v102025（`current_rules.md`，2026-10-26 核对）、题号 → task_type、六种 problem_shape 与方法对照、54 条反模式（A–J 通用 + M1–M18 美赛特有，每条有出处）、Summary Sheet / Memo / Letter 写法、英文句式库、静默陷阱。
- **实证层** `competitions/mcm/empirical.json`：279 篇 O 奖论文（2018–2025），2022–2025 逐篇按 COMAP 官方结果页核对控制号与题号；扫描版用 MinerU 解析。只分发统计结果，不分发论文。
- **排版** `templates/latex/mcm/main.tex`：仓库原创的 Summary Sheet 版式，pdflatex + newtx，页眉 "Team # / Page N of M"，`\label{MathmodelSolutionEnd}` 标出 25 页解答的终点，AI 报告放在其后不计页。
- **脚本**：`render_paper.py`（Markdown 节文件 → LaTeX → PDF，超 25 页报错）、`render_ai_usage.py`（AI 使用台账 → Report on Use of AI）、`check_compliance.py`（页数、页眉、字号、匿名、文件名/大小等，针对 PDF）、`build_empirical.py`（重建实证层）、`doctor.py`（环境自检）等。
- **测试**：264 个单元测试全部通过；`doctor.py --skip-tools` 在装有 pypdf 时 13/13 通过。端到端渲染冒烟测试通过（6 页 PDF，合规 20/20）。

已知未完成：

- `kit/5_算法讲解手册.md` 的"出处"栏和部分测试数据仍是国赛例子（手册开头已注明）。
- 没有纳入逐题 Judges' Commentary（需要 Mathmodels.org 会员）。
- **还没有用真实赛题完整跑过一遍十阶段流程**：目前只验证了单元测试和渲染/合规链路。

## 下一步（按优先级）

1. **真题实跑**：用一道往年题（如 2026 C，本地有数据）在 Claude Code 和 Codex 里各跑一遍 Stage 0–9，记录卡住或输出不对的地方，按问题修 `references/stage_*.md` 和脚本。这是目前最大的未知。
2. **触发测试**：显式 `$mcm-icm` 应触发；国赛、HiMCM、普通数据分析、普通论文润色不应触发（见 `AGENTS.md` 末段）。
3. **加入 2026 年 O 奖论文**：2026 届结果已于 2026 年 5 月公布。拿到论文后按官方名单核对，放进语料目录，重跑 `build_empirical.py`，并更新 `competitions/mcm/README.md` 的样本表。
4. **赛前核对（2027-01-28 开赛前）**：重新打开 COMAP 2027 说明、AI 政策、官方 Summary Sheet 模板，逐条核 `current_rules.md`，更新核对日期。
5. 把 `kit/5_算法讲解手册.md` 的出处和国赛味的测试数据换成美赛例子。
6. 可选：加 GitHub Actions 跑单元测试和 `doctor.py --skip-tools`；有会员时补 Judges' Commentary 要点（只写摘要与出处，不搬原文）。

## 本机开发环境（zhy-ai0626 的 Windows 机器）

- **Python 用 `D:\conda\python.exe`（3.13）**。默认的 `python` 是 3.7，跑不了本仓库。
- `D:\conda` 里还没装 pypdf，所以 doctor 的 compliance-stack / gates-smoke 两项会报缺失；`D:\conda\python.exe -m pip install pypdf` 即可。
- TeX：MiKTeX + pdflatex。已手动装过 newtx、xpatch、xstring、carlisle、binhex、fontaxes、fancyhdr、lastpage。MiKTeX 缺包时会弹安装窗口导致编译"卡住"，排查时加 `--disable-installer`。
- 另有 Pandoc、pdftotext（poppler）。
- Git Bash 下传中文路径参数会乱码；涉及 `D:\Users\MSI-\Desktop\大二\美赛` 的命令用 PowerShell 跑。
- 推送 GitHub 要用户本人通过 Git Credential Manager 登录，agent 没有凭据。

## 语料与原始资料（都不在仓库里）

- 原始资料：`D:\Users\MSI-\Desktop\大二\美赛`（往年 O 奖论文、2026 题目与数据、写作模板、付费课程资料）。**付费课程资料、题面、论文都不能进公开仓库。**
- 解析后的语料：`C:\Users\MSI-\meisai_corpus\corpus\`（279 个 `<cid>.txt` + 70 个 MinerU `.md` + `_index*.json`）。2026-10-26 验证过：用它重跑 `build_empirical.py` 得到的结果与仓库里的 `empirical.json` 完全一致。
- 同目录 `tools/` 是当时的维护脚本：`extract_*.py`（pdftotext 抽取与建索引）、`mineru_batch.py`（MinerU v4 批量 API）、`method_freq.py`（方法出现率）。`official_O.json` 是从官方结果页整理的 O 奖名单。
- MinerU token **只通过环境变量 `MINERU_TOKEN` 传入**，绝不写进任何文件或提交。

重建实证层：

```bash
D:/conda/python.exe scripts/build_empirical.py --corpus C:/Users/MSI-/meisai_corpus/corpus --out competitions/mcm/empirical.json
```

## 踩过的坑

- `render_paper.py` 的节标记正则曾用 `\s*`，会吞掉空行，导致 "Summary" 和正文粘在一起；现在只匹配 `[ \t]`，模板里也加了 `\par`。
- 目录用 `\small` 会让字号检查误报 10.9pt；已去掉，`check_compliance.py` 也会跳过目录页。
- 对下载来的 O 奖论文跑合规检查，会看到中文水印、`/Author=COMAP` 之类的分发方痕迹，这不是检查器的 bug。
- 2024 年本地资料有标错题号的（如 2419588 实为 D 题），所以一律以官方结果页为准。
