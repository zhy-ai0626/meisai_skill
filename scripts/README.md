# Scripts 工具说明

这里的脚本分为两组：比赛过程中使用的运行时工具，以及维护资料库时才使用的离线工具。下列命令均假设当前目录是 skill 根目录；用户项目中的动态文件统一放在项目工作目录，不写回 skill。

## 运行时工具

### `doctor.py` — 环境与包结构预检

在启动工作流前运行。默认同时检查 skill 结构、美赛竞赛包、JSON 配置、本地渲染工具（**真编译一次** `templates/latex/mcm/smoke.tex`）、绘图样式与提交门；`--skip-tools` 适合 CI 或只做静态检查。

```bash
python scripts/doctor.py --workspace /path/to/project
python scripts/doctor.py --skip-tools --json
python scripts/doctor.py --require-renderer --require-modeling
```

### `render_rubric.py` — rubric 单一数据源的生成与漂移检查

**`config/rubric.json` 是 L1 rubric 的唯一数据源。** md 里的 22 处表格由本脚本生成，`score_artifact.py` 的 `DIM_WHITELIST` 也从同一份 JSON 加载。

重构前这份 rubric 散在**四处**、无人核对：`references/rubrics.md`（声明为 canonical）、各 `stage_0N_*.md` 里的平行副本（agent 运行时真正读的）、`score_artifact.py` 的硬编码白名单、`config/dim_weights.json` 的加权键。逐份抽出来比对的实测结果：

- **stage 1 / 3 / 6 / 7 的维度名两边完全不同**——「命名准确性」vs「模型命名真实性」、「局限真实」vs「缺点真实」。键相同，所以**既有的每一项检查都查不出来**：Critic 照 stage 文件打分，评的却是和 canonical 表描述不同的东西；
- **stage 5 的 stage-level 五维、stage 9 的五维在 `rubrics.md` 里干脆没有表**（前者只有两条散文、后者只写了 L3 panel），白名单有键、没有满分行为，Critic 只能自己编判据；
- stage 4「假设支撑」在 stage 文件里只剩断句「**每条必须有**」，完整判据在 rubrics.md。

所以定稿不是机械二选一：以 stage 文件为基底，**逐条与 rubrics.md 旧版比对后合并了 14 处**。生成的每一行都同时印中文名和 `` `dim_key` ``——Critic 输出的是英文键、人读的是中文名，两者印在同一行才不会再出现"名字对不上键"。

```bash
python scripts/render_rubric.py --check      # doctor 的 rubric-sync 项就是它
python scripts/render_rubric.py --diff       # 只看差异
python scripts/render_rubric.py --write      # 按 JSON 重写全部表格
python scripts/render_rubric.py --whitelist  # 打印维度键白名单
```

**改判据改 JSON，不要手改 md 表格**——手改会被 `--check` 报出来。加载失败时 `score_artifact.py` 直接抛异常，**不回落到硬编码副本**：静默用一份过期白名单，会让"键校验通过"变得毫无意义。

`dims[].fail_marks` 是可选的 1 分锚点（只有 stage 0 原表带这一列），任一维有它就渲染成三列。想给别的 stage 补两端锚点，加这个字段即可。

L1 架构**固定 5 维**：要加判据请折进已有维度，不要加第 6 行——多一维的后果是二选一且两个都坏（Critic 真产出第 6 个键 → 校验 FAIL；只产出 5 个 → 新判据永远不被打分）。`tests/test_rubric_consistency.py` 里有一条专门测**漂移检测器不是空转**：故意改一个字，`--check` 必须报出来。

### `score_artifact.py` — L1 Critic 结果处理

校验 critique JSON、计算实际 verdict，并把阶段分数与迭代记录写入项目的 `state/decision_log.json`。

```bash
python scripts/score_artifact.py \
  --stage 5 \
  --critique /path/to/project/state/critique_v0.json \
  --decision-log /path/to/project/state/decision_log.json
```

不传 `--decision-log` 时，脚本按 `MATHMODEL_STATE_DIR`、最后 `<cwd>/state/decision_log.json` 的顺序解析路径。

所有子问完成后，可聚合 per-Qi 结果并把 `qi_status`、`review_qis`、`refine_qis` 与最终 verdict 原子写回 Stage 5：

```bash
python scripts/score_artifact.py \
  --mode aggregate_qi \
  --qi-results /path/to/project/state/qi_results.json \
  --decision-log /path/to/project/state/decision_log.json
```

### `extract_diff.py` — 定向修补辅助器

根据 Critic 指出的问题生成 section patch prompt，或应用已经生成的 section patch / unified diff。它的价值是缩小修改范围并保留已通过章节；实际节省量取决于论文和修补范围，不设固定比例。

```bash
# 生成定向修补 prompt
python scripts/extract_diff.py \
  --artifact /path/to/project/paper_workspace/06_models.md \
  --critique /path/to/project/state/critique_v0.json \
  --mode section \
  --output /path/to/project/state/refine_prompt.md

# 应用模型返回的 patch；--apply 模式不需要 --critique
python scripts/extract_diff.py \
  --artifact /path/to/project/paper_workspace/06_models.md \
  --apply /path/to/project/state/refine_patch.md \
  --mode section \
  > /path/to/project/paper_workspace/06_models_v1.md
```

### `render_paper.py` — Markdown 章节装配与 LaTeX 编译

把 `paper_workspace/` 中的编号 Markdown 章节装入 `templates/latex/mcm/main.tex`（仓库原创，COMAP Summary Sheet 版式），用 Pandoc 转换、pdflatex 三编。必需章节 `01`–`08`、`10`、`11` 缺失或为空、marker 缺失/重复/未知时停止；`09_memo_letter.md` 与 `12_ai_use_report.md` 是可选块，存在才渲染。内置简化转换器只用于 `--no-compile` 结构预检。

正式渲染检查提交元数据：控制号（7 位数字）、题号（A–F）、年份、题目、关键词。CLI 参数优先于 `decision_log.paper_metadata`；`1111111`、`ABCDEF`、`TITLE OF YOUR PAPER`、`keyword1` 等占位值会阻断编译。只有显式组合 `--allow-placeholders --no-compile` 才生成带醒目标记的结构预览。

编译后报告三个数：PDF 总页数、**计入 25 页上限的解答页数**（从 `main.aux` 里 `MathmodelSolutionEnd` 标签的页码读出，不含 Report on Use of AI；超 25 页返回失败）、TeX 报错条数。

```bash
python scripts/render_paper.py \
  --workspace /path/to/project/paper_workspace \
  --decision-log /path/to/project/state/decision_log.json \
  --output-dir /path/to/project/paper_output

# 只检查模板装配，不编译 PDF
python scripts/render_paper.py --workspace paper_workspace --no-compile --allow-placeholders
```

### `render_ai_usage.py` — Report on Use of AI 生成

从 `decision_log.compliance.ai_usage` 生成 COMAP AI 政策（v102025）要求的披露材料：`paper_workspace/12_ai_use_report.md`（25 页之后的 Report on Use of AI，模板提供标题）与 `paper_workspace/ai_tool_references.md`（每个工具一条参考文献，粘进 `10_references.md`）。显式 `[]` 表示未使用：不生成报告并删除旧文件，提交表单 AI uses statement 选 No。无第三方依赖。

```bash
python scripts/render_ai_usage.py \
  --decision-log /path/to/project/state/decision_log.json \
  --paper-workspace /path/to/project/paper_workspace
```

每条记录必须含 `tool`、`model`、`version`、`use_stage`、`purpose`、`paper_sections`、`human_review`，并完整记录 `query` + `output`，或为翻译/代码补全等非对话式工具提供 `disclosure`。缺失或 `null` 会报错。

### `check_numbers.py` — 数值可追溯性

论文里的数字大多是从终端手抄进 LaTeX 的，抄错一位不报错、评委却能核出来。这个脚本把论文里的每个数值拿去 `results/` 下的 `.json`/`.csv` 里找同一个值，报出找不到的那些。单向检查：结果文件里有而论文没用到的值不算问题。

```bash
python scripts/check_numbers.py --paper paper.tex --results results/
```

### `scan_attachments.py` — 数据结构体检（Stage 1/2 有数据就必跑）

分两组检查。**第一组决定方法主线**——题型判据里有几条依赖附件的结构性事实，读题面看不出来，而看漏的代价是整条路线错：一组列之和是否为（近似）常数（→ 成分数据，必须 CLR）、同一对象是否有多条记录（→ 观测不独立）、名字像标签的列是否只有一个取值（→ 真标签在别处，监督学习会退化成零正例且不报错）、是否有 Excel 合并单元格残留（→ 分组前必须 ffill）。

**第二组是 `静默陷阱.md` §四那四条**——路线对了但数字错，比第一组更难自己发现：

| kind | 扫什么 | 不扫会怎样 |
|---|---|---|
| `mixed_dtype` | 同一列混了 number / string / datetime；文本列里大部分能当数读；`11w+6` 这类复合写法 | `to_numeric(errors="coerce")` 把转不了的**静默变 NaN**，行数不变、分布悄悄改了 |
| `edge_row_text` | 多列的文本值集中在表格头部或末 1~2 行 | 表头埋行 / 末行注释被当成数据；列名全错也不报错 |
| `case_collision` | 规范化（首尾空白 → 大小写 → NFKC 全角）后取值数变少 | 同一类被 `groupby` 切成两组，正则不加 `re.I` 静默丢行 |
| `derived_mismatch` | 自报的"时长"列与两个日期列之差对不上 | 两列都能用，**选哪一列当准会改变结果** |
| `identity_collinear` | 原始与 log 空间的 VIF > 100 | 恒等式变量同时入模，回归系数符号可以整个翻过来 |

```bash
python scripts/scan_attachments.py <附件目录或文件>
python scripts/scan_attachments.py 附件1.xlsx --json
```

**这是体检不是门**，有发现也退出 0。但 `compositional` 与 `repeated_measures` 两类会改变方法主线，必须写进 `decision_log.problem_shape_modifiers`；第二组的结论写进 `decision_log.stages.2.data_schema.silent_traps`，处理决定走 `stage_02_analysis.md` Step 4b 的闸门。

第一组实测：2021B 六个"选择性"列之和恒为 100.0000（114 行无一例外）；2022C 化学成分和集中在 100 附近但范围 71.89~100（题面自己给了 85%~105% 的有效区间）；2025C 女胎表『胎儿是否健康』605 行全是"是"，真标签在『染色体的非整倍体』列。

第二组实测（2021–2025 全部附件跑过一遍）：

- 2025C `检测日期` 是 686 行整数 `20230429` + 396 行真 datetime，`末次月经` 是 674 行 datetime + 396 行字符串——整列 dtype 因此是 object，**`pd.to_datetime` 对整数按"距 epoch 多少纳秒"解释，把 20230429 变成 1970 年且不报错**；
- 2025C `检测孕周` 与「检测日期 − 末次月经」相关 0.96，但只有 **38.8%** 的行吻合到 ±0.15 周（女胎表更低，2.7%）；
- 2025C `检测孕周` 里混了一个大写 `16W+1`；`体重 / 孕妇BMI / 身高` VIF 分别 359 / 223 / 109；
- **2024C `作物名称` 里有一个 `'生菜 '` 带尾随空格**（42 个取值实际只有 41 种作物），直接 `groupby` 会把生菜切成两种；
- 2021 「附件A 订购方案数据结果」是填写模板，前 4 行是"请不要修改表格中已有的任何信息"之类的说明、真表头在第 5 行；
- 2021 `基准态时上/下端点 X/Y/Z 坐标` 六列 VIF 到 10⁷（同一根促动器的两端共线）。

为避免刷屏，同类发现超过 5 条会折叠成一条并提示"整表读法有问题"；宽矩阵（>25 个数值列，如 2021「近5年402家供应商」的 242 列企业×月份表）不做 VIF——列本身是同一个量的不同时点，高相关是形态而非恒等式。已被 `compositional` 报过的列组也不重复报 VIF。

回归测试在 `tests/test_data_scan.py`，每条检查都成对写了**该命中**和**不该误报**两个方向——按 `静默陷阱.md` 末节那条"自检只覆盖它真正测过的那一维"。检查项自身抛异常会报 `check_error` 而不是静默跳过：**跳过一项检查和这项检查通过，在输出上长得一模一样**。

### `check_selfaudit.py` — 自检承诺与局限的了结检查（Stage 6 与 Stage 9 强制项）

针对本 skill 演练里重复次数最多的失效模式：**写了自检却没执行**，以及**把本来就该做掉的活写成了"局限"**。脚本扫论文里的三类句子——自检承诺、局限（含整个「局限」小节）、自陈取常数/文献值——每一类都必须在 `state/self_audit.json` 台账里被了结，否则 FAIL。

台账条目用 `source_quote` 引用它所了结的那句原文，匹配靠子串包含，不做模糊匹配。**承诺写在论文里而台账没有也算 FAIL**：只查台账等于自己查自己，而演练里栽掉的恰恰是"承诺只写在散文里"。

```bash
# 首次：扫出待办生成台账骨架
python scripts/check_selfaudit.py --paper paper.tex --workspace paper_workspace/ \
    --scaffold > state/self_audit.json

python scripts/check_selfaudit.py --ledger state/self_audit.json \
    --paper paper.tex --workspace paper_workspace/ --results results/
```

模板与字段含义见 `templates/shared/self_audit.json`。退出码 1 = 有未了结项，2 = 没跑成。

### `check_data_decisions.py` — 数据口径闸门（Stage 2 强制项）

`题型与算法对照.md` §四第一步那条判据——**这一步是统计习惯，还是领域方法的组成部分**——此前只是散文清单，于是"忘了填"和"这题不需要填"在状态文件里长得一模一样。这个门把它变成一条命令。

**它双向查，因为这条教条两个方向都栽过：**

| 方向 | 现象 | 判定 |
|---|---|---|
| Z3 | 动了数据却把 `nature` 写成"统计习惯" | **FAIL** |
| Z18 | 全问全 `keep_as_is`，连领域质控也不考虑 | **WARN**（附 2025C 实测数字） |

Z18 只能是 WARN：**多数题目全 `keep_as_is` 是正确答案**（2025C 问题 1–3、绝大多数 A/B 题）。判成 FAIL 会逼人为了过门去动数据，正好掉进 Z3。这是设计决定，`tests/test_gates.py` 有测试钉住。

其余 FAIL：有附件数据却没填决策、缺 Qi 的键、`action` 不在枚举、`rationale` 是套话、`rationale` 没有可追溯出处、`data_schema.silent_traps` 缺失。`rationale` 的判据是**有没有出处，不是写得长不长**——「题面 85%~105% 为有效数据」只有 12 个字但依据完整，「按 3σ 剔除极值」同样短却一个出处都没有。

```bash
# 首次：从数据体检报告生成骨架（骨架的 action=TODO 故意不合法，过不了门）
python scripts/scan_attachments.py 附件/ --json > state/scan.json
python scripts/check_data_decisions.py --decision-log state/decision_log.json \
    --scan state/scan.json --scaffold > state/preproc.json

# 过门；给了 --scan 会顺便对账"体检报了却没给决定的列"
python scripts/check_data_decisions.py --decision-log state/decision_log.json \
    --scan state/scan.json
```

退出码 1 = 有 FAIL，**Stage 2 不得退出**；2 = 没跑成。

### `check_figures.py` — 图表交付体检（Stage 8/9）

`empirical.json` 里存着 279 篇 O 奖论文的图表数量分位（图中位约 14、表约 5）——但没人去数；交叉引用也一直靠眼看。

**FAIL 两类，都是评委看得见的**：`\includegraphics` 指向的文件不存在（LaTeX 缺图不一定报错，有的引擎只在图位置留个方框，PDF 照样出）、`\ref` 没有对应 `\label`（PDF 里印成 `??`）、`\label` 重复定义（编号看着对、指向是错的）。

**WARN 三类**：图/表数低于 O 奖 p25、`figures/` 里有图没被引用、有 label 但正文从未引用它。

**数量绝不判 FAIL。** 仓库一贯立场是"经验值不能当官方评分线"（`stage_08_writing.md` 明写 Do not treat empirical distributions as official rules）。图少不违规——把它做成硬门会逼人凑图（2025F 有 O 奖论文只有 2 张图）。同样有测试钉住：一张图都没有也不许让退出码变 1。

```bash
python scripts/check_figures.py --paper paper.tex --figures figures/ --topic A
python scripts/check_figures.py --workspace paper_workspace/ --figures figures/ --json
```

`--topic A|B|C|D|E|F` 用该题号的分位，不给用全体分位。注释掉的 `\includegraphics` 不计数（否则改稿后计数照旧，检查就开始骗人）；`\%` 转义百分号不当注释起点；`_gray.png` 灰度校样不算漏用。

### `check_compliance.py` — 提交前合规自查（Stage 9 强制项）

把 COMAP 规则里能机器判定的部分变成一条命令：PDF < 25 MB、文件名 = 控制号、第 1 页是 Summary Sheet、Summary 未溢出、每页页眉控制号与页码、**解答 ≤ 25 页**（以 Report on Use of AI 所在页为界）、正文字号 ≥ 12pt、全英文、目录与参考文献、题面交付物（letter/memo/policy brief/report）、用了 AI 则有 AI 报告且工具列入参考文献、身份字段与机构名、PDF 元数据、`??` 与模板占位符。控制号、交付物、AI 台账默认从 `state/decision_log.json` 读。

```bash
python scripts/check_compliance.py --paper paper_output/2712345.pdf
python scripts/check_compliance.py --paper 2712345.pdf --require letter --json
```

退出码 1 表示有 FAIL，不得提交（WARN 与人工项不影响退出码）；2 表示没跑成（文件不存在、缺 pypdf）。`--json` 里的 `compliance_checks` 可直接写进 Stage 9，其中 `null` 表示该项没测到，必须人工确认后改成布尔值。在真实 O 奖论文上实测：除分发方水印带来的中文字符外，其余项均通过。

## 离线维护工具

### `build_empirical.py` — 从 O 奖论文统计 `empirical.json`

输入一个语料目录：`<cid>.txt`（pdftotext 输出）或 `<cid>.md`（MinerU 解析的扫描版），加 `_index*.json`（`cid / year / problem / src`）。输出页数、图表数、参考文献数、Summary 词数与数字个数、章节出现率、方法出现率的分位，按题号与年份分层。

```bash
python scripts/build_empirical.py --corpus /path/to/corpus --out competitions/mcm/empirical.json
python scripts/build_empirical.py --corpus /path/to/corpus --dump-summaries summaries.jsonl
```

**论文原件不进仓库**（版权属于 COMAP 与作者）。语料的获奖身份要先对照 COMAP 官方结果页核对，再更新 `competitions/mcm/README.md` 的样本表。解析扫描版 PDF 时用到的 API token 只放环境变量。

## 路径协议

| 类型 | 位置 | 覆盖方式 |
|---|---|---|
| skill 静态资源 | `<skill>/{references,templates,scripts,competitions}` | 不覆盖 |
| 项目状态 | `<project>/state/decision_log.json` | `--decision-log` 或 `MATHMODEL_STATE_DIR` |
| 项目产物 | `<project>/{results,figures,paper_workspace,paper_output}` | 通过各脚本参数指定 |

`<cwd>` 只是命令启动时的当前目录，不是一个应当原样创建的文件夹名。

## 测试 fixture

Critic schema 样本位于 `tests/fixtures/`：

- `test_critique_good.json`：有效的 stage-level critique。
- `test_critique_bad_keys.json`：包含不在白名单中的维度键，预期校验失败。

在临时项目目录运行写入型示例，避免修改仓库内的模板状态：

```bash
python scripts/score_artifact.py \
  --stage 1 \
  --critique tests/fixtures/test_critique_good.json \
  --decision-log /tmp/mcm-test/state/decision_log.json
```
