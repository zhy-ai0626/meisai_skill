---
stage: 1
name: problem_selection
duration_h: 2-4
inputs:
  - "stage.0.problem_scan"
  - "problem_pdfs[A..F]"
outputs:
  - "stage.1.{selected, rationale, rejected_alternatives, candidates_assessed, risks_identified}"
  - "root.task_type"
  - "root.problem_shape"
  - "root.problem_shape_modifiers"
  - "problem_meta.{letter, title, required_deliverables, deliverable_specs}"
loads_reference:
  - "references/rubrics.md§Stage_1"
  - "references/model_catalog.md§0"
  - "competitions/mcm/topic_specs.json"
  - "competitions/mcm/题型与算法对照.md"
  - "competitions/mcm/winning_patterns.md§1"
feedback: ["L1"]
next: stage_02_analysis
---

# Stage 1 — 选题（六选一）

**时长**: 2-4h | **反馈层**: L1 | **关键决策点**: 选题依据写入状态；出现新证据时可审计地重开决策

---

## 目标

在 MCM A/B/C 与 ICM D/E/F 六道题中，选出**最契合团队优势 + 时间预算 + 数据可获取性 + 交付物负担**的一题，
并让选择、否决与后续变更都有据可查；同时**从题面判定题型**（不是从题号推）。

选定后必须写入：

- `decision_log.task_type` ← `topic_specs.json[selected].task_type_key`（A_continuous / B_discrete / C_data / D_network / E_interdisciplinary / F_policy）。**只供 dim_weights 查表**。
- `decision_log.problem_shape` ← **从题面判定的题型**，六选一（`topic_specs.json.problem_shapes`），判据见 `题型与算法对照.md` §1。Stage 3 按它选方法主线。
- `decision_log.problem_shape_modifiers` ← `explicit_model_form` / `open_data_required` / `no_paired_labels` / `stakeholder_deliverable` / `repeated_measures`
- `decision_log.problem_meta.required_deliverables` 与 `deliverable_specs` ← **逐字抄题面**的 letter/memo/report 要求

> **⚠ 题号不是题型。** 2026A 是电池 SOC 连续模型，2025A 是楼梯磨损反演，2024A 是七鳃鳗种群动力学；
> 2025E 题名是"可持续"，四篇 O 奖却全部以微分方程食物网为主线。`topic_specs.json` 的近年真题与方法分布可以做先验，
> **题型必须从当届题面重新判定**。

---

## 操作流程

### Step 0: 加载题号体系与近年真题 (5 min)

读 `competitions/mcm/topic_specs.json`：题号 → task_type、近年真题、O 奖论文各题号常用方法（`observed_methods`）。

### Step 0.5: 数据体检 (10 min，有数据就必做)

```bash
python <skill>/scripts/scan_attachments.py <数据文件或目录>
```

C 题固定给数据（例 `2026_MCM_Problem_C_Data.csv`）；其他题有时给少量数据，更多时候要队伍自己找公开数据。

| 扫到什么 | 意味着 |
|---|---|
| `repeated_measures` | 同一对象多条记录 → 观测不独立，回归要用混合效应/GEE |
| `case_collision` | 同一类别多种写法（2026C 实测：`Social Media Personality` vs `Social media personality`）→ 分组前规范化 |
| `constant`（列名像标签却只有一个取值） | **真标签在别处**或根本没有标签 |
| `compositional` | 一组列之和为常数 → 成分数据，方法要变 |

结果写进 `problem_shape_modifiers`。题面要求自己找数据时加 `open_data_required`，并估计检索时间。

### Step 1: 六题卡片 (45 min，可分工并行)

为六道题各做一张同构卡片（Stage 0 预扫已有的直接复用）：

```
## B 题: <标题>
- 核心: <一句话>
- Tasks: <按题面编号逐项列出>
- 数据: <题给 / 需自行检索（列出候选来源）/ 无>
- 交付物: <题面 "should include" 段原文，例：One-page letter to MCM Agency>
- 模型形式限制: <题面硬约束原文，没有写 none>
- 预估题型: <problem_shape> + modifiers
- 主要风险: <证据>
```

### Step 2: 六维对比矩阵 (30 min)

| 维度 | 权重 | A | B | C | D | E | F |
|------|-----|---|---|---|---|---|---|
| 1. 团队方法匹配（`题型与算法对照.md` §2） | 0.25 | | | | | | |
| 2. 数据可得性与处理量 | 0.20 | | | | | | |
| 3. 模型形式限制与可行性 | 0.15 | | | | | | |
| 4. 交付物与英文写作负担 | 0.15 | | | | | | |
| 5. 时间可行性（96h 倒推） | 0.15 | | | | | | |
| 6. 创新与论证空间 | 0.10 | | | | | | |
| **加权总分** | | | | | | | |

每维评分必须有**一句话依据**（写在表下方）。不要用"历年哪题 O 奖多"打分：O 奖数量主要反映参赛队数（`winning_patterns.md` §1）。

### Step 3: 风险识别 (20 min)

为领先的 2–3 道题列出**有题面、数据或团队能力证据的实质风险**及应对：

```
风险 <ID>: <风险>
  证据: <题面原文 / 数据扫描结果 / 团队能力>
  应对: <缓解措施与触发 fallback 的条件>
```

美赛常见风险：公开数据找不到或口径不一（`open_data_required`）；题面限定模型形式而团队只会黑箱 ML；letter/memo 读者是陌生领域；开放题论证与英文写作量大。

### Step 4: 决策与锁定 (15 min) — 问答式

```
【基于六维对比矩阵，推荐选题】

  1) <题号> — <加权结果>，主要依据: <可核验依据>
  2) <题号> — <加权结果>，主要依据: <可核验依据>
  3) <题号> — ...
  4) 让我决定（推荐当前证据最充分的题）

回复数字。
```

用户选定后，**agent 自动写入** `decision_log.stages.1` 与 root 字段：
```json
{
  "selected": "B",
  "rationale": "... 可追溯依据 ...",
  "rejected_alternatives": [{"题号": "C", "reason": "..."}],
  "candidates_assessed": [...],
  "risks_identified": [...]
}
```
同步写：
- `task_type`、`problem_shape`（含判定依据：题面里的哪句话/哪个数据特征）、`problem_shape_modifiers`
- `problem_meta.letter`、`problem_meta.title`、`problem_meta.required_deliverables`（`letter` / `memo` / `policy_brief` / `report`）、`problem_meta.deliverable_specs`（读者、篇幅、限制，原文照抄）
- `paper_metadata.problem` ← 选定题号
- `stages.5.qi_count` ← 题面 Task 数；`stages.5.qi_weights` ← `[1.0] * qi_count`

**目标：北京时间周五中午前定题。** 决策版本留痕：若官方更正或新证据足以改变排序，触发 L2 并向用户做一次编号确认，在 `events.log` 记录原题号、新题号、证据与受影响阶段。无证据不换题（J2）。

### Step 5: 移交 (5 min)

给 Stage 2 的"问题输入包"：选定题号、Task 清单、数据路径/候选来源、预估题型与 modifiers、交付物要求、风险清单。

---

## L1 Rubric (`rubrics.md` Stage 1)

<!-- RUBRIC:BEGIN 1 -->
| 维度 | 满分行为 |
|------|---------|
| 1. 候选覆盖与对比深度 (`1_three_options_depth`) | 当前全部可选题按同一组维度评估（难度 / 数据 / 契合度 / 工具 / 资料 / 主要风险），依据可追溯 |
| 2. 团队优势匹配 (`2_team_strength_match`) | 选题理由含"我们擅长 X,本题需要 X" |
| 3. 风险识别 (`3_risk_identification`) | 实质风险均有证据与应对；不重复凑数 |
| 4. 时间可行性 (`4_time_feasibility`) | 已估各阶段所需 h,合计不超过实际截止预算 |
| 5. 决策记录质量 (`5_decision_record_quality`) | rationale 与 rejected_alternatives 能回溯到题面、数据或团队约束 |
<!-- RUBRIC:END 1 -->

退出: 全维 ≥7。

---

## 常见坑

- **J2** 选题摇摆：无新证据不重开
- **M1** 没抄交付物：Step 1 卡片里"交付物"一栏空着就不许进 Step 2
- **M11** 漏看模型形式限制：题面末尾的要求段与 "Note" 也要读
- 六道题都说不清核心：回 Stage 0 重读题目全文

---

## 退出条件

1. 六道题都有卡片并按同一组维度评估，选定一个当前有效题号
2. `stages.1` 五个 key 都有内容；`task_type`、`problem_shape`、`required_deliverables` 已写入
3. L1 rubric 全维 ≥7
4. 风险清单已有应对

→ 跳转 `stage_02_analysis.md`
