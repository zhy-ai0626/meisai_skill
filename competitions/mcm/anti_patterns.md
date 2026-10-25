# 反模式清单（MCM/ICM）

> 操作性检查项。A–J 是通用建模/写作失误（按美赛语境改写）；**M 组是美赛特有的失分点**，每条都标了可公开核对的出处：
> COMAP 规则页 / AI 政策 / 当届题面原文 / O 奖论文实证（`empirical.json`）。
> 它们不是官方评分权重，也不预测奖项；Stage 3 选模型、Stage 9 终审时逐条过。每条：现象 → 风险 → 修复。
> 逐题 Judges' Commentary 需会员权限，未纳入；没有出处的经验判断不写进本清单。

---

## A. Summary Sheet 类（高影响）

### A1. Summary 没有定量结论
- 现象: "Our model achieves good results" / "The results are reasonable"
- 风险: 评委第一轮主要读 Summary（COMAP: judges place considerable weight on the summary）；没有数字就看不出你到底解出了什么
- 修复: 每个 Task 一句"方法 + 关键数值 + 单位/场景"。O 奖论文 Summary 中数字个数中位约 9 个（`empirical.json` dims.summary_numbers）
- 例（2025C O 奖 2510862）: "...predicted the top three gold medal winners: the United States (56), China (33), and Australia (25)."

### A2. Summary 复述题目或剪贴 Introduction
- 现象: 前半页在讲背景和题目要求
- 风险: COMAP 规则原文：restate the problem / cut-and-paste from the introduction 的 Summary **被视为弱摘要**
- 修复: 背景压到 1–2 句，立刻进入 "We develop ..."；Summary 最后写

### A3. Summary 与正文不符
- 现象: Summary 说用了 LSTM，正文是 GRU；Summary 的数字与表 5 不一致
- 修复: 定稿前逐项回指正文的模型名、表号与数值；跑 `scripts/check_numbers.py`

### A4. Summary 溢出到第 2 页
- 现象: Keywords 被挤到第 2 页，或为塞下而缩字号
- 风险: Summary Sheet 是**一页**；缩字号违反 ≥12pt 规则
- 修复: 删背景句、合并同类方法句、去掉 Summary 里的公式；不缩字号、不改页边距

### A5. 关键词空泛或缺失
- 现象: "mathematical modeling; optimization"；或干脆没有
- 修复: 3–6 个：核心对象 + 核心方法 + 模型名。O 奖论文约 83% 写了 Keywords（2024 年起约 97%）

---

## B. 假设与符号类

### B1. 假设无理由
- 现象: "We assume the temperature is constant." 孤立一句
- 修复: 每条假设后跟 **Justification**：数据、文献或量级估计。O 奖论文目录里 "Assumptions" 出现率约 92%，几乎都用 "Assumption + Justification" 成对写法

### B2. 假设清单膨胀
- 现象: 十几条相近或不进入任何公式的假设
- 修复: 合并同义项，删除不参与推导/算法/验证的假设

### B3. 关键假设缺失
- 现象: 模型隐含了"各地区独立"却没写
- 修复: 对每个方程/约束问一句"这里默认了什么"，写出来

### B4. 符号重复定义或无单位
- 现象: $t$ 一会儿是时间一会儿是温度；Notations 表没有 Unit 列
- 修复: 全文一张 Notations 表（Symbol / Description / Unit），Stage 4 定稿后不再改口

### B5. 符号在出现前未定义
- 修复: 首次出现处定义，或指向 Notations 表

---

## C. 模型选型类

### C1. 模型名称与实际实现脱节
- 现象: 起了个"XX-YY Hybrid Model"的名字，实际只是一次线性回归
- 修复: 命名可以（O 奖论文普遍给模型起名/缩写），但名字下面必须有对应的方程与算法

### C2. 模型与问题不匹配
- 现象: 题问"随时间如何变化"，却给一个静态评价打分
- 修复: 先按 `problem_shape` 定方法主线（`题型与算法对照.md`），再选具体模型

### C3. 候选模型同族、选型理由薄弱
- 修复: Stage 3 至少比较两个不同结构的候选，写出为什么选这个、放弃了什么

### C4. 不验证求解可行性
- 现象: 写了 MINLP 却在 96 小时里解不出来
- 修复: 先跑小规模版本，确认能出结果再扩展

### C5. 题面说某量随条件变化，却拿一个常数交差
- 现象: 题面列出"温度会影响有效容量"（2026A），论文里却写 "capacity is taken as a constant from the datasheet"
- 风险: 题面列出的影响因素就是要你建模的东西；取常数等于没回应题目要求
- 修复: 题面点名的影响因素逐个进入模型（哪怕是简单的线性/分段关系），并对它做灵敏度；`check_selfaudit.py` 会扫出 "assumed constant" / "taken from literature" 这类自陈，要求逐条裁定

---

## D. 求解类

### D1. 结果不可追溯
- 修复: 每个进入论文的数字都能在 `results/` 里找到同一个值（`check_numbers.py`）

### D2. 没做 sanity check / 量纲检查
- 修复: 极限情形、守恒、量级估计；出现"人口为负""概率大于 1"立刻回查

### D3. 随机结果不可复现
- 修复: 固定 seed，报告多次运行的均值与区间

### D4. 设计了仿真却没跑出结果
- 风险: COMAP 刊发的参赛建议原话：*You don't want to end up with a paper that just says you designed a simulation but couldn't run it, with no results or analysis.*（Mitchener, "Go with What You Know", COMAP）
- 修复: 先用最简版本跑通出图，再加复杂度

---

## E. 结果分析类

### E1. 只报数字不解读
- 修复: 每张结果图/表后跟一段 "This means ..."：对决策者意味着什么

### E2. 图表不自解释
- 现象: 图题写 "Figure 3: Result"；坐标轴无单位；配色打印后分不清
- 修复: 图题写结论；轴带单位；用 `figures/mcm_style.py`（颜色 + 线型/填充双通道）。O 奖论文图数中位约 14 张

### E3. 不与基线对比
- 修复: 给一个朴素基线（常数、线性、现行政策），说明你的模型好在哪里、好多少

---

## F. 灵敏度与稳健性类

### F1. 没有灵敏度分析
- 风险: O 奖论文目录中 Sensitivity Analysis 出现率约 75%，Summary 里提到 sensitivity 的约一半；缺了它，"模型可信"没有证据
- 修复: 对最不确定的参数做扰动，报告结论是否改变

### F2. 只做单因素、幅度随意
- 修复: 扰动幅度要有依据（数据区间、文献范围）；关键参数做两两联合扰动或全局方法（Sobol/Morris，`SALib`）

### F3. "Our model is robust" 无证据
- 修复: 给出"参数在 ±X% 内，结论/排序不变"的具体区间

---

## G. 子问题协调类

### G1. 各 Task 各做各、口径不一
- 现象: Task 1 用 2023 年数据标定，Task 3 换了数据却沿用参数
- 修复: `decision_log.resume.settled_conventions` 写死口径；Stage 5 每问结束做跨问一致性回检

### G2. 子问题结论互相矛盾却没有回检
- 修复: 把前一问的"上界/不可行/最优"类断言用最终解代回检查

---

## H. 模型评价类

### H1. Strengths & Weaknesses 套话
- 现象: "Our model is simple and easy to understand"
- 修复: 优点对应具体证据（验证误差、可解释性）；缺点对应具体机制和改进方向。O 奖论文约 76% 有此节

### H2. 推广空泛
- 修复: 说清推广到什么场景、需要改哪个参数/模块（2025B O 奖 2505199 逐个举了夏威夷、优胜美地、新奥尔良的调整方式）

---

## I. 英文写作与排版类

### I1. 公式、图表编号错乱或悬挂引用
- 修复: 跑 `scripts/check_figures.py`；PDF 里出现 `??` 评委看得见

### I2. 术语前后不一致（机翻痕迹）
- 现象: 同一概念一会儿 "carrying capacity" 一会儿 "bearing capacity"
- 修复: Stage 4 建术语表，写作时统一；最后全文搜一遍同义词

### I3. 引用不规范
- 现象: 有图无出处；参考文献是"百度百科"
- 修复: 见 M10；参考文献用可核对的来源

### I4. 中式长句、被动语态堆叠
- 修复: 一句一个意思；用 "We + 动词" 主动句陈述自己的工作（O 奖 Summary 的典型句式见 `phrase_bank.md`）

---

## J. 流程协作类

### J1. 三人都全栈但都不深
- 修复: 建模 / 编程 / 写作各有主责与互备

### J2. 选题摇摆
- 现象: 六道题都看着能做，Day 2 还在换题
- 修复: Stage 1 用同一组维度比较，Day 1 中午前定题，写进 decision_log 后不再回头

### J3. 英文写作留到最后一天
- 修复: Day 2 起写作主并行写 Introduction / Assumptions / Model 描述

---

## M. 美赛特有失分点（出处可查）

### M1. 漏交题面要求的 letter / memo / report
- 出处: 当届题面 "Your PDF solution ... should include" 段。2026 年 B 要 one-page letter，C 要 1–2 页 memo，D/E 要 1–2 页 letter，A/F 不要
- 风险: 没完成题目要求；`check_compliance.py --require` 会 FAIL
- 修复: Stage 0/1 逐字抄入 `problem_meta.required_deliverables` 与 `deliverable_specs`

### M2. letter / memo 写成技术摘要
- 现象: 满篇模型名和公式，没有建议；或没有写给题面指定的读者
- 修复: 按 `Memo与Letter写法.md`：To/From/Date/Subject → 一句目的 → 2–4 条带数字的发现 → 编号建议 → 落款。2024C O 奖 2401298 的 memo 用 5 条加粗标签建议收尾

### M3. letter 写给了题面不允许的对象
- 出处: 2026E 原文 "write a one- to two-page letter to either Sungrove University or Borealis University (not both)"
- 修复: 读者、篇幅、数量限制逐字核对

### M4. 超过 25 页（附录代码挤占）
- 出处: COMAP 规则：25 页覆盖 Summary、目录、正文、参考文献、附录、代码
- 修复: 附录只放关键代码片段；完整代码不交（COMAP 不收、也不评）。`render_paper.py` 会报解答页数

### M5. 缩字号、改页边距换页数
- 出处: COMAP 规则：readable font of at least 12-point type
- 修复: 不改。超页就删内容

### M6. 身份信息泄露
- 现象: 图里带学校水印、致谢写了导师、PDF 属性作者是本机用户名、数据来源写"我校实验室"
- 出处: COMAP 规则：no identifying information other than the team Control Number
- 修复: `check_compliance.py` 查正文、元数据；图片水印只能人工翻

### M7. 用了 AI（含翻译、copilot）却不披露
- 出处: COMAP AI 政策：policy applies to ... even translations；undisclosed use → COMAP will take appropriate action
- 修复: 全程记 `compliance.ai_usage`；翻译工具也记。`render_ai_usage.py` 生成报告

### M8. AI 报告只写一句"用于润色"
- 出处: AI 政策示例要求对话类工具给出完整 Query 与 Output；只有翻译可以只写一句说明
- 修复: 台账里保存原始 query/output（`evidence` 字段指向文件）

### M9. AI 工具没有 inline citation、没进参考文献
- 出处: AI 政策：Use inline citations and list all AI tools used in the reference section of your 25-page solution
- 修复: 把 `paper_workspace/ai_tool_references.md` 的条目粘进参考文献，并在使用处标引用

### M10. 非自制图片/表格不注出处
- 出处: COMAP 规则：each image, figure, table ... not created by the team needs a specific cited reference at its location
- 修复: 图题末尾加 "(Source: [n])"

### M11. 题面限定了模型形式，却交了黑箱
- 出处: 2026A 原文：projects based solely on discrete curve fitting, timestep regression, or black-box machine learning without an explicit continuous-time model **will not satisfy this problem's requirements**
- 修复: Stage 1 把这类句子记为 `explicit_model_form`；Stage 3 选型必须满足它，数据只用于标定与验证

### M12. 数据来源不清或非开放
- 出处: 2026A 原文：All data used must be well documented and freely available ... under an open license；COMAP 规则要求注明所有外部来源
- 修复: Data 小节列出每个数据集的来源、时间范围与许可；C 题外加数据也要完整注明

### M13. C 题不报验证指标
- 出处: O 奖论文实证——C 题 Summary 中出现交叉验证/误差指标（R²、RMSE、准确率、置信区间）的约 51%，其他题号都在 11% 以下
- 修复: 留出验证集或时间序列交叉验证，报告指标与区间；预测要给区间而不是点值

### M14. 要估计的量没有观测，却做监督学习
- 出处: 2026C 原文：fan votes (which are unknown and a closely guarded secret)
- 风险: 没有标签就没法训练和验证；结论无从检验
- 修复: 改为约束反推（让估计结果与每周淘汰结果一致）+ 一致性/不确定性度量——题面本身就要求 "Provide measures of the consistency ... measures of your certainty"

### M15. E/F 题只交一张打分表
- 现象: 整篇就是"建指标 → 熵权/AHP → TOPSIS 排名"
- 依据: O 奖论文中 E/F 题评价类方法出现率高（AHP 36–38%、熵权 44–51%），但读 Summary 可见几乎都把评价嵌在预测、机理或优化模型里（例：2024E O 奖 2400860 用风险模型 + CAPM 定价再做保护评价；2025E 四篇 O 奖全部以微分方程食物网为主线）
- 修复: 评价只是一环；至少再有一个能回答"如果……会怎样"的模型，并给出情景比较

### M16. 目录缺失
- 出处: 近年题面把 Table of Contents 列为应含部分；O 奖论文约 87% 有目录（2022 年起 92–98%）
- 修复: 模板默认生成目录（计入 25 页）

### M17. 图里出现中文、截图低清
- 风险: 论文必须是英文；中文标签在英文字体下会变方框
- 修复: 用 `figures/starter.py` 起手；导出 300 dpi 或矢量 PDF

### M18. 先写中文再整篇翻译
- 风险: 最后一天翻译 20 页质量难保证；翻译工具也要按 AI 政策披露
- 修复: 直接用英文写，中文只用于队内讨论

---

## 使用本清单的边界

- **简化不是错误**：合理的简化假设 + 理由 + 灵敏度检验，比堆复杂模型更好。不要把"用了简单模型"判成反模式。
- 经验比例（"约 75%""中位 14 张"）只用于发现明显异常，**不是评分线**。图少但论证扎实的论文照样拿 O 奖（2025F O 奖 2507789 只有 2 张图，以新颖框架取胜）。
- 命中一条不等于必须改：要么修，要么在论文里写明为什么不适用（Stage 9 rubric 的要求）。

## 与其他文件的关系

- `winning_patterns.md`：正面做法；本清单：反面检查
- `phrase_bank.md`：A2/I4 的替代句式
- `Memo与Letter写法.md`：M1–M3 的展开
