---
stage: 8
name: writing
duration_h: 16-30
inputs: ["decision_log.stages.0-7", "decision_log.task_type", "decision_log.problem_meta", "decision_log.paper_metadata"]
outputs:
  # AI 披露不写 `stage.8.*`。它的唯一权威位置是 `compliance.ai_usage`（顶层，跨阶段），
  # `render_ai_usage.py` 只读那里。
  - "stage.8.{section_word_counts, figures_per_subproblem, tables_per_subproblem, summary_drafts, compliance}"
  - "compliance.ai_usage"
  - "paper_workspace/*.md"
  - "paper_output/main.pdf"
loads_reference:
  - "competitions/mcm/current_rules.md"
  - "competitions/mcm/winning_patterns.md§7"
  - "competitions/mcm/phrase_bank.md"
  - "competitions/mcm/empirical.json"
  - "competitions/mcm/静默陷阱.md§三"
loads_template:
  - "competitions/mcm/paper_skeleton.md"
  - "competitions/mcm/abstract_template.md"
  - "competitions/mcm/Memo与Letter写法.md"
  - "templates/latex/mcm/"
feedback: ["L1", "L2_at_end"]
next: stage_09_review
---

# Stage 8 — 英文论文装配

把 Stage 0–7 已验证的产出装配成一篇连贯的英文论文。**写作时不产生新结果**；写作暴露出建模矛盾时，记录下来并触发定向 L2 回检。

英文写作从 Day 2 起并行（Stage 0 的分工），本阶段是收拢与定稿，不是从零翻译。

## 1. 先锁规则

1. 读 `competitions/mcm/current_rules.md`，打开其中的 COMAP 官方链接，确认是当届版本。
2. 把核对日期、来源、页数/字号/文件大小限制、匿名规则、AI 披露要求写进 `decision_log.compliance.ruleset`。
3. 重新读一遍所选题目的 "Your PDF solution ... should include" 段，与 `problem_meta.required_deliverables` 对照。
4. 仓库基线与官方冲突时，以官方为准并标记仓库过期。

实证分位、`winning_patterns.md`、rubric 分数都**不是**官方规则，只是写作辅助。

## 2. 25 页预算

先排预算再写（`paper_skeleton.md` §篇幅预算）：

| 固定开销 | 页 |
|---|---|
| Summary Sheet + Contents | 2 |
| Letter/Memo（题面要求时） | 1–2 |
| References | 1 |
| **留给正文** | **约 20** |

O 奖论文页数中位约 25 页：几乎都用满。超页时的删减顺序：附录代码 → 重复图表 → 背景叙述 → 合并相近的小节。**不缩字号、不改页边距**（M5）。

## 3. 节文件契约

在 `<cwd>/paper_workspace/` 下写这些文件（详见 `paper_skeleton.md`）：

| 文件 | 内容 |
|---|---|
| `01_summary.md` | Summary 正文，**最后写**；无一级标题（模板提供 Summary Sheet 页眉与标题） |
| `02_introduction.md` | `# Introduction`：Background / Restatement / Our Work（总览流程图） |
| `03_analysis.md` | `# Problem Analysis`（内容少可以只写一段过渡，但文件必须存在） |
| `04_assumptions.md` | `# Assumptions and Justifications` |
| `05_notation.md` | `# Notations`（Symbol / Description / Unit 三列表） |
| `06_models.md` | Data（如有）+ Model I … Model N，按 Task 组织 |
| `07_sensitivity.md` | `# Sensitivity Analysis` |
| `08_evaluation.md` | `# Strengths and Weaknesses` / Extensions / `# Conclusion` |
| `09_memo_letter.md` | **可选**：题面要求的 letter/memo；存在才渲染，新页开始 |
| `10_references.md` | `# References`，含 AI 工具条目 |
| `11_appendix.md` | `# Appendix`：只放关键代码片段（计入 25 页）；没有就写一句说明 |
| `12_ai_use_report.md` | **由脚本生成**：Report on Use of AI；未用 AI 时不存在 |

除 `01` 和 `12` 外，每个文件自带一个一级 Markdown 标题。顺序：正文 → letter/memo → 参考文献/附录 → **Summary 最后**。Summary 里每个数字都必须指向正文已有的结果。

## 4. 一条证据链

每个 Task 保持：`题面要求 → 假设 → 模型 → 求解 → 结果 → 验证 → 解读`

推进前核对：
- 符号与 Stage 4 一致，模型与 Stage 3 一致；
- 报告的数值来自 `results/`，不是重新手写的；
- 图有英文标签、单位、图题（图题写结论），非自制图片标注出处（M10）；
- 结论与引用可核对；
- Weaknesses 指向具体失效机制与改进方向（H1），且不是"没做完的活"（Stage 6 的 `check_selfaudit.py`）。

## 5. Summary Sheet 与 letter/memo

- Summary：按 `abstract_template.md` 写，一页、逐 Task 方法 + 数值结论、灵敏度结论、提到 letter/memo。
- Letter/Memo：按 `Memo与Letter写法.md`，读者、篇幅、限制逐字对照 `problem_meta.deliverable_specs`。

## 6. AI 使用台账与披露

本 skill 本身就是 AI agent，所以只要用了它，就**必须**维护 `decision_log.compliance.ai_usage`（格式见 `templates/shared/ai_usage_ledger.json`）。每次实质性使用记录：工具与版本、日期、阶段与目的、完整 query 与 output（或存档路径）、采纳了什么、人工如何核对与修改。翻译工具与 code copilot 也要记（COMAP 政策明确覆盖）。

```bash
python <skill>/scripts/render_ai_usage.py --paper-workspace paper_workspace/
```

生成 `12_ai_use_report.md`（Report on Use of AI，25 页之后，不计页数）与 `ai_tool_references.md`（把条目粘进 `10_references.md`，并在正文使用处 inline citation，句式见 `phrase_bank.md` §9）。显式 `[]` 表示未使用：不生成报告，提交表单 AI uses statement 选 No。

台账里不放 API key、token、个人信息。

## 7. 渲染

```bash
python <skill>/scripts/render_paper.py --workspace paper_workspace/ --output-dir paper_output/
```

元数据从 `decision_log.paper_metadata` 读（`mcm_control_number` / `problem` / `year` / `title` / `keywords`），也可用 `--control-number --problem --year --title --keywords` 覆盖。缺任何一项或仍是占位符（`1111111`、`ABCDEF`、`TITLE OF YOUR PAPER`），脚本拒绝正式编译。

渲染脚本会报三个数，**都要看**：
1. `PDF 已生成 (... N 页)`：PDF 总页数（含 AI 报告）
2. `计入 25 页上限的解答页数: M`：从 `main.aux` 读出，**超 25 直接 FAIL**
3. TeX 报错条数（log 里以 `!` 开头的行）

页数与预期不符就去 `paper_output/main.log` 找**第一条** `!`，从那里往后的内容都可能已经丢了。
编译不出来先跑 `doctor.py --require-renderer`（MiKTeX 缺包会卡住不报错，见 `静默陷阱.md` §3.3）。

最终提交文件名必须是控制号：`paper_output/main.pdf` → `<control number>.pdf`。

## 8. 图表与结果

| 要什么 | 用什么 |
|---|---|
| 常用六类图（分布/相关矩阵/拟合残差/灵敏度龙卷风/面板/流程） | `figures/starter.py`，改 `load_data()` |
| 样式（英文衬线字体、颜色 + 线型/填充双通道、灰度校样） | `figures/mcm_style.py`；规矩见 `figures/README.md` |
| Introduction 的 "Our Work" 总览图、每个 Task 的流程图 | `figures/flow_pptx.py` 出**可编辑 pptx**，改完另存为 PDF |

- 轴标签带单位（`ms.finish()` 强制非空）；对比类结果画在同一张图上；**不用双纵轴**
- O 奖论文图数中位约 14 张、表约 5 张（`empirical.json`）。图少不违规，但每个 Task 至少要有一张能说明结论的图
- 论文里的数字不要手抄：让脚本把关键结果写进 `results/summary.json`，Stage 9 的 `check_numbers.py` 逐个核对

## 9. 评分

L1 五维（由 `config/rubric.json` 生成，不要手改这张表）：

<!-- RUBRIC:BEGIN 8 -->
| 维度 | 满分行为 (10) | 失败行为 (1) |
|------|-------------|-------------|
| 1. Summary Sheet 信息闭环 (`1_summary_sheet`) | 一页内覆盖：背景一句 → 逐 Task 的方法 + 关键数值结论 → 验证/灵敏度 → 建议；不复述题面、不贴 Introduction（COMAP 明确判为弱摘要） | 复述题目或只有方法没有结果 |
| 2. 章节与交付物完整性 (`2_section_completeness`) | 题面列出的全部交付物齐全（目录、各 Task、letter/memo/report、参考文献、AI 报告如适用），证据链所需章节（假设+理由、符号、验证、灵敏度、优缺点）无空节 | — |
| 3. 技术沟通清晰度 (`3_communication_clarity`) | 英文准确简洁，图表自解释（图题说明结论），letter/memo 用非技术读者能懂的语言给出可执行建议 | — |
| 4. 公式 / 图表 / 引用 (`4_formulas_figures_citations`) | 公式/图/表编号规范，首次引用先解释；每个外部来源与 AI 工具均有 inline citation 与参考文献条目；非自制图表在原位标注出处 | — |
| 5. 25 页预算分配 (`5_page_budget`) | 解答 ≤25 页且无填充：核心结果在正文而非附录，附录代码只放关键片段，Summary/目录/letter 的篇幅已计入预算 | — |
<!-- RUBRIC:END 8 -->

## 退出条件

- [ ] 全部节文件存在且非空；题面要求的 letter/memo 已写（`09_memo_letter.md`）
- [ ] `render_paper.py` 编译成功，解答页数 ≤ 25，log 无 `!` 报错
- [ ] Summary 的每个数字能在正文/`results/` 找到同一个值
- [ ] AI 台账完整，AI 报告与参考文献条目已生成并放入
- [ ] 论文与 Stage 0–7 的 decision_log 一致；当届规则已复核并记录
- [ ] L1 通过，最终 L2 一致性检查没有未解决的 high-severity 冲突

→ 进入 `stage_09_review.md`
