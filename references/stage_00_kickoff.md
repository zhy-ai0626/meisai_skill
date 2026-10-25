---
stage: 0
name: kickoff
duration_h: 1
inputs:
  - "user_inputs.{problem_status, team_size, deadline, control_number, pdf_paths}"
outputs:
  - "stage.0.{team_roles, tools_ready, problem_scan, time_budget_h, collab_protocol, checklist_completed}"
  - "root.{competition}"
  - "paper_metadata.{mcm_control_number, year}"
loads_reference:
  - "competitions/mcm/current_rules.md"
  - "competitions/mcm/topic_specs.json"
  - "competitions/mcm/README.md"
loads_template:
  - "templates/shared/decision_log.json"
  - "templates/shared/requirements.txt"
feedback: ["L1"]
next: "stage_01_problem_selection | wait_for_prompt"
---

# Stage 0 — 团队启动与资料预扫

**时长**: 1h | **反馈层**: L1 | **触发**: skill 首次启动 / 用户说"开始建模"

---

## 目标

在题目公布前（或公布后立即），把队伍状态调到"上手即可执行"，避免后续阶段因协作/工具/角色问题反复返工。

美赛的时间轴和国赛不同，先对齐（以 `current_rules.md` 当届核对结果为准）：

| 事件 | 美东时间 (EST) | 北京时间 |
|---|---|---|
| 赛题公布、开始 | 周四 17:00 | 周五 06:00 |
| 停止一切修改 | 周一 20:00 | 周二 09:00 |
| PDF 提交截止 | 周一 21:00 | 周二 10:00 |

**六道题同时公布，队伍自选一道**——所以 Stage 1 是真的"六选一"，不是国赛那种 ABC 里挑一道。

---

## 输入

- 用户提供: 队员数 (默认 3) / 截止时间 / 队伍控制号 (team control number，报名后 COMAP 发放的 7 位数) / 模式偏好
- (若题目已发布) 六道题的 PDF 路径与数据文件

## 产出

- `state/decision_log.json` 初始化，问题元信息与 `paper_metadata.mcm_control_number` 填好
- 角色分工表 (写入 `decision_log.stages.0.team_roles`)
- 工具就绪 checklist
- 六题预扫（题目已公布时）→ Stage 1 输入

---

## 操作流程

### Step 1: 元信息收集 (5 min) — 问答式

收集以下启动字段。先合并当前用户消息与已有 state，**只询问尚缺字段**；将缺失项合并成一轮问答（Claude Code: 单条 AskUserQuestion；Codex: 编号列表，见 `references/harness_compat.md` §1）：

1. **题目状态** — `1) 已公布，PDF 在 <路径>  2) 未公布  3) 已选定某题（A–F）`
2. **队员数与各人擅长** — 自由文本 (例: "3 人, 建模 / 编程 / 写作+英语")
3. **截止时间** — 自由文本（默认按 `current_rules.md` 的北京时间换算；ISO 字符串或 "距现在 X 小时"）
4. **队伍控制号** — 7 位数字；未拿到可先留空，Stage 8 渲染前必须补齐

**禁止**让用户手动编辑 decision_log.json；拿到答案后由 agent 自动写入：

- `decision_log.competition` ← `"mcm"`（本 skill 只有这一个取值）
- `decision_log.problem_meta.{year, deadline_iso, team_size}`、`paper_metadata.{mcm_control_number, year}`
- `decision_log.events.log` ← 题目 PDF 与数据路径

先读取 `competitions/mcm/current_rules.md`，再打开其中的官方来源复核当年规则；仓库内经验值不能覆盖 COMAP 当届通知与题面。Stage 0 不预加载 `winning_patterns.md`。

**自动推断**（加载 `competitions/mcm/README.md` 与 `topic_specs.json`）：
- 时长预算 96h；写作语言英文；LaTeX 编译器 pdflatex
- 题面未公布或尚未读取时，`problem_scan.subproblem_count` 与 `stages.5.qi_count` 保持 `null`；不得用历史题目猜默认子问数
- `task_type` 在 Stage 1 选定题号后再填（`topic_specs.json` 给出 `<letter> → task_type_key`）

### Step 2: 角色分工 (10 min)

确保以下三类职责都有明确主责与互备。队员少于三人时允许一人兼任：

| 角色 | 主责内容 | 互备 |
|------|---------|------|
| **建模主** | Stage 2/3/4/5 主导，数学公式 | 编程主 |
| **编程主** | Stage 5 求解、Stage 6 灵敏度、全部图表 | 建模主 |
| **写作主** | Stage 8 主导（英文写作 + Summary Sheet + letter/memo），Stage 1/9 协助 | 全员 |

美赛特有：**英文写作是独立的工作量**。写作主从 Day 2 起就要边做边写，不能等模型做完再"翻译"——
COMAP AI 政策规定翻译工具也要披露，整篇中译英后再交的成本比直接英文写高得多。

**反模式 J1**（`competitions/mcm/anti_patterns.md`）："人人都负责一切，实际无人主责" — 拒绝。

### Step 3: 工具就绪 checklist (15 min)

```bash
python --version           # ≥ 3.10

# skill 自检 + **真编译一次** smoke.tex。--require-renderer 使编译链失败以非零码退出。
python <skill>/scripts/doctor.py --workspace . --require-renderer

# 建模依赖（一次性安装见 templates/shared/requirements.txt）
python -c "import numpy, scipy, sklearn, matplotlib, pandas, statsmodels, SALib, pypdf"
```

**编译链是 Stage 0 的 block，不允许推迟到 Stage 9。** `doctor.py` 的 `latex-smoke` 会把
`templates/latex/mcm/smoke.tex`（Summary Sheet 页眉 + newtx 字体 + 公式 + 三线表 + 浮动体）
复制到临时目录**真的编译一次**。MiKTeX 首次编译会按需下载宏包，如果被拦截就在这里暴露，
而不是周一晚上。`latex-smoke` 失败时按 `doctor.py` 打印的修复顺序处理；**在它转绿之前不要进入 Stage 1**。
实在装不上 TeX，可退到 Overleaf 或 COMAP 官方 Word 模板，把决定写进 `decision_log.events.log`。

再裸跑一次绘图起手式，六段全出才算通（同时验证英文字体回退与灰度校样）：

```bash
python <skill>/figures/starter.py --out ./_figcheck
```

**目录初始化**（agent 自动执行，不要让用户敲命令）：
```bash
mkdir -p state results figures paper_workspace
cp <skill>/templates/shared/decision_log.json state/decision_log.json   # 仅当不存在时
```

| competition | LaTeX 模板 | 引擎 | 静态资料 |
|---|---|---|---|
| mcm | `<skill>/templates/latex/mcm/main.tex` | pdflatex | COMAP 当届规则 + O 奖论文实证分位（见 `competitions/mcm/README.md`） |

### Step 4: 六题预扫 (题目公布后，20 min)

用户提供题目 PDF 后，agent 读完**全部六道题的全文**（包括末尾的 "Your PDF solution ... should include" 段和 Glossary），对每道题输出：

```json
{
  "problem_id": "2027-B",
  "domain_keywords": ["<extracted keyword>"],
  "data_provided": "<数据文件名与规模；'无，需自行检索公开数据' 也是一种结论>",
  "tasks": ["<题面编号的每一项要求，原文短句>"],
  "required_deliverables": ["letter"],
  "deliverable_specs": [{"kind": "letter", "audience": "MCM Agency", "length": "one page"}],
  "model_form_constraints": "<题面对模型形式的硬要求，如 2026A 'continuous-time model'，没有写 none>",
  "primary_problem_type": "<inferred shape with evidence>",
  "estimated_difficulty": "<easy|medium|hard with rationale>"
}
```

**交付物要逐字抄题面**：2026 年 B 题要 one-page letter，C 题要 1–2 页 memo，A/F 只要标准件——
同一年六道题各不相同，漏一个就是没完成题目要求。写入 `decision_log.events.log`，作为 Stage 1 输入。

### Step 5: 时间预算分配 (10 min)

从真实 deadline 倒推并写入 `decision_log.stages.0.time_budget_h`。题面未公布时只记录 provisional 总预算：

- 最后 **8 小时**只做装配、Summary Sheet 定稿、合规检查和提交，不再改模型。北京时间周二 09:00 停止修改。
- 英文写作（含 Summary Sheet 与 letter/memo）至少占总预算的 25%，从 Day 2 起并行。
- 题面要求自行收集公开数据（`open_data_required`）时，数据检索与清洗单独列预算。
- 剩余时间不足时，列出会牺牲的验证或表达范围，让用户确认取舍。

### Step 6: 协作约定 (5 min)

写入 `decision_log.stages.0.notes`：命名规范、版本控制节奏、同步节奏（每次同步含阻断项和交接产物）、求助升级条件。
**作息**：96 小时跨四个夜晚，约定轮班睡眠，不要三人同时通宵到第三天崩掉。

---

## L1 Rubric (5 维 × 1-10)

<!-- RUBRIC:BEGIN 0 -->
| 维度 | 满分行为 (10) | 失败行为 (1) |
|------|-------------|-------------|
| 1. 角色分工明确性 (`1_role_clarity`) | 按实际人数覆盖建模/编程/写作责任，并设置互备 | 职责和交接人不明确 |
| 2. 工具就绪度 (`2_tools_ready`) | 题目需要的计算、写作、版本与沟通工具已验证 | 关键工具尚未试运行 |
| 3. 时间盒规划 (`3_time_planning`) | 按实际截止时间设置里程碑、关键路径和缓冲 | 无计划 |
| 4. 题目预扫信号 (`4_problem_scan`) | 已识别问题域 (优化/预测/评价等) | 未读题 |
| 5. 协作约定 (`5_collab_protocol`) | 命名规范、版本控制、daily standup 时间 | 无规范 |
<!-- RUBRIC:END 0 -->

参考 `rubrics.md` Stage 0 节。每维必须 ≥7 才通过。

## 常见坑 (anti_patterns)

- **J1**: 三人都全栈不深 → 强制角色主责
- **J2**: 选题摇摆（六道题都看着能做，到 Day 2 还在换题）
- **J3**: 英文写作留到最后 → time budget 把 Stage 8 提前到 Day 2

## 退出条件

1. `decision_log.stages.0.checklist_completed == true`
2. 团队角色明确，工具全员 ready，`latex-smoke` 为绿
3. (若题目已发布) 六题预扫完成，每题的 `required_deliverables` 已抄录
4. L1 rubric 全维 ≥7

分支：

- **题面已可读** → 跳转 `stage_01_problem_selection.md`。
- **题面未公布/不可读** → 写入 `current_stage=0` 与等待原因，停止内容生成并等待；恢复时从 Step 4 继续。

---

## 与 Stage 1 的衔接

仅在 Step 4 已完成时，把六题预扫 JSON 作为 Stage 1 的上下文输入，避免重新读题。没有题面时不得伪造预扫或进入选题。
