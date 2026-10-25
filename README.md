# meisai_skill — 美赛 MCM/ICM 工作流 Skill

> 面向美国大学生数学建模竞赛（COMAP MCM/ICM）A–F 题的 Agent Skill。把 96 小时的建模比赛组织成 10 个可恢复、可检查的阶段，
> 从六选一选题到 25 页合规提交，并用 279 篇 O 奖论文的统计作为参照。

[![License](https://img.shields.io/badge/license-MIT-22c55e)](./LICENSE)
[![Contest](https://img.shields.io/badge/MCM%2FICM-A--F-f97316)](./competitions/mcm/)
[![Rules](https://img.shields.io/badge/COMAP%20rules-2027%20baseline-6f42c1)](./competitions/mcm/current_rules.md)

支持 **Claude Code** 与 **Codex**。工作流骨架来自国赛版 [`zhy-ai0626/shumoskill`](https://github.com/zhy-ai0626/shumoskill)（上游 [`handsomeZR-netizen/mathmodel-skill`](https://github.com/handsomeZR-netizen/mathmodel-skill)，MIT）；本仓库把竞赛层整体换成了美赛。

---

## 它解决什么问题

美赛很少因为"不够聪明"而失分，更常见的是：

- 漏交题面要求的 letter / memo（2026 年六道题里四道要，读者和篇幅各不相同）
- 附录代码把解答撑过 25 页；或者为塞下内容把字号缩到 12pt 以下
- 用了 AI（包括翻译工具）却没写 Report on Use of AI
- Summary 在复述题目，没有一个数值结论
- C 题拿随机 K 折验证时间序列，准确率虚高
- 第三问换了口径，前两问的数字悄悄对不上了

这个 skill 把这些隐含的依赖显式化：一份 `decision_log.json` 保存全部决策与口径，每个阶段有 rubric 自评与跨阶段回检，提交前有机器能判的合规门。

## 美赛特化了什么

| 方面 | 内容 |
|---|---|
| **规则基线** | `competitions/mcm/current_rules.md`：2027 届说明（2026-10-26 核对）、北京时间时间表、25 页覆盖范围、AI 政策 v102025、2026 年六题的交付物差异 |
| **选题** | 六选一对比矩阵；逐题抄录交付物与模型形式限制；按题面判定六种题型（不按题号） |
| **实证层** | 279 篇 O 奖论文（2018–2025，逐年对照官方 Outstanding 名单）：页数、图表数、Summary 词数与数字、章节出现率、各题号方法分布 → `empirical.json`、`题型与算法对照.md` |
| **写作** | Summary Sheet 写法（`abstract_template.md`）、letter/memo 写法、论文骨架与 25 页预算、英文句式库 |
| **反模式** | A–J 通用 + **M 组 18 条美赛特有失分点**，每条标出可公开核对的出处 |
| **LaTeX** | 原创模板：COMAP Summary Sheet 版式、每页 `Team # / Page N of M`、目录、可选 letter/memo 与 AI 报告块；渲染时报告**解答页数**（不含 AI 报告） |
| **合规门** | `check_compliance.py`：Summary Sheet、25 页、12pt、页眉控制号、英文、匿名、交付物、AI 报告、文件名与大小 |
| **AI 披露** | `render_ai_usage.py` 按 COMAP 格式生成 Report on Use of AI 与参考文献条目 |
| **图表** | 英文样式（与 Times 正文一致、灰度可读）、六段绘图起手式、可编辑 pptx 流程图 |

## 10 个阶段

| # | 阶段 | 美赛要点 |
|---|---|---|
| 0 | 团队启动 + 六题预扫 | 北京时间截止、控制号、编译链 smoke、逐题抄交付物 |
| 1 | 选题（六选一） | 交付物负担 / 数据来源 / 模型形式限制 |
| 2 | 问题分解 | Task 卡片、数据体检、数据口径闸门 |
| 3 | 模型选型 | 按题型取主线，满足题面硬约束 |
| 4 | 假设与符号 | Assumption + Justification、英文术语表 |
| 5 | 逐 Task 求解 | 数值结论 + 图 + 解读，恒等式自查 |
| 6 | 灵敏度 / 稳健性 | 自检承诺与 Weaknesses 的了结检查 |
| 7 | 模型评价 | Strengths & Weaknesses 具体到证据 |
| 8 | 英文论文装配 | Summary Sheet、letter/memo、AI 披露、pdflatex 渲染 |
| 9 | 提交终审 | 合规门 → 反模式 → 五视角 panel |

## Quick Start

```bash
# Claude Code
git clone https://github.com/zhy-ai0626/meisai_skill ~/.claude/skills/mcm-icm
pip install -r ~/.claude/skills/mcm-icm/templates/shared/requirements.txt
python ~/.claude/skills/mcm-icm/scripts/doctor.py --require-renderer

# Codex
git clone https://github.com/zhy-ai0626/meisai_skill ~/.agents/skills/mcm-icm
```

需要 Python ≥ 3.10、Pandoc、TeX 发行版（MiKTeX 或 TeX Live，含 newtx）。在比赛目录里启动 Claude Code，说：

```
开始美赛建模。六道题在 problems/ 下，我们 3 人……控制号 27xxxxx。
```

不装 skill 也能用：`kit/2_提示词模板.md` 有按阶段的独立提示词；`kit/0_开赛操作手册.md` 是开赛当天的完整命令清单。

## 目录

```
meisai_skill/
├── SKILL.md                    # 入口：触发边界、加载协议、收敛准则
├── references/                 # 10 个阶段文档 + 4 层反馈 + rubric
├── competitions/mcm/           # 美赛特化层（规则、实证、写作指南、反模式）
├── config/                     # rubric.json（唯一数据源）、dim_weights.json
├── scripts/                    # 渲染、AI 披露、合规门、数值/图表/自检门、doctor、语料统计
├── templates/latex/mcm/        # main.tex + smoke.tex
├── templates/shared/           # decision_log.json、AI 台账、代码起手式
├── figures/                    # mcm_style.py、starter.py、flow_pptx.py
├── code-templates/             # 30 个算法模板 + 12 个 playbook（Lupynow，MIT）
├── kit/                        # 开赛手册、提示词模板、算法讲解手册
└── tests/
```

用户项目里的产物（`state/`、`results/`、`figures/`、`paper_workspace/`、`paper_output/`）都在比赛工作目录，不写回 skill。

## 边界与可信度

- **COMAP 当届说明与当届题面永远优先**。规则每年可能变，Stage 0 必须重新核对。
- 实证数字是"O 奖论文长什么样"的观察，**不是评分线，不预测获奖**；没有对照组，不能推出因果。
- O 奖论文原件、COMAP 题面与模板**不随仓库分发**（版权属于 COMAP 与作者）。
- 逐题 Judges' Commentary 需要 Mathmodels.org 会员权限，未纳入。
- 用这个 skill 就是在用 AI：按 COMAP 政策如实记录并披露。

## 验证

```bash
python -m unittest discover -s tests -p "test_*.py"
python scripts/doctor.py --skip-tools
python scripts/render_rubric.py --diff
```

## License

MIT（见 `LICENSE`）。第三方来源与边界见 `THIRD_PARTY_NOTICES.md`。
