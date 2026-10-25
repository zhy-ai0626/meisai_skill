# Summary Sheet 写法与模板

> COMAP 规则原意：Summary 是第 1 页，评委非常看重它，获奖论文常常靠 Summary 质量与其他论文拉开差距；
> **最后写**；复述题目、从 Introduction 剪贴过来的 Summary 被视为弱摘要。
> 下面的结构与数字来自 O 奖论文（`empirical.json`；2024–2025 年的 Summary 逐篇读过），是观察，不是评分线。

## 1. 一页里要有什么

| 成分 | O 奖论文的做法 | 篇幅 |
|---|---|---|
| 标题 | 两段式："意象/问题 + 冒号 + 方法或对象"，如 *Stair Wear: Traces of History*、*Changing Tides: Momentum Swings in Tennis* | 1 行 |
| 开场 | 1–2 句背景或引语，马上转到 "we develop / we establish ..." | ≤ 3 行 |
| 总述 | 一句话交代整体框架（几个模型、各自干什么），常给模型起名或缩写 | 1–2 句 |
| **逐 Task** | 按题面任务顺序：**方法 + 关键数值结论**，必要时指向图表号 | 主体，约 70% |
| 验证 | 灵敏度/稳健性/交叉验证的结论（不是"做了"，是"结论不变/误差 X%"） | 1–2 句 |
| 交付物 | 题面要 letter/memo 时，一句话交代写给谁、核心建议 | 1 句 |
| 收尾 | 一句意义或展望（可选） | 1 句 |
| Keywords | 3–6 个 | 1 行 |

**长度**：O 奖 Summary 正文词数中位约 440 词（四分位 390–500）。12pt 单页基本就是这个量；超过 550 词通常意味着要么溢出，要么删了留白。

**数字**：Summary 中数字个数中位约 9 个，四分之一的 O 奖论文不到 5 个——但那些论文大多是政策/开放题，结论本身是定性的。数据题（C）和优化题（B）的 Summary 几乎都给出具体数值。

## 2. 逐 Task 段落怎么写

一个 Task = **做了什么（方法） → 得到了什么（数值/结论） → 意味着什么（一句解读）**。

✅ 2025C O 奖（2510862）：
> In Task 1: We prepared the data by creating three key indicators: medal lag, host country effect, and participant count. These ... served as inputs for a Stacking ensemble model, which outperformed individual algorithms with an R² of 0.88. ... predicted the top three gold medal winners: the United States (56), China (33), and Australia (25). We also calculated 95% confidence intervals using the Bootstrap method.

✅ 2025A O 奖（2501909）把结论写成考古学家能用的事实：
> The results demonstrate the steps were built about a century ago, typically used by three people walking side by side. Both directions were used, with an upward-to-downward ratio of 3:2 and a daily usage frequency of 261.

❌ 只有方法没有结果：
> For Task 2, we use the entropy weight method and TOPSIS to evaluate the policies and obtain the ranking.

**组织方式**三选一（O 奖论文都有人用）：
1. `For Task 1: ... For Task 2: ...`（最常见，评委对照题面最省力）
2. `Model I: ... Model II: ...`（模型跨多个 Task 时）
3. 加粗小标题列表，如 2024C O 奖 2401298：`Performance Metrics (Problem 1): ...` `Momentum Existence (Problem 2): ...`

## 3. 模板（填空用，写完删掉方括号）

```text
[Title: Hook phrase: What You Model / How]

Summary

[1–2 sentences: why this problem matters, with one concrete fact or number.]
To [goal stated in the problem's own terms], we develop [N] models: [Model I name]
for [purpose] and [Model II name] for [purpose].

For Task 1, we [method, with the key modeling idea in one clause]. [Key result with
number and unit.] [One clause of interpretation.] (Figure [k])

For Task 2, we [method]. [Key result.] [Comparison with baseline / current practice.]

For Task 3, ...

[Validation:] Sensitivity analysis shows that [conclusion] remains unchanged when
[parameter] varies within ±[x]%; [the most influential parameter is ...].

[Deliverable, if required:] Finally, we write a [one-page letter / memo] to [audience]
recommending [the 1–2 core actions].

[Optional closing sentence.]

Keywords: [object]; [core method]; [model name]; [key concept]
```

## 4. 常见问题

- **公式**：Summary 里尽量不放独立公式块；一个 display equation 就要吃掉 3–4 行。
- **引语开头**：O 奖论文里有人用（2024C 2401919 引网球教练、2409404 引德约科维奇、2024E 2401102 引 Bear Grylls），但它占篇幅，Summary 吃紧时第一个删。
- **"In this paper, we ..."**：O 奖 Summary 中最常见的开头之一，可以用，但别每段都用；高频句式见 `phrase_bank.md`。
- **AI 润色**：可以，但要按 COMAP AI 政策披露（Report on Use of AI 里贴出 query 与 output）。

## 5. 写完自查（Stage 8 L1 `1_summary_sheet` 维度）

- [ ] 删掉第一段后，评委还能知道你解决了每个 Task 吗？
- [ ] 每个 Task 至少有一个可核对的结论（数值、排序、阈值、是/否判断）？
- [ ] 数字与正文表格逐一对得上（`check_numbers.py`）？
- [ ] 题面要的 letter/memo 在 Summary 里提到了吗？
- [ ] 一页之内、≥12pt、Keywords 在第 1 页？（`check_compliance.py`）
