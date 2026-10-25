# 论文骨架（MCM/ICM）

> O 奖论文的高频结构，对应 `paper_workspace/` 的节文件与 `templates/latex/mcm/main.tex` 的 section marker。
> 骨架是起点不是格式要求：题面要求的交付物与当届规则优先，章节可以按题目合并或拆分。
> 括号里的出现率来自 `empirical.json`（目录任意层级标题）。

| 页 | 章节 | 节文件 | 说明 |
|---|---|---|---|
| 1 | **Summary Sheet** | `01_summary.md` | 模板提供页眉（Problem Chosen / Year / Control Number）与标题；文件里只写 Summary 正文，无一级标题。Keywords 由 `paper_metadata.keywords` 填入 |
| 2 | Contents | （模板生成） | 计入 25 页 |
| 3– | **1 Introduction**（~95%） | `02_introduction.md` | 1.1 Problem Background → 1.2 Restatement of the Problem（用自己的话列出各 Task）→ 1.3 Our Work（一张总览流程图，`figures/flow_pptx.py`） |
| | 2 Problem Analysis（可选，~63%） | `03_analysis.md` | 各 Task 的建模思路、数据情况。内容少可并入 Introduction（文件仍需存在，可写一句过渡） |
| | **3 Assumptions and Justifications**（~92%） | `04_assumptions.md` | 编号列表：**Assumption** + *Justification* |
| | **4 Notations**（~77%） | `05_notation.md` | 三列表：Symbol / Description / Unit |
| | 5 Data（C 题必备，~58%） | 放在 `06_models.md` 开头 | 来源、时间范围、预处理决策（逐条有理由） |
| | **Model I … Model N** | `06_models.md` | 按 Task 组织，每节：模型建立 → 求解 → 结果 → 解读 |
| | **Sensitivity Analysis**（~75%） | `07_sensitivity.md` | 扰动哪些参数、多大、结论变不变；龙卷风图 |
| | **Strengths and Weaknesses**（~76%） + Extensions（~43%） + **Conclusion** | `08_evaluation.md` | 优缺点各 3–4 条，具体到证据 |
| | **Letter / Memo**（题面要求时） | `09_memo_letter.md` | 新页开始；见 `Memo与Letter写法.md` |
| | **References** | `10_references.md` | 中位约 10 条；包括 AI 工具条目 |
| | Appendix（可选，~15%） | `11_appendix.md` | 只放关键代码片段——计入 25 页 |
| 25 页之后 | **Report on Use of AI** | `12_ai_use_report.md` | 由 `render_ai_usage.py` 生成；未用 AI 时不存在 |

## 每节的写法要点

### Introduction
- Background 3–5 句，给一个具体数字或事实；不要从人类文明讲起。
- Restatement 用编号列表逐条改写题面任务——后面的模型章节和 Summary 都按这个编号走。
- Our Work 一张图 + 一句话："Our work is shown in Figure 1."

### Assumptions
```markdown
1. **The phone operates at a constant ambient temperature within each usage session.**
   *Justification:* Sessions last minutes to hours, while ambient temperature changes over
   hours; Section 6 relaxes this assumption.
```

### Notations
```markdown
| Symbol | Description | Unit |
|---|---|---|
| $S(t)$ | State of charge at time $t$ | % |

: Notations used in this paper
```
（表格下方的 `: 表题` 行会生成带编号的 Table N，正文才能写 "Table 2 shows ..."。没有表题也能编译，但评委无从引用。）

### Model 章节
每个模型一节，四段式：
1. **Model Establishment**：从最简形式开始，逐项加入因素，每项说明机理
2. **Solution**：算法、参数、数据来源
3. **Results**：图 + 表
4. **Analysis**：这说明什么、回答了题面哪个问题

### Sensitivity / Strengths & Weaknesses / Conclusion
见 `winning_patterns.md` §5–§6；Conclusion 逐 Task 回答题面问题，与 Summary 的数字一致。

## 篇幅预算（25 页）

| 部分 | 典型页数 |
|---|---|
| Summary + Contents | 2 |
| Introduction + Assumptions + Notations | 3–4 |
| Models（全部 Task） | 12–14 |
| Sensitivity + S&W + Conclusion | 2–3 |
| Letter/Memo | 1–2 |
| References (+ 关键代码) | 1–2 |

`render_paper.py` 编译后报告解答页数；超 25 页直接 FAIL。
