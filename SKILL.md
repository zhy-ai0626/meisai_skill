---
name: mcm-icm
description: 美国大学生数学建模竞赛（MCM/ICM，美赛）A–F 题的端到端工作流。Use when the user works on COMAP MCM or ICM Problem A, B, C, D, E or F — from choosing among the six problems through modeling, solving, sensitivity analysis, English paper writing, Summary Sheet, required letter/memo, AI-use report and final 25-page compliance review. 10 stages with persistent decision state, COMAP 2027 rules baseline with AI-disclosure gating, and an empirical layer distilled from 279 Outstanding papers (2018–2025). Do not trigger for CUMCM/国赛, HiMCM, 电工杯, generic model selection, or ordinary data analysis.
---

# mcm-icm — 美赛 MCM/ICM 工作流 (v1.0)

10 阶段把 96 小时的美赛协作变成可恢复、可检查的流程。用户回答关键问题，agent 维护状态与脚本。
每阶段产出经过 rubric 自评、定向精修与跨阶段一致性回检；Stage 8–9 先遵守 COMAP 当届规则，再做多视角终审。
实证层来自 **279 篇 O 奖论文（2018–2025，逐年对照官方 Outstanding 名单核对）**。

**与上游的关系**：工作流骨架来自 `zhy-ai0626/shumoskill`（国赛版，其上游为 `handsomeZR-netizen/mathmodel-skill`，MIT），
本仓库把竞赛层整体换成美赛：规则、模板、合规检查、AI 披露、实证语料全部重做，国赛内容已移除。

---

## 入口

| harness | 入口文件 | 用户交互工具 | 状态文件 |
|---------|---------|-------------|---------|
| Claude Code | `SKILL.md`（本文件） | `AskUserQuestion` 工具 | `<cwd>/state/decision_log.json` |
| Codex CLI / app | skill 目录中的 `SKILL.md`（发现层薄壳 `skills/mcm-icm/SKILL.md`、UI 元数据 `agents/openai.yaml`） | markdown 编号列表 | 同上（**互通**） |

安装位置：Claude Code `~/.claude/skills/mcm-icm/`；Codex `$HOME/.agents/skills/mcm-icm/`。
用户可直接说"开始美赛建模"或"使用 `$mcm-icm`"。跨 harness 细节见 `references/harness_compat.md`。

---

## 问答式优先 (Friendly Mode)

用户只需回答**编号问题**，不应被要求手敲 bash / python / json。

- 离散选项（选题 / 选模型 / verdict 决策）→ **必须**用问答式，并给"让我决定（推荐 X）"兜底
- 自由文本（PDF 路径 / 截止时间 / 控制号）→ 单行回复
- 状态读写（decision_log.json）→ agent 自动完成

---

## 路径解析协议（任何阶段必读）

| 类型 | 位置 | 例 |
|------|------|-----|
| skill 内通用 | skill 根目录的相对路径 | `references/stage_05_subproblem_loop.md`, `templates/shared/decision_log.json` |
| 美赛特化 | `competitions/mcm/` | `current_rules.md`, `winning_patterns.md` |
| 用户产物 | 用户工作目录的相对路径 | `<cwd>/state/`, `<cwd>/results/`, `<cwd>/figures/`, `<cwd>/paper_workspace/`, `<cwd>/paper_output/` |
| 环境变量 | `MATHMODEL_STATE_DIR` / `MATHMODEL_COMPETITION`（恒为 `mcm`） | scripts 用 |

---

## 美赛特化层（优先读这里）

| 文件 | 内容 | 何时读 |
|---|---|---|
| `competitions/mcm/current_rules.md` | **COMAP 2027 规则基线**：25 页上限的覆盖范围、页眉控制号、≥12pt、匿名、单 PDF < 25 MB、北京时间截止、AI 政策 v102025、各题交付物 | Stage 0 必读；Stage 9 逐条核 |
| `competitions/mcm/winning_patterns.md` | **运行时主入口**：各 Stage 的正面做法与 O 奖实证数字 | 各 Stage 按需 |
| `competitions/mcm/题型与算法对照.md` | 六种 problem_shape 判据、方法主线、O 奖论文各题号方法分布 | Stage 1 判题型、Stage 3 选模型 |
| `competitions/mcm/anti_patterns.md` | A–J 通用 + **M 组美赛特有失分点**（漏交 letter/memo、超页、AI 未披露、题面限定模型形式……），每条有出处 | Stage 3、Stage 9 |
| `competitions/mcm/abstract_template.md` | **Summary Sheet** 写法与模板 | Stage 8 |
| `competitions/mcm/Memo与Letter写法.md` | 题面要求的 letter / memo | Stage 1 抄要求、Stage 8 写 |
| `competitions/mcm/paper_skeleton.md` | 论文骨架 ↔ 节文件 ↔ 25 页预算 | Stage 8 |
| `competitions/mcm/phrase_bank.md` | 英文句式库 | Stage 8 |
| `competitions/mcm/静默陷阱.md` | 不报错只出错的建模/数据/提交陷阱 | Stage 0/5/6/9 |
| `competitions/mcm/empirical.json` | O 奖论文观察分位 | L1 critic 锚点、`check_figures.py` |
| `templates/latex/mcm/main.tex` | 原创模板：COMAP Summary Sheet 版式、每页 "Team # / Page N of M"、目录、letter/memo 与 AI 报告可选块 | Stage 8 |
| `figures/mcm_style.py` + `figures/starter.py` + `figures/flow_pptx.py` | 英文图表样式（灰度可读）、六段绘图起手式、可编辑 pptx 流程图 | Stage 0 自检、Stage 5/8 出图 |
| `config/rubric.json` + `scripts/render_rubric.py` | L1 rubric 唯一数据源（stage 8/9 为美赛维度：Summary Sheet、交付物完整性、25 页预算） | 改判据时 |
| `code-templates/` | 30 个代码模板 + 12 个 playbook（来自 `Lupynow/math-modeling-skills`，MIT） | Stage 5 |

**可信度边界（必须遵守）**：
- COMAP 当届说明与当届题面永远优先于本仓库；
- 实证分位只用于"这篇是不是明显异常"的提示，**不是评分线，也不预测获奖**；
- 2023 年扫描件有水印遮挡，引用其原文前核对原 PDF（论文原件不随 skill 分发）。

---

## Quick Start（用户首次说"开始建模"）

```
1. 一段话介绍 (≤50 字): "启动美赛 MCM/ICM 工作流，10 阶段，全程问答式。"

2. 收集启动字段；用户已经提供或 state 已记录的不再询问，只把尚缺字段合并成一轮问答:
   - 题目状态（已公布 + PDF 路径 / 未公布 / 已选定 A–F）
   - 队员数 + 各人擅长（建模 / 编程 / 英文写作）
   - 截止时间（默认按 current_rules.md 换算成北京时间）
   - 队伍控制号（7 位；可稍后补，Stage 8 渲染前必须有）

3. 自动初始化 (agent 自动完成, 不要让用户编辑 json):
   - 不存在 `<cwd>/state/decision_log.json` → 创建目录并复制 `<skill>/templates/shared/decision_log.json`
   - 已存在 → 读 current_stage 决定恢复点

4. **先读 `competitions/mcm/current_rules.md`**，核对 COMAP 官网有无更新并写入 compliance.ruleset

5. 进入 Stage 0 (`references/stage_00_kickoff.md`)；若题面未公布，完成环境与协作准备后保持 `qi_count=null` 并等待，不进入 Stage 1
```

**已有 state 触发**（用户中途回到 skill，或上下文被压缩后换了会话）:
```
1. 读 `<cwd>/state/decision_log.json` 的 current_stage
2. **读 resume 段**：
   - `settled_conventions` → 这些口径已经定死，不许重新决定
   - `in_flight` → 上次停在哪个 Task、做到哪一步
   - `next_actions` → 下一步做什么，照做，不要重新读题面自己另想一套
   - `open_questions` → 有未决问题就先问用户
   - `reproduce` → 要复现数值就按 entrypoints 与 seed 跑，别重写脚本
3. 清点磁盘：results/ figures/ paper_workspace/ 里已有什么，别重算已有的
4. 加载对应 stage_NN.md
```
> 恢复时最容易犯、也最难发现的错不是"忘了做什么"，而是**把某个口径换了个同样合理的定法**
> ——平均改成加权、起算年份换一个、异常值判据松一档。前后两问的数字就不可比了，而且**任何脚本都不会报错**。

---

## 三模式

| Mode | 上下文策略 | 反馈层 | 用途 |
|---|---|---|---|
| fast | 只保留当前阻断项与最小证据 | L1 单次 | 选题试跑 / sanity check |
| standard | 按阶段加载并保留决策摘要 | L1+L2 | 默认主流程 |
| championship | 终审阶段扩展证据与独立视角 | L1+L2+L3+L4 + red-team | 提交前最后冲刺 |

按距截止剩余时间推荐：> 72h standard（最后 8h 升 championship）；24–72h standard；8–24h fast 关键阶段 + championship 终审；< 8h 直接进 Stage 9。

---

## 10 阶段索引

| # | 阶段 | reference | 时长 | 反馈 | 美赛要点 |
|---|------|-----------|------|------|-----------|
| 0 | 团队启动 + 六题预扫 | `stage_00_kickoff.md` | 1h | L1 | 北京时间截止、控制号、编译链 smoke、逐题抄交付物 |
| 1 | 选题（六选一） | `stage_01_problem_selection.md` | 2-4h | L1 | 交付物负担 / 数据来源 / 模型形式限制；写入 task_type、problem_shape、required_deliverables |
| 2 | 问题深度解析与分解 | `stage_02_analysis.md` | 2-3h | L1 | 每个 Task 一张卡片；数据体检与口径闸门 |
| 3 | 模型选型 | `stage_03_model_selection.md` | 2-4h | L1 + 反事实 | 满足 explicit_model_form；从简到繁 |
| 4 | Foundation（假设+符号+术语） | `stage_04_foundation.md` | 1h | L1 | Assumption + Justification；英文术语表 |
| 5 | **递归子问题循环** Task 1..n | `stage_05_subproblem_loop.md` | 按题目分配 | L1 + 子检查点 | 每个 Task 有数值结论 + 图 + 解读 |
| 6 | 灵敏度 / 稳健性 | `stage_06_robustness.md` | 2-3h | L1 + L2 | C 题加验证（时间序列 CV、预测区间） |
| 7 | 模型评价 + 推广 | `stage_07_evaluation.md` | 1-2h | L1 | Strengths & Weaknesses 具体到证据 |
| 8 | 英文论文 + Summary Sheet + letter/memo | `stage_08_writing.md` | 16-30h | L1 + L2 | 25 页预算、AI 披露链路、pdflatex 渲染 |
| 9 | 提交合规 + Panel | `stage_09_review.md` | 2-6h | L1 + L3 panel | `check_compliance.py` 无 FAIL；30-Second Judge |

---

## 加载协议（节省 token 的关键）

**只在进入阶段 N 时加载** `references/stage_NN_*.md`。**切勿**一次性全读。

- 每阶段开头：读 `<cwd>/state/decision_log.json`，**先读 `resume` 段**
- 每阶段结尾：写 decision_log（核心决策 + 5 维评分 + **`resume` 段**）。96 小时赛期里上下文必然被压缩多次，只有磁盘上的东西还在
- stage 1-9：`references/rubrics.md` 对应章节（L1 评分用）。**表格是生成物**——唯一数据源是 `config/rubric.json`，改判据改 JSON 再跑 `scripts/render_rubric.py --write`
- **stage 1**：`competitions/mcm/topic_specs.json` + `题型与算法对照.md`。写入 `task_type`（题号，只供评分权重）、**`problem_shape`（从题面判定，六选一）**、`problem_shape_modifiers`、**`problem_meta.required_deliverables` 与 `deliverable_specs`（逐字抄题面）**
- **stage 2**：有数据就跑 `scripts/scan_attachments.py`，再跑 `scripts/check_data_decisions.py` 过数据口径闸门（动数据必须有可追溯理由）
- **stage 3**：按 `problem_shape` 取 `题型与算法对照.md` §1 主线，再看 `references/model_catalog.md`
- **stage 5**：per-Task 评分后调 `scripts/score_artifact.py --mode aggregate_qi` 聚合；出图用 `figures/starter.py`，流程图用 `figures/flow_pptx.py`
- **stage 6**：`scripts/check_selfaudit.py` 必跑（中英文论文都能扫：自检承诺写了没执行、"Weaknesses" 其实是没做完的活）
- **stage 0 / 8 / 9**：`competitions/mcm/current_rules.md`
- **stage 8**：`competitions/mcm/{winning_patterns, abstract_template, Memo与Letter写法, paper_skeleton, phrase_bank}.md`；AI 披露 `scripts/render_ai_usage.py`；渲染 `scripts/render_paper.py`（报告解答页数）
- **stage 9**：先过 `scripts/check_compliance.py`（退出码非零不得提交），再跑 `check_numbers.py`、`check_selfaudit.py`、`check_figures.py`，最后 `anti_patterns.md` 与 `rubric_overlay.json` 的 panel personas
- 触发反馈时：`references/feedback_layer*.md`

---

## 收敛准则（三处一致）

| verdict | 触发 | 行为 |
|---------|------|------|
| `block` | issues 含 ≥1 high-severity | 暂停 skill，用户介入 |
| `pass_early` | raw_min ≥ 9 AND weighted_mean ≥ 9 | iter-1 早退 |
| `pass` | raw_min ≥ 7 AND weighted_mean ≥ 8 | 进下一阶段 |
| `pass_with_review` *(stage 5)* | 任 Task mark_for_review 但加权阈值满足 | 进 stage 6，L2 必读 review_qis |
| `refine` | 其他 | section-patch 精修，iter+=1（cap 3） |
| `refine_partial` *(stage 5)* | 任 Task.min < 7，其他已 pass | 仅 refine 该 Task |
| `carryover` | iter == 3 仍 refine | 进下一阶段，标记由 L2 处理 |

`weighted_mean` = Σ(s_i × w_i) / Σ(w_i)，权重来自 `config/dim_weights.json["mcm"][<task_type>]`（clamp [0.7, 1.5]）。
此定义在 `feedback_layer1_critic.md` / `rubrics.md` / `scripts/score_artifact.py` 三处必须**完全一致**。

---

## 状态持久化

`decision_log.json` v3.1 关键字段（与 `templates/shared/decision_log.json` 对齐）：
- root：`competition`（恒为 `mcm`）、`task_type`、`problem_shape`、`mode`、`current_stage`、`budget`、`events`、`compliance`
- `problem_meta`：`year`、`letter`、`title`、`deadline_iso`、**`required_deliverables`**、**`deliverable_specs`**
- `paper_metadata`：`mcm_control_number`、`problem`、`year`、`title`、`keywords`（渲染时 fail closed）
- `compliance.ai_usage`：AI 台账，显式 `[]` = 未使用
- stage_5 扩展：`qi_count`、`qi_weights`、`qi_status`

L2 跨阶段回检（stage 5/6/8 末尾）读这个文件主动找冲突，触发**定向回滚**：不重做整阶段，只针对冲突点。

---

## 上下文预算纪律

- L1 Critic 强制 JSON 输出，~500 token/次
- 精修策略：section-level patch（`scripts/extract_diff.py`）
- references/ 与 competitions/ **懒加载**，本 SKILL.md 主体 ≤ 6k tokens
- 阶段完成后，artifact 摘要 + 关键数据 + 路径写入 decision_log，不在上下文保留全文
- 只有 harness 提供可靠 usage 时才记录 token 消耗；不可观测时保留为 `null`
- 时间或上下文吃紧时，向用户建议降级模式，确认后写入 events

---

## 用户指令快捷

- "进入 stage N" / "重做 stage N" → 跳转
- "换成 B 题" → 改 `problem_meta.letter`、`task_type`、`problem_shape`、`required_deliverables`（重新抄题面）
- "升级到 championship" → 启用 L3 + L4 + red-team
- "切到 fast" → 关闭迭代
- "回退到 stage M" → 回退 current_stage 并清理 ≥M 节点
- "做 L2 回检" → 立即触发 cross-stage backtrack
- "看进度" → 输出 decision_log 摘要 + 当前评分
- "查合规" → 跑 `check_compliance.py` 并解释每个 FAIL

---

## 数据来源声明

- `competitions/mcm/empirical.json`：279 篇 O 奖论文（2018 年 10 篇、2019–2021 年 110 篇、2022 年 44 篇、2023 年 37 篇、2024 年 35 篇、2025 年 43 篇）。文字版用 pdftotext 抽取，扫描版用 MinerU 解析。论文原件不随 skill 分发。
- 规则：COMAP Rules/Instructions（2027）、Use of AI Tools in COMAP Contests（v102025）、Submission Walk Through（V20251232）、2026 年六道题题面。

## 外部资源

- 当届赛题、规则与结果：<https://www.contest.comap.com/undergraduate/contests/mcm/>
- 美赛 LaTeX 社区模板（仅供参考，未打包）：`QTH1225/LaTeX-in-ICM-MCM`（LPPL）、`mcmthesis`
