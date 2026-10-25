# Letter / Memo 写法

> 近年过半的美赛题要求在 25 页内附一份写给非技术读者的 letter、memo 或 report（2026 年六题里四题要）。
> 它不是第二份 Summary，而是**一份能直接交给题面指定读者的建议书**。
> 本文的格式规律来自 O 奖论文原文（2024C、2024E、2024F、2025B、2025C、2025F 等），引用处都给了控制号。

## 1. 先从题面抄四件事

写进 `decision_log.problem_meta.deliverable_specs`：

| 项 | 2026 年例子 |
|---|---|
| 类型 | B: letter；C: memo；D/E: letter |
| 读者 | B: fictional MCM Agency；C: DWTS 制作方；D: 球队老板与总经理；E: Sungrove **或** Borealis 大学（不能两所都写） |
| 篇幅 | B: one page；C/D/E: 1–2 pages |
| 内容要求 | D: 推荐策略 + 取舍与风险 + 如何兼顾竞技与财务；C: 评委分与观众票合并方式的影响与建议 |

题面怎么说就怎么做。篇幅写"one page"就是一页，超了等于没按要求做。

## 2. Memo 的骨架（O 奖论文的共同格式）

```text
MEMORANDUM
To:      [题面指定的读者，原样照抄]
From:    Team #[control number]
Date:    [提交日期]
Subject: [一句话说清这份 memo 要对方做什么决定]

[1 句目的] This memo summarizes our findings on ... and recommends ...

Key findings                       ← 2–4 条，每条带一个数字
  • [发现 1：结论 + 数值]
  • [发现 2]

Recommendations                    ← 编号，动词开头，可执行
  1. [加粗标签]: [做什么，为什么，预期效果]
  2. ...

[可选：风险/注意事项 1–2 句]
[1 句收尾]
Sincerely, Team #[control number]
```

**实例**（结构摘录）：
- 2025B O 奖 2505199（写给朱诺旅游委员会）：`From / To / Date / Subject` 抬头 → "This memo summarizes our research ... and offers practical strategies" → **Research Findings**（2023 年 160 万邮轮游客、3.75 亿美元收入）→ **Key Results**（每日 12,000 人上限、人头费 15 美元、收入分配 30/40/30）→ **Effects of Measures** → **Recommendations** → Best regards。
- 2024C O 奖 2401298（写给网球教练）：抬头 → Dear Coaches → 一段讲模型告诉了我们什么 → **5 条加粗标签建议**（Consistency is Key / Aggressiveness Pays Off / Serve Smart / Build Resilience / Lead to Succeed）→ 收尾。
- 2025F O 奖 2513705（写给 ITU 峰会各国领导人）：每个发现用 "➢ Approach: ... ➢ Finding: ..." 两行，一页内三块，最后给出优先级排序的政策建议。

## 3. Letter 与 Memo 的区别

| | Letter | Memo |
|---|---|---|
| 抬头 | `Dear [读者],` | `To / From / Date / Subject` |
| 语气 | 更正式，可以有一段说明"我们是谁、为什么写信" | 直接，开门见山 |
| 结构 | 段落为主，可以有小标题 | 小标题 + 列表为主 |
| O 奖例子 | 2025C 2510862 写给各国奥委会；2024E 2400860 写给东京塔社区（含 Recommendation Plan / Implementation Timeline / Budget Overview 三个小标题） | 2024C 2401298、2025B 2505199 |

题面说 letter 就写 letter，说 memo 就写 memo。

## 4. 写给非技术读者的规则

1. **不出现公式和模型名缩写**。"Our Stacking model" 可以出现一次，"TMH-OMP" 这种自造缩写不要。
2. **每条发现都翻译成读者的语言**：不说 "the coefficient of x₃ is 0.42"，说 "每多投入 1 美元宣传，游客满意度提高约 0.4 分"。
3. **数字少而准**：一份 memo 4–8 个关键数字足够，全部能在正文找到出处。
4. **建议可执行**：动词开头，有对象、有量级、有时间。"Limit daily visitors to 12,000" 比 "Control the number of tourists" 好。
5. **说清取舍与风险**：2026D 题面明确要求 "discusses trade-offs and risks"；即使题面没要求，一句"这样做的代价是……"也会让建议更可信。
6. **落款只写控制号**，不写学校和姓名（COMAP 匿名规则）。

## 5. 放在哪里、怎么渲染

- 位置：Conclusion 之后、References 之前（O 奖论文的普遍做法），计入 25 页。
- 文件：`paper_workspace/09_memo_letter.md`。存在时 `render_paper.py` 自动渲染并从新页开始；不存在时模板跳过。
- 合规：`check_compliance.py` 读 `problem_meta.required_deliverables`，在 25 页解答里找 letter/memo 的特征（Dear / To: / MEMORANDUM），找不到就 FAIL。

## 6. 自查

- [ ] 读者与题面原文一致（包括"只能写给一个"这类限制）
- [ ] 篇幅不超过题面要求
- [ ] 删掉所有公式与自造缩写
- [ ] 每条建议都能在正文找到支撑的结果
- [ ] Summary 里有一句提到这份 letter/memo
