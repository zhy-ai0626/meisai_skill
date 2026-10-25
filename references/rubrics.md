# 评分细则 (rubrics)

> **本文件里的 rubric 表格是生成物，不要手改。**
> 唯一数据源是 `config/rubric.json`；改完跑 `python scripts/render_rubric.py --write`。
> `doctor.py` 的 `rubric-sync` 每次都核，手改会被报出来。
> 各 stage 文件里的同名表格由同一份 JSON 渲染，因此不可能再漂。

> 美赛 MCM/ICM 的 5 维 rubric：stage 0-7 为通用建模框架，stage 8/9 已是美赛维度（Summary Sheet、交付物、25 页预算、`check_compliance.py`）。L1 Critic 直接 JSON 化使用。

---

## Overlay 协议 (v3.1)

| 层级 | 来源 | 加载 |
|------|------|------|
| 基础 | 本文件 stage 0-9 表格（由 `config/rubric.json` 生成） | 全部阶段 |
| 竞赛特化 dim 名 | `competitions/mcm/rubric_overlay.json` 的 `dim_whitelist`（当前为空：rubric.json 已是美赛维度） | score_artifact.py 自动合并 |
| 题型 dim 权重 | `config/dim_weights.json["mcm"][<task_type>]` | compute_verdict 加权 mean |
| 样本观察 | `competitions/mcm/empirical.json`（279 篇 O 奖论文） | Critic 评分前加载；只作参照 |

`task_type` 由 stage 1 选题后填入 decision_log; null 时 default 全 1.0 等价老逻辑。

---

## MCM/ICM 质量视角（官方约束 + 内部检查，不是官方评分权重）

| 维度 | 关键检查项 | 依据 |
|------|----------|------|
| **Summary Sheet** | 第 1 页、一页内、逐 Task 方法 + 数值结论、不复述题目 | COMAP 规则（Summary 被高度重视；复述题目 = 弱摘要） |
| **Approach & Modeling** | 回应题面每项要求（含模型形式硬约束）、假设有理由、从简到繁 | 当届题面；`anti_patterns.md` B/C/M11 |
| **Solution & Results** | 结果可复现、每个 Task 有数值结论、与基线比较 | `winning_patterns.md` §4 |
| **Validation** | 灵敏度/稳健性；C 题验证指标与预测区间 | O 奖实证：目录 Sensitivity 约 75%，C 题验证指标约 51% |
| **Communication** | 英文清晰、图表自解释、术语一致 | COMAP 刊发的参赛建议 |
| **Problem-specific deliverable** | letter/memo 读者与篇幅对、无公式、建议可执行 | 当届题面 "should include" 段 |
| **Compliance** | ≤25 页、≥12pt、页眉控制号、匿名、AI 披露 | `current_rules.md`；`check_compliance.py` |

---

## L1 阶段级 rubric (5 维 × 1-10)

每阶段产出后,Critic 输出以下 JSON:

```json
{
  "stage_id": 0-9,
  "iteration": 0-3,
  "scores": {
    "<dim_key_snake_case>": {"name": "中文名称", "score": 1-10, "evidence": "≤30字"},
    ...
  },
  "min_score": <number>,
  "mean_score": <number>,
  "issues": [
    {"severity": "high|medium|low", "where": "...", "anti_pattern_id": "A1|null", "fix": "..."},
    ...
  ],
  "verdict": "block | pass_early | pass | refine"
}
```

**dim key 命名约定**: 各 stage 的 5 个 `scores` 字段必须用**英文 snake_case**, 与 `feedback_layer1_critic.md §6` 各 stage 列出的固定集合精确一致 (`scripts/score_artifact.py` 加白名单校验)。下面各 stage 表第一列写中文是为了人读, 实际 JSON 输出用英文 key, **中文写在 `name` 子字段**。

退出条件: 见本文件末尾"阈值汇总"节, 与 SKILL.md / feedback_layer1_critic.md / score_artifact.py 三处统一。

---

### Stage 0 — 团队启动

<!-- RUBRIC:BEGIN 0 -->
| 维度 | 满分行为 (10) | 失败行为 (1) |
|------|-------------|-------------|
| 1. 角色分工明确性 (`1_role_clarity`) | 按实际人数覆盖建模/编程/写作责任，并设置互备 | 职责和交接人不明确 |
| 2. 工具就绪度 (`2_tools_ready`) | 题目需要的计算、写作、版本与沟通工具已验证 | 关键工具尚未试运行 |
| 3. 时间盒规划 (`3_time_planning`) | 按实际截止时间设置里程碑、关键路径和缓冲 | 无计划 |
| 4. 题目预扫信号 (`4_problem_scan`) | 已识别问题域 (优化/预测/评价等) | 未读题 |
| 5. 协作约定 (`5_collab_protocol`) | 命名规范、版本控制、daily standup 时间 | 无规范 |
<!-- RUBRIC:END 0 -->

---

### Stage 1 — 选题

<!-- RUBRIC:BEGIN 1 -->
| 维度 | 满分行为 |
|------|---------|
| 1. 候选覆盖与对比深度 (`1_three_options_depth`) | 当前全部可选题按同一组维度评估（难度 / 数据 / 契合度 / 工具 / 资料 / 主要风险），依据可追溯 |
| 2. 团队优势匹配 (`2_team_strength_match`) | 选题理由含"我们擅长 X,本题需要 X" |
| 3. 风险识别 (`3_risk_identification`) | 实质风险均有证据与应对；不重复凑数 |
| 4. 时间可行性 (`4_time_feasibility`) | 已估各阶段所需 h,合计不超过实际截止预算 |
| 5. 决策记录质量 (`5_decision_record_quality`) | rationale 与 rejected_alternatives 能回溯到题面、数据或团队约束 |
<!-- RUBRIC:END 1 -->

退出条件: 选定题号 + decision_log.json stage 1 节点完整 + 全维 ≥7。

---

### Stage 2 — 问题深度解析

<!-- RUBRIC:BEGIN 2 -->
| 维度 | 满分行为 |
|------|---------|
| 1. 子问题分解清晰度 (`1_subproblem_decomposition`) | 每个 Task 卡片完整：输入 / 输出 / 约束 / 目标均明确 |
| 2. 关键变量识别 (`2_key_variables_count`) | 覆盖目标、约束与数据接口，标注类型，无占位变量 |
| 3. 数学化程度 (`3_math_skeleton_present`) | 每个 Task 有符号化目标雏形；数学对象、输入输出、约束或评价关系与题意对应 |
| 4. 数据契合度 (`4_data_alignment`) | 题给/公开数据已扫描（`scan_attachments.py` 已跑），与变量映射清楚、来源与许可已记录；**且预处理决策逐 Task 记录在 `preprocessing_decisions`，每个「做」的动作都写了非「统计习惯」的依据**（判据见 `stage_02_analysis.md` Step 4b / `静默陷阱.md` §二；`check_data_decisions.py` 退出码须为 0） |
| 5. 子问题关联性 (`5_subproblem_dependency_identified`) | 每个 Task 的依赖或独立理由均已识别 |
<!-- RUBRIC:END 2 -->

---

### Stage 3 — 模型选型

<!-- RUBRIC:BEGIN 3 -->
| 维度 | 满分行为 |
|------|---------|
| 1. 候选质量与反事实覆盖 (`1_candidate_diversity`) | 所有合理替代均被评估；无合理替代时检索范围与原因可审计 |
| 2. 选型理由 (`2_selection_rationale`) | 每个候选有 (a) 适配理由 (b) 不选的原因，两者都能追溯到题面、数据或团队约束 |
| 3. 命名准确性 (`3_naming_variant`) | 每个修饰词均能定位到公式、代码与验证；允许标准名称 |
| 4. 求解可行性 (`4_solver_feasibility`) | 已确认求解库存在、时间复杂度可承受，且 toy demo 真跑通 |
| 5. 文献/理论支撑 (`5_literature_support`) | 关键选型主张有相关且已核验的来源；不以篇数代替相关性 |
<!-- RUBRIC:END 3 -->

championship 模式额外：red-team 提出最可能推翻模型选择的反例或证据缺口，并给出验证动作。

---

### Stage 4 — Foundation (假设 + 符号 + 术语)

<!-- RUBRIC:BEGIN 4 -->
| 维度 | 满分行为 |
|------|---------|
| 1. 假设必要性 (`1_assumption_count`) | 每条都对应实际模型依赖，无同义凑数项 |
| 2. 假设支撑 (`2_assumption_support`) | 每条都有来源与证据路径（文献 / 数据 / 物理或业务机制 / 可执行检验）；必要但尚未验证的标 `provisional` 并在 Stage 5/6 安排检验（反模式 B1） |
| 3. 符号唯一性 (`3_symbol_uniqueness`) | 同一符号不跨语境换义；需要单位的量均标明单位 |
| 4. 与模型一致性 (`4_consistency_with_model`) | 与 Stage 3 选定模型无矛盾；Stage 5 结束后回检一次 |
| 5. 术语规范 (`5_terminology_standard`) | 专业术语首次出现即给定义并中英对照；正文中可能歧义的术语均已定义，无未使用术语 |
<!-- RUBRIC:END 4 -->

---

### Stage 5 — 子问题递归循环 (per Qi)

每个 sub-problem 跑一次 5 维 rubric,**外加** stage-level overall:

#### Per-Qi rubric:

<!-- RUBRIC:BEGIN 5_per_qi -->
| 维度 | 满分行为 |
|------|---------|
| 1. 模型与问题契合 (`1_problem_fit`) | 目标函数 / 决策变量 / 约束 与题面一一对应 |
| 2. 数学严谨性 (`2_math_rigor`) | 符号一致, 推导无跳跃 |
| 3. 求解正确性 (`3_solve_correctness`) | 代码运行 + sanity check 通过 |
| 4. 结果表达 (`4_visualization`) | 每个关键论点有最合适的图、表或数值证据；不重复、不凑数量 |
| 5. 物理意义讨论 (`5_physical_meaning`) | 解释与结果证据绑定；baseline 仅在公平可比时使用 |
<!-- RUBRIC:END 5_per_qi -->

#### Stage-level (跨子问题):

原来这里只有「复用链」「变量一致性」两条散文，而白名单有 5 个键——
**另外三维在 canonical 表里根本不存在**，Critic 只能自己编判据。现已补齐：

<!-- RUBRIC:BEGIN 5 -->
| 维度 | 满分行为 |
|------|---------|
| 1. 子问题完整性 (`1_subproblem_completeness`) | 所有 Qi 都跑完 |
| 2. 依赖链 (`2_cross_reference_chain`) | 有依据的上下游接口均显式传递；无合理依赖时理由已记录 |
| 3. 符号一致 (`3_symbol_consistency`) | 全 Qi 用同一套 stage 4 符号 |
| 4. 证据表达 (`4_visual_density`) | 图、表与数值产物足以支持关键论点且无装饰性重复 |
| 5. 时间预算 (`5_time_budget`) | 在已确认的 stage 5 预算内完成；偏差已留痕并获用户确认 |
<!-- RUBRIC:END 5 -->

退出条件: 所有 Qi 通过 + 复用链满足 + 全维 ≥7。

---

### Stage 6 — 全局灵敏度 / 稳健性

<!-- RUBRIC:BEGIN 6 -->
| 维度 | 满分行为 |
|------|---------|
| 1. 验证设计契合度 (`1_multivariate_perturbation`) | 按核心风险选择 OAT / 联合扰动 / 重采样 / 数据留出 / 情景或边界分析，并说明为什么是这一种 |
| 2. 范围真实性 (`2_perturbation_realism`) | 参数域、数据切分与场景有题目、数据或领域依据 |
| 3. 输出完整性 (`3_output_completeness`) | 同时追踪关键性能、决策变化、可行性与失败样本中适用的部分 |
| 4. 定量可复核 (`4_robust_interval_quantitative`) | 报告样本、种子、计算方法、区间及判断标准 |
| 5. 边界诚实度 (`5_failure_warning`) | 不虚构临界点，明确已观察边界与未测试区域 |
<!-- RUBRIC:END 6 -->

L2 触发: 末尾跨阶段回检 stage 3 的模型选择前提是否被本节结果推翻。

---

### Stage 7 — 模型评价 + 推广

<!-- RUBRIC:BEGIN 7 -->
| 维度 | 满分行为 |
|------|---------|
| 1. 优点具体 (`1_strengths_specific`) | 每项都有证据路径、适用范围和不外推声明 |
| 2. 局限真实 (`2_weaknesses_real`) | 覆盖证据、受影响结论、替代方案与验证代价 |
| 3. 改进可执行 (`3_improvements_actionable`) | 有对照设计、指标、资源，并区分 planned / tested / adopted / rejected；未做对照实验时不填收益 |
| 4. 推广具体 (`4_generalization_concrete`) | 说明可复用结构、重新标定、新风险与最低验证，或诚实不主张推广 |
| 5. 自我批判可信 (`5_self_critique_credibility`) | 不隐瞒失败样本，不把计划当结果，不虚构提升幅度；不写「假设理想化」这类套话（`anti_patterns.md` 会自动检） |
<!-- RUBRIC:END 7 -->

---

### Stage 8 — 论文写作

<!-- RUBRIC:BEGIN 8 -->
| 维度 | 满分行为 (10) | 失败行为 (1) |
|------|-------------|-------------|
| 1. Summary Sheet 信息闭环 (`1_summary_sheet`) | 一页内覆盖：背景一句 → 逐 Task 的方法 + 关键数值结论 → 验证/灵敏度 → 建议；不复述题面、不贴 Introduction（COMAP 明确判为弱摘要） | 复述题目或只有方法没有结果 |
| 2. 章节与交付物完整性 (`2_section_completeness`) | 题面列出的全部交付物齐全（目录、各 Task、letter/memo/report、参考文献、AI 报告如适用），证据链所需章节（假设+理由、符号、验证、灵敏度、优缺点）无空节 | — |
| 3. 技术沟通清晰度 (`3_communication_clarity`) | 英文准确简洁，图表自解释（图题说明结论），letter/memo 用非技术读者能懂的语言给出可执行建议 | — |
| 4. 公式 / 图表 / 引用 (`4_formulas_figures_citations`) | 公式/图/表编号规范，首次引用先解释；每个外部来源与 AI 工具均有 inline citation 与参考文献条目；非自制图表在原位标注出处 | — |
| 5. 25 页预算分配 (`5_page_budget`) | 解答 ≤25 页且无填充：核心结果在正文而非附录，附录代码只放关键片段，Summary/目录/letter 的篇幅已计入预算 | — |
<!-- RUBRIC:END 8 -->

---

### Stage 9 — 终稿审核

**Stage 9 有两层反馈**（`stage_09_review.md` 的 `feedback: ["L1", "L3_panel", ...]`），
下面两张表各管一层。**别把它们混起来**：L1 是 5 维阶段级打分、键在
`score_artifact.py: DIM_WHITELIST[9]` 里；L3 是 5 视角 panel，走 `feedback_layer3_panel.md`。

#### L1 阶段级 (5 维，与其它阶段同构)

<!-- RUBRIC:BEGIN 9 -->
| 维度 | 满分行为 |
|------|---------|
| 1. 反模式覆盖 (`1_anti_pattern_coverage`) | `competitions/mcm/anti_patterns.md` 的全部索引项都过了一遍（数量以 `doctor.py` 报告为准），命中的每一条**要么已修，要么在论文里写明为什么不适用**；不允许"看过了" |
| 2. 图表定稿质量 (`2_visual_polish`) | 逐张过 `figures/README.md` 的硬规矩：轴标签带单位、无双纵轴、≥2 系列有图例、只标结论点、顺序色非彩虹；灰度校样已翻过一遍 |
| 3. Panel 共识 (`3_panel_consensus`) | L3 五视角无 high-severity 未决项；verdict 不靠权重覆盖异议（任一 high-severity 保持 `block`） |
| 4. 瓶颈已处理 (`4_bottleneck_addressed`) | 最低分维度与高影响 issue 已**定向修补并让受影响视角复核**，不是记录在案就算完 |
| 5. 提交件可编可查 (`5_pdf_compile_clean`) | `check_compliance.py` 无 FAIL：第 1 页是 Summary Sheet、解答 ≤25 页、每页页眉含控制号与页码、正文 ≥12pt、全英文、文件名=控制号.pdf 且 <25 MB、题面交付物齐全、用了 AI 则有 Report on Use of AI、无身份信息 |
<!-- RUBRIC:END 9 -->

时间压力不把已知违规或错误算成满分——第 5 维由脚本判定，不接受人工"应该没问题"。

#### L3 五视角 panel

每个 panelist 独立打分:

| Panelist | 关注 |
|----------|------|
| **数学严谨** | 定理引用、推导、边界条件、单位 |
| **模型贡献** | 设计必要性、基线比较、实质改动证据 |
| **代码正确** | 复现性、注释、变量名、可读性 |
| **写作呈现** | Summary、章节、图表、引用、英文表达 |
| **评委视角** | 30 秒内能否看懂核心问题、方法、结果与可信度 |

每位 panelist 输出:
```json
{"panelist": "...", "scores": {"1_dim": {"score": 8, "evidence": "..."}}, "issues": [], "verdict": "ready|refine|block"}
```

聚合器:
- 任一 high-severity issue 保持 `block`，权重不能覆盖
- 找最低分与高影响 issue，定向修补对应阶段一次
- 只让受影响视角复核；时间压力不把已知违规或错误变成 `ready`

---

## 阈值汇总 (与 SKILL.md / feedback_layer1_critic.md / score_artifact.py 统一)

**verdict 优先级 (从高到低)**:

| verdict | 触发条件 | 行为 |
|---------|---------|-----|
| `block` | issues 含 ≥1 high-severity | 暂停 skill, 用户介入 |
| `pass_early` | raw_min ≥ 9 AND weighted_mean ≥ 9 | iter-1 早退, 节省 token |
| `pass` | raw_min ≥ 7 AND weighted_mean ≥ 8 | 进下一阶段 |
| `pass_with_review` *(stage 5)* | 任 Qi mark_for_review 但加权阈值满足 | 进 stage 6, L2 必读 review_qis |
| `refine` | 其他 | section-patch 精修, iter+=1 (cap 3) |
| `refine_partial` *(stage 5)* | 任 Qi.min < 7, 但其他 Qi 已 pass | 仅 refine 标记 Qi, 不动其他 |
| `carryover` | iter == 3 仍 refine 或 refine_partial | 进下一阶段, 标记由 L2 处理 |

`weighted_mean` = Σ(s_i × w_i) / Σ(w_i), 其中 w_i 来自 `config/dim_weights.json` 题型加权 (clamp [0.7, 1.5]); `task_type=default` 全 1.0 等价老逻辑。

**内部质量档位**（用于工作流自检，不对应、也不预测竞赛奖项）：

| 档位 | 单维最低 | 均值 |
|---|---:|---:|
| 强 | ≥8 | ≥9 |
| 可交付 | ≥7 | ≥8 |
| 待复核 | ≥6 | ≥7 |
| 阻塞 | <6 | - |

---

## 与 winning_patterns / anti_patterns / empirical 的对应

本文件 rubric 项 ↔ `competitions/mcm/` 段落:
- Summary（stage 8 dim 1）→ `abstract_template.md` + winning_patterns §7 + anti_patterns §A
- 交付物完整（stage 8 dim 2）→ `Memo与Letter写法.md` + anti_patterns M1–M3
- 25 页预算（stage 8 dim 5）→ `paper_skeleton.md` 篇幅预算 + anti_patterns M4–M5
- 图表（stage 5 dim 4）→ winning_patterns §4 + anti_patterns §E
- 模型选型（stage 3）→ winning_patterns §2 + `题型与算法对照.md` + anti_patterns §C
- 假设支撑（stage 4 dim 2）→ winning_patterns §3 + anti_patterns §B
- 灵敏度（stage 6）→ winning_patterns §5 + anti_patterns §F
- 评价与推广（stage 7）→ winning_patterns §6 + anti_patterns §H

字数、图表数和公式数不作为官方硬阈值。`empirical.json` 统计自 279 篇 O 奖论文、没有对照组，只能用于异常提示。若 critique 提供 `evidence_metrics`，`score_artifact.py` 会打印可用的分位比较；它不会据此自动改分。
