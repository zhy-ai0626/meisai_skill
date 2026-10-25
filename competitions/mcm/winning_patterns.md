# 正面做法（winning patterns）— 运行时主入口

> 各 Stage 需要经验模式时读本文件对应小节。数字来自 O 奖论文实证（`empirical.json`，2018–2025 共 279 篇，
> 论文原件不随 skill 分发），是**观察分位，不是评分线，不预测获奖**。与当届规则冲突时以 `current_rules.md` 为准。

---

## §1 Stage 1 — 六选一

美赛六道题同时公布，选题是真正的决策。用同一组维度给六道题打分（`stage_01_problem_selection.md`）：

1. **交付物负担**：要不要 letter/memo、读者是谁（2026 年六题四题要）
2. **数据**：给了数据（C 题固定给）还是要自己找公开数据（`open_data_required`，检索时间要算进预算）
3. **模型形式限制**：题面有没有 "will not satisfy this problem's requirements" 这类硬约束（2026A）
4. **团队匹配**：机理（A）/ 优化仿真（B）/ 数据（C）/ 网络（D）/ 评价+机理（E）/ 政策+数据（F）——方法分布见 `题型与算法对照.md` §2
5. **英文写作负担**：E/F 题的论证与建议写作量通常大于 A/B

O 奖数量按题号差别很大（2025 年：A 5 / B 7 / **C 18** / D 4 / E 4 / F 5 篇），这主要反映各题参赛队数，**不能当作"哪题容易拿奖"的依据**。

## §2 Stage 3 — 方法主线

先按 `problem_shape` 取主线（`题型与算法对照.md` §1），再按"最小可交付"路线（§3）推进。三条贯穿所有题型的做法：

- **从最简模型开始，逐步加因素**。O 奖 A 题论文几乎都是"基础方程 → 逐项加入影响因素 → 每项说明机理"（2024A 多篇从 Logistic/Lotka-Volterra 起步再加性别比反馈）。
- **给模型起名**。O 奖论文普遍给模型命名或缩写（"Stair Wear Model"、"Dual-Temporal Bayesian Network"、"TMH-OMP"），方便 Summary 与正文互相指引。但名字下面必须有方程与算法（C1）。
- **评价不是终点**。E/F 题的 AHP/熵权/TOPSIS 要嵌在一个能做情景比较的模型里（M15）。

## §3 Stage 4 — 假设与符号

- **Assumptions + Justification 成对写**：O 奖论文目录中 Assumptions 出现率约 92%。
- **Notations 表**（Symbol / Description / Unit）约 77% 的 O 奖论文有。
- 假设数量没有标准；每条都应进入某个公式、算法或验证（B2）。

## §4 Stage 5 — 求解与结果呈现

- **图**：O 奖论文图数中位约 14 张（四分位 12–18）。A 题偏多（中位约 17），E/F 偏少（约 12–13）。图少但论证扎实也能拿 O（2025F 2507789 只有 2 张）。
- **表**：中位约 5 张。参数表、结果对比表最常见。
- **每张图后一段解读**："This indicates ..." / "This means ..."（E1）。
- **每个 Task 一节**，节标题对应题面任务，评委按题面逐项找答案。
- 结果图用 `figures/starter.py` 起手（英文、灰度可读），流程图用 `figures/flow_pptx.py`。

## §5 Stage 6 — 灵敏度与稳健性

- O 奖论文目录中 Sensitivity Analysis 出现率约 75%；Summary 里提到 sensitivity 的约一半，A、B 题约 70%。
- 写法：扰动哪个参数、扰动多少（有依据）、**结论变不变**。O 奖 Summary 的典型句："Material hardness demonstrates a high sensitivity in our model. The model shows low sensitivity to weathering rate constant within 4 centuries ..."（2025A 2501909）
- C 题额外要验证：交叉验证/误差指标在 C 题 O 奖 Summary 中出现率约 51%，其他题号都在 11% 以下。

## §6 Stage 7 — 模型评价与推广

- Strengths & Weaknesses 约 76% 的 O 奖论文有单独一节；Extensions/Future Work 约 43%。
- 推广要具体到"换哪个参数/模块"（2025B 2505199 逐个说明夏威夷、优胜美地、新奥尔良的调整重点）。

## §7 Stage 8 — 论文装配

**结构**（O 奖论文的高频骨架，详见 `paper_skeleton.md`）：
Summary Sheet → Contents → Introduction（Background / Restatement / Our Work 流程图）→ Assumptions & Justifications → Notations → [Data] → Model I / II / ...（按 Task）→ Sensitivity Analysis → Strengths & Weaknesses → [Extensions] → Conclusion → **Letter/Memo** → References → [Appendix] → Report on Use of AI

**篇幅**：O 奖论文页数中位约 25 页（四分位 24.5–26，含部分论文附带的 AI 报告）——**几乎都用满了 25 页**。规划时按"每页都要有用"分配：Summary 1 + 目录 1 + letter/memo 1–2 + 参考文献 1 ≈ 4–5 页固定开销，正文约 20 页。

**参考文献**：中位约 10 条（四分位 7–14）。要可核对，AI 工具也要列入（M9）。

**目录**：2022 年起 O 奖论文 92–98% 有目录。**Keywords**：2024 年起约 97%。

**Summary**：见 `abstract_template.md`。正文词数中位约 440，数字中位约 9 个。

**Letter/Memo**：见 `Memo与Letter写法.md`。

**AI 披露**：2024、2025 年分别约 34%、42% 的 O 奖论文附了 Report on Use of AI——**如实披露 AI 使用并不妨碍拿 O 奖**。格式按 COMAP 政策逐条列工具、版本、query、output。

## §8 Stage 9 — 终审

- 先过机器门：`check_compliance.py`（25 页、页眉控制号、字号、英文、交付物、AI 报告、匿名）→ `check_numbers.py` → `check_figures.py` → `check_selfaudit.py`
- 再逐条过 `anti_patterns.md`
- 最后用 `rubric_overlay.json` 的 panel personas 做多视角审阅，**30-Second Judge** 视角只看 Summary 和图

## 可信度边界

- 文字版论文用 pdftotext 抽取，扫描版用 MinerU 解析；2023 年部分扫描件有水印遮挡，个别词句残缺，但不影响结构类统计。
- "出现率"基于目录/标题/Summary 的关键词匹配，会漏掉用非常规标题的论文，**偏低估**。
- 语料只有 O 奖论文，没有对照组——这些是"O 奖论文长什么样"，**不能推出"这样做就能拿 O 奖"**。
