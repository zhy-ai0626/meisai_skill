---
stage: 2
name: analysis
duration_h: 2-3
inputs:
  - "stage.1.selected"
  - "problem_pdf"
  - "attachment_data_paths"
outputs:
  - "stage.2.{decomposition, key_variables, key_constraints, objective_per_subproblem, data_schema, preprocessing_decisions, subproblem_dependency}"
loads_reference:
  - "references/rubrics.md§Stage_2"
  # Stage 2 Step 4 是全流程里**唯一**系统扫数据的地方，也是决定"要不要动数据"的地方。
  - "competitions/mcm/题型与算法对照.md§1"          # problem_shape 与 modifiers
  - "competitions/mcm/静默陷阱.md§二"               # 数据与建模的静默坑
feedback: ["L1"]
next: stage_03_model_selection
---

# Stage 2 — 问题深度解析与分解

**时长**: 2-3h | **反馈层**: L1

---

## 目标

把题目从**自然语言描述**转化为**数学语言骨架**: 识别决策变量、目标函数、约束、子问题间关系。这一步质量决定后续 5/6/8 阶段的天花板。

---

## 输入

- stage 1 输出: 选定题号 + 子问题清单 + 数据路径
- 题目原文 (再读一次)
- 题给数据（C 题必有）与队伍收集的公开数据（用 pandas/Read 扫一遍 schema）

## 产出

- 子问题分解树 (全部 Qi 的输入/输出/约束/目标)
- 关键变量清单 (覆盖实际模型所需变量并标注决策/状态/参数；不设凑数下限)
- 子问题间关联图 (谁依赖谁的结果)
- 目标函数雏形 (符号级,不必精确)
- 数据 schema 与变量映射
- **逐问的预处理决策表** (做什么、不做什么、凭什么；见 Step 4b)

---

## 操作流程

### Step 1: 题目精读 (30 min)

**精读三遍,每遍不同任务:**

第一遍 (10 min): 抓动词。题目让你做什么? "求最优..." / "预测..." / "评价..." → 决定问题类型。

第二遍 (10 min): 抓约束。哪些条件不能违反? 列出来。

第三遍 (10 min): 抓数据接口。哪些参数题目会给? 哪些要从题给数据提? 哪些要去找公开数据? 哪些要假设?

### Step 2: 子问题正式分解 (45 min)

对每个 sub-problem Qi,填写卡片:

```
Q1 卡片
├── 自然语言描述: <一句话提炼>
├── 输入:
│   - 题目给定参数: ...
│   - 数据: <文件名> 第 X 列 / 公开数据源 <名称+URL>
│   - 上游问题结果: 无 (Q1 是入口)
├── 输出 (最终决策变量):
│   - x_1, x_2, ... (含义、单位)
├── 约束:
│   - C1: ...
│   - C2: ...
├── 目标:
│   - 最小化/最大化 <什么>
├── 问题类型: <model_catalog 第几类>
└── 难度估计: easy / medium / hard
```

**关键**: 每张 Qi 卡片的“上游依赖”列必须明确写依赖哪些结果。只有题面、数学接口或业务机制支持时才建立依赖；“题目未禁止”不构成复用证据。没有合理依赖时写“无”，并保留理由。

### Step 3: 关键变量统一编号 (30 min)

跨子问题统一符号 (anti_pattern B4: 符号重复定义):

```
全局变量表 (stage 4 会复制到论文)

| 符号 | 含义 | 单位 | 类型 | 出现于 |
|------|-----|------|------|-------|
| x_i | 第 i 个产品的产量 | 件 | 决策变量 | Q1, Q2 |
| p_i | Price of product i | USD/unit | parameter (data file) | Task 1, Task 3 |
| α  | 折扣率 | 无量纲 | 参数 | Q3 |
| ξ  | 需求随机扰动 | 件 | 随机变量 | Q3 |
| ... |
```

只收录在目标、约束、数据映射或验证中实际使用的变量；缺少必要变量要补齐，无用途变量要删除。

### Step 4: 数据 schema 扫描 (30 min)

先跑脚本，再用 pandas 补细节。**脚本必跑**——它扫的四类结构性事实
（成分定和、重复测量、退化标签列、合并单元格残留）读题面看不出来，
漏掉任何一条都会让整条方法主线错，而且不报错：

```bash
python scripts/scan_attachments.py <数据文件或目录>
```

然后人工补 schema：

```python
import pandas as pd
df = pd.read_csv("2026_MCM_Problem_C_Data.csv")
print(df.shape, df.dtypes, sep="\n")
print(df.describe(include="all"))
print(df.isnull().sum())
```

输出 schema 卡片:
```
2026_MCM_Problem_C_Data.csv:
- 行数/列数: `<由扫描结果写入>`
- 时间跨度: `<由原始字段计算>`
- 缺失: `<列名、计数与比例；不得预填>`
- 异常: `<检测口径与实际命中；不得预填>`
- 结构性发现: `<scan_attachments 的 findings；无发现写"无">`
- 与变量映射: s_{i,w} ← 列 "week{w}_judge{j}_score"
- 来源与许可: <题给 / 公开数据源名称、URL、时间范围、许可>（COMAP 要求注明全部外部来源）
```

### Step 4b: 预处理决策闸门 (15 min，**有数据就必做**)

**扫完不等于处理完，但也不等于什么都不做。** 美赛的数据来源比国赛杂：
C 题给数据，其余题常要队伍自己拼几个公开数据源。判据是**这一步动数据，对这道题是否必要、理由能否写进论文**：

| 步骤性质 | 做不做 |
|---|---|
| 多个公开数据源合并：统一定义、单位、年份口径、国家/地区编码 | **做**——这是建模的一部分，在 Data 小节写清 |
| 数据源文档标明的无效值、哨兵值（-1、999、N/A） | **做**，引用数据源文档 |
| 同一类别多种写法（2026C 的大小写不一致） | **做**，规范化后再分组 |
| 领域方法内在要求的质控 | **做**，写明依据 |
| 常规统计预处理：去重、插补、类别平衡、按 3σ/分位删异常值 | **默认不做**；要做必须说清对这道题为什么必要 |

**逐 Task 填**：同一列在不同 Task 里可以有不同用法。

写入 `decision_log.stages.2.preprocessing_decisions`：

```json
{
  "<Task>": [
    {"column": "<列名或列组>",
     "action": "keep_as_is | aggregate | qc_filter | unit_convert | impute",
     "nature": "统计习惯 | 领域方法组成部分 | 口径统一",
     "rationale": "<为什么；引题面/数据源文档/领域规范，不能只写『常规做法』>",
     "rows_affected": "<实际影响行数；keep_as_is 写 0>"}
  ]
}
```

`action` 不是 `keep_as_is` 时，`nature` **不允许**填"统计习惯"——那等于说没有理由。

### Step 4c: 静默坑排查 (10 min)

`competitions/mcm/静默陷阱.md` §二的条目，逐条在本题数据上验一遍。它们的共同点是**不抛异常，只出错数**：

| 坑 | 怎么验 |
|---|---|
| 同一类别多种写法 | `df[c].str.strip().str.lower().nunique()` 比 `df[c].nunique()` 小就命中（`scan_attachments.py` 报 `case_collision`） |
| 同一列混合类型 | `df[c].map(type).value_counts()`；别直接 `to_numeric(errors="coerce")`，它把错的静默变 `NaN` |
| 多源口径不一致 | 对重叠年份/地区比对两个来源的同一指标，报差异比例；选哪个当准要在论文里写理由 |
| 时间序列信息泄漏（C 题） | 训练/验证按时间切分；标准化只用训练集拟合 |

`scan_attachments.py` 会扫 `mixed_dtype` / `case_collision` / `derived_mismatch` / `identity_collinear`，
但**脚本只给候选，判断要人做**——比如"两个来源对不上"到底哪个可信，只有读数据源文档才知道。

### Step 5: Task 关系图 (15 min)

以 mermaid / ASCII 表达:

```
<上游 Task> (<任务>)
  ↓ <有证据支持的输出接口>
<下游 Task> (<任务>)
  ↓ <有证据支持的输出接口>
最终: <题面要求的交付，含 letter/memo>
```

写入 `decision_log.stages.2.decomposition`。

### Step 6: 目标函数 / 核心关系雏形 (30 min)

每个 Task 写出符号化目标或核心方程（不必完整，要框架）：

```
Task 1: dS/dt = -P(t) / (V Q)          # continuous_dynamics 的核心方程
Task 2: max  Σ_i p_i x_i - C(x)  s.t. Σ_i x_i ≤ B, x_i ≥ 0
Task i: <与该 Task 匹配的符号化目标>
        若使用上游结果或 warm start，注明接口与依据；否则保持独立
```

### Step 7: 输出移交 (5 min)

写入 `decision_log.stages.2`:
```json
{
  "decomposition": [...],
  "key_variables": [...],
  "key_constraints": [...],
  "objective_per_subproblem": {"<Task>": "..."},
  "data_schema": {...},
  "preprocessing_decisions": {"<Task>": [{"column": "...", "action": "...",
                                          "nature": "...", "rationale": "...",
                                          "rows_affected": 0}]},
  "subproblem_dependency": {"<Task>": ["<only evidence-backed upstream IDs>"]}
}
```

---

## L1 Rubric (`rubrics.md` Stage 2)

<!-- RUBRIC:BEGIN 2 -->
| 维度 | 满分行为 |
|------|---------|
| 1. 子问题分解清晰度 (`1_subproblem_decomposition`) | 每个 Task 卡片完整：输入 / 输出 / 约束 / 目标均明确 |
| 2. 关键变量识别 (`2_key_variables_count`) | 覆盖目标、约束与数据接口，标注类型，无占位变量 |
| 3. 数学化程度 (`3_math_skeleton_present`) | 每个 Task 有符号化目标雏形；数学对象、输入输出、约束或评价关系与题意对应 |
| 4. 数据契合度 (`4_data_alignment`) | 题给/公开数据已扫描（`scan_attachments.py` 已跑），与变量映射清楚、来源与许可已记录；**且预处理决策逐 Task 记录在 `preprocessing_decisions`，每个「做」的动作都写了非「统计习惯」的依据**（判据见 `stage_02_analysis.md` Step 4b / `静默陷阱.md` §二；`check_data_decisions.py` 退出码须为 0） |
| 5. 子问题关联性 (`5_subproblem_dependency_identified`) | 每个 Task 的依赖或独立理由均已识别 |
<!-- RUBRIC:END 2 -->

> **不要在这里加第 6 维。** L1 rubric 全局固定 5 维，`score_artifact.py` 的 `DIM_WHITELIST[2]` 也只认 5 个键。
> 预处理决策折进 `4_data_alignment`——`config/dim_weights.json` 对 C 题给它 **1.4** 权重，正好是数据口径最要紧的题型。

---

## 常见坑

- 题目仅读一次就开干 → 强制读 3 遍
- 子问题间符号不统一 (B4) → 统一变量表
- 数据没扫 → strictly 必做 Step 4
- 为了“串起来”强行复用上游结果 (G1) → 只保留题面、数学或业务机制支持的依赖
- **无据改数**：删补、按 3σ 删异常值却没有理由 → 走 Step 4b 闸门
- **一律不动**：多源合并也不统一口径 → 逐 Task 判断，见 `静默陷阱.md` §2.10
- **数据来源不写**（M12）→ schema 卡片里必须有"来源与许可"一行

---

## 退出条件

1. 题面中的全部子问题卡片完整
2. 全局变量表覆盖后续模型实际所需项且无凑数项
3. 数据 schema 扫描完成（`scan_attachments.py` 已跑，findings 已入卡片）
4. 每个 Qi 的依赖关系明确 (依赖 / 独立,均有理由)
5. **数据口径闸门通过**（第 5、6 条不再靠人核，跑脚本）：

   ```bash
   python scripts/scan_attachments.py <数据文件或目录> --json > state/scan.json
   python scripts/check_data_decisions.py \
       --decision-log state/decision_log.json --scan state/scan.json
   ```

   退出码 1 表示有 FAIL，**Stage 2 不得退出**。它查：有数据却没填决策、
   缺 Task 的键、`action` 不在枚举、**动了数据却把 `nature` 写成"统计习惯"**、
   `rationale` 是套话或没有可追溯出处、`data_schema.silent_traps` 缺失。
   反方向（全 Task 全 `keep_as_is`）只报 WARN——多数题目这是对的，WARN 要逐条读完再决定。

   首次可从体检报告生成骨架：`--scan state/scan.json --scaffold`。
6. L1 rubric 全维 ≥7（数据口径与静默坑都计入 `4_data_alignment` 这一维）

→ 跳转 `stage_03_model_selection.md`
