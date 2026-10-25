# MCM/ICM 当前规则基线

> **最后核对：2026-10-26**，对照 COMAP 已发布的 **2027** 竞赛说明。每届 Stage 0 必须重新打开下列官方页面核对；
> **COMAP 当届说明与当届题面永远优先于本文件**。本文件只记录核对过的条款与出处，不是官方文件的替代品。

## 官方来源

| 文件 | 出处 | 核对版本 |
|---|---|---|
| Rules, Registration and Instructions | <https://www.contest.comap.com/undergraduate/contests/mcm/instructions.php> | 2027 说明（2026-10-26 读取） |
| Use of AI Tools in COMAP Contests | 随题目包分发的 `Contest_AI_Policy.pdf` | v102025 |
| Submission Walk Through | 随题目包分发的 `MCM-ICM_SubProcess.pdf` | V20251232 |
| Summary Sheet 模板 | 官方 Word / LaTeX 模板（`assets/official/README.md` 有下载说明） | 2026 版 |
| 当届题面 | 六道题各自末尾的 "Your PDF solution of no more than 25 total pages should include" 段 | 每届不同，必须逐题读 |

## 时间（2027 届）

| 事件 | 美东时间 (EST) | 北京时间 |
|---|---|---|
| 报名截止 | 2027-01-28（周四）15:00 | 2027-01-29（周五）04:00 |
| 赛题公布、开始 | 2027-01-28（周四）17:00 | 2027-01-29（周五）06:00 |
| **停止一切修改** | 2027-02-01（周一）20:00 | 2027-02-02（周二）09:00 |
| PDF 提交截止 | 2027-02-01（周一）21:00 | 2027-02-02（周二）10:00 |
| 公布结果 | 2027-05-08 | — |

20:00 之后的任何修改都算违规；未按时提交可能被取消资格或降级。

## 提交硬条款（违反 = 降级或取消资格，机器可查的都在 `scripts/check_compliance.py`）

1. **25 页上限覆盖整份解答**：Summary Sheet、目录、正文、letter/memo 等题面特定交付物、参考文献、注释、附录、**代码**，全部计入。
2. **Report on Use of AI 不计入 25 页**，放在 25 页解答之后。
3. **第 1 页必须是 Summary Sheet**（用 COMAP 模板）。不加封面。
4. **每页页眉**写队伍控制号和页码，例：`Team # 0000000, Page 6 of 25`。
5. **英文**，可读字体 **≥ 12 pt**。缩字号换页数是违规。
6. **只交一个 PDF**，文件名 = 控制号（例 `2712345.pdf`），**< 25 MB**。每队只提交一次。
7. **匿名**：任何一页都不得出现学生、导师、学校/机构名称；PDF 中除控制号外不得有任何身份信息（文件属性里的作者也算）。
8. **不交程序、软件、数据库等其他文件**——它们不参与评审。要让评委看到的代码只能放进 PDF（并计入 25 页）。
9. 在线表单提交（<https://forms.comap.org/241335097294056>），需要控制号、Advisor ID、所选题号，并回答 **AI uses statement: Yes/No**。队员或导师均可提交。不发确认邮件。
10. 每队只选一道题：MCM A / B / C 或 ICM D / E / F。

## 引用与来源

- 所有外部来源用脚注、尾注或 inline citation 标注，并附参考文献列表。
- **每张非本队制作的图片、图表、表格，在其所在位置标注具体出处**。
- 直接引用必须加引号或以其他方式标明，并注明出处。

## AI 使用（COMAP 政策 v102025）

- 允许负责任地使用 AI，但**解题不需要 AI**。政策覆盖一切 AI 辅助技术：LLM、生成式 AI、数学软件、**翻译软件**、code copilot、自动补全。
- 必须写清用了哪个模型、用于什么目的；**正文 inline citation + 参考文献列出所用 AI 工具**（这部分在 25 页之内）。
- 必须核实 AI 生成内容与引用的准确性，警惕抄袭（AI 可能复现他人文本）。
- 用了 AI 就在 25 页之后追加 **Report on Use of AI**（无页数限制）。格式示例（COMAP 原文）：
  - `OpenAI ChatGPT (Nov 5, 2023 version, ChatGPT-4)` → `Query: <完整原样输入>` / `Output: <完整输出>`
  - 翻译用途只需一句说明，例：`Baidu Translate (Sep 10, 2025 version) — Uploaded entire paper written in Mandarin to be translated into English.` 不必贴全文。
  - code copilot：`GitHub CoPilot (Jan 16, 2024 version) — Auto-completions for code used in preparing our models.`
- COMAP 发现**未披露**的 AI 使用会采取相应措施。
- 链路：`decision_log.compliance.ai_usage` → `scripts/render_ai_usage.py` → `paper_workspace/12_ai_use_report.md`（+ `ai_tool_references.md` 供粘进参考文献）。显式 `[]` = 未使用，不生成报告，表单选 No。

## 题面层面的要求（每届不同，Stage 0/1 必须逐题抄录）

2026 届六道题的交付物要求，示范"同一年各题不同"：

| 题 | 题面列出的应含部分（25 页内） |
|---|---|
| 2026 A | Summary Sheet、目录、完整解答、in-text citation + 参考文献；AI 报告（如用） |
| 2026 B | 同上 + **one-page letter to MCM Agency** |
| 2026 C | 同上 + **1–2 页 memo**（给 DWTS 制作方：评委分与观众票怎么合并） |
| 2026 D | 同上 + **1–2 页 letter**（给球队老板与总经理：推荐策略、取舍与风险） |
| 2026 E | 同上 + **1–2 页 letter**（只能写给 Sungrove 或 Borealis 其中一所大学，不能两所都写） |
| 2026 F | Summary Sheet、目录、完整解答、参考文献；AI 报告（如用） |

六道题里四道要额外交付物，而且读者、篇幅、限制各不相同（E 题"不能两所都写"）。**逐字抄题面**，不要凭印象。

题面还可能**限定模型形式**。例：2026 A 题写明"仅基于离散曲线拟合、时间步回归或黑箱机器学习、没有显式连续时间模型的方案**不满足本题要求**"，且所用数据必须有出处、可免费获取、开放许可。这类句子写进 `problem_shape_modifiers: explicit_model_form`，Stage 3 选模型时必须满足。

## Summary Sheet（COMAP 说明原意）

- Summary 是解答的第 1 页，**评委非常看重它**，获奖论文常常就是靠 Summary 质量与其他论文拉开差距。
- **最后写**。要传达方法与最重要的结论；**复述题目、从 Introduction 剪贴过来的 Summary 被视为弱摘要**。

## 本文件之外

- 经验分位（`empirical.json`）只是"这篇是不是明显异常"的提示，**绝不能替代上面的官方限制**。
- 逐题 Judges' Commentary 需要 Mathmodels.org 会员权限，本仓库未纳入；`anti_patterns.md` 中凡引用评审观点的条目都标注了可公开核对的出处。
