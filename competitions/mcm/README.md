# MCM/ICM 美赛特化层

| 字段 | 值 |
|------|-----|
| 竞赛代码 | `mcm`（覆盖 MCM A/B/C 与 ICM D/E/F） |
| 官方名 | Mathematical Contest in Modeling / Interdisciplinary Contest in Modeling（COMAP） |
| 时长 | 约 96 小时（美东周四 17:00 → 周一 20:00，北京时间周五 06:00 → 周二 09:00） |
| 队员 | ≤ 3 人 |
| 语言 | 英文 |
| LaTeX | `templates/latex/mcm/main.tex`（仓库原创，COMAP Summary Sheet 版式）+ pdflatex |
| 页数 | 整份解答 ≤ 25 页；Report on Use of AI 不计入 |
| 题号 | A 连续 / B 离散 / C 数据 / D 运筹与网络 / E 可持续 / F 政策 |
| 当前规则 | 2027 届说明 + AI 政策 v102025，见 `current_rules.md`（2026-10-26 核对） |
| 实证语料 | 279 篇 O 奖论文（2018–2025，每年按官方名单核对），统计结果在 `empirical.json` |

## 文件清单

| 文件 | 用途 | 加载阶段 |
|------|------|---------|
| `current_rules.md` | 规则基线、时间表、AI 政策、题面层面的交付物要求 | Stage 0 必读；Stage 9 逐条核 |
| `topic_specs.json` | 题号 → task_type、近年真题、各题号常见方法 | Stage 1 |
| `winning_patterns.md` | **运行时主入口**：各 Stage 的正面做法与实证数字 | 各 Stage 按需 |
| `题型与算法对照.md` | 六种 problem_shape 的判据、方法主线、各题号方法分布 | Stage 1/3 |
| `anti_patterns.md` | A–J 通用 + M 组美赛特有失分点，每条有出处 | Stage 3、Stage 9 |
| `abstract_template.md` | Summary Sheet 写法与模板 | Stage 8 |
| `Memo与Letter写法.md` | 题面要求的 letter/memo 怎么写 | Stage 1 抄要求、Stage 8 写 |
| `paper_skeleton.md` | 论文骨架 ↔ `paper_workspace/` 节文件 ↔ 25 页预算 | Stage 8 |
| `phrase_bank.md` | 英文句式库（含 O 奖 Summary 高频句式） | Stage 8 |
| `静默陷阱.md` | 不报错只出错的数据/建模/提交陷阱 | Stage 0/5/6/9 |
| `rubric_overlay.json` | panel personas 与资源路径 | Stage 9 |
| `empirical.json` | O 奖论文观察分位（页数、图表、参考文献、Summary 词数、章节出现率、方法出现率） | L1 critic 取锚点；`check_figures.py` |

## 实证语料

| 年份 | 篇数 | 来源 |
|---|---|---|
| 2018 | 10 | 本地资料（2018 B–F 英文全文） |
| 2019–2021 | 110 | GitHub `Jackksonns/MCM-ICM-Outstanding-Papers`（MIT） |
| 2022 | 44 | 本地资料 |
| 2023 | 37 | 本地资料（扫描版，MinerU 解析） |
| 2024 | 35 | 本地资料 |
| 2025 | 43 | 本地 8 篇（文字版）+ GitHub 35 篇（扫描版，MinerU 解析） |

- 2022–2025 年每篇都与 COMAP 官方结果页的 Outstanding 名单核对过控制号与题号。
- **论文 PDF 不随 skill 分发**（版权属于 COMAP 与作者），仓库只含统计结果与短引文。
- 统计脚本 `scripts/build_empirical.py`，口径写在 `empirical.json` 的 `_method` 字段。

## 可信度边界

- 分位数只用于"这篇是不是明显异常"的提示，**不是评分线，也不预测获奖**。
- 语料只有 O 奖论文、没有对照组：能说"O 奖论文长什么样"，不能说"这样做就能拿 O"。
- 关键词/标题匹配会漏掉非常规写法，各种"出现率"**偏低估**。
- 2023 年扫描件有水印遮挡，个别词句残缺；结构类统计不受影响。
- 逐题 Judges' Commentary 需 Mathmodels.org 会员权限，未纳入。
- **2026 年 O 奖论文未纳入**：官方名单（41 篇：A 6 / B 6 / C 19 / D 3 / E 3 / F 4，不含 Finalist）已于 2026-10-27 从 COMAP 结果页抄录，但全文只在 Mathmodels.org（会员）发布，截至该日 GitHub 上的常见合集仍止于 2025。

## 与 references/ 通用层的关系

- `references/stage_NN_*.md` 按 `decision_log.competition`（恒为 `mcm`）加载本目录文件
- `references/model_catalog.md` 是通用模型清单
- 反馈层 `references/feedback_layer*.md` 通用；L1 critic 需要经验锚点时读 `empirical.json`
