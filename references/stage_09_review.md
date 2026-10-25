---
stage: 9
name: review
duration_h: 2-6
inputs: ["paper_output/main.pdf", "paper_workspace/*.md", "decision_log_full"]
outputs:
  - "stage.9.{anti_patterns_check, compliance_checks, panel_scores, weakest_section, redo_log, red_team_record, final_pdf_path, submission_ready}"
loads_reference:
  - "competitions/mcm/current_rules.md"
  - "competitions/mcm/anti_patterns.md"
  - "competitions/mcm/rubric_overlay.json"
  - "references/feedback_layer3_panel.md"
loads_template: ["templates/latex/mcm/"]
feedback: ["L1", "L3_panel", "red_team_in_championship"]
next: SUBMIT
---

# Stage 9 — 提交终审

顺序：**合规第一，内容一致性第二，呈现第三**。排版再漂亮，违反当届规则就不能交。

**时间线**：北京时间周二 09:00 停止一切修改（2027 届，以 `current_rules.md` 为准）。Stage 9 至少在此前 6 小时开始。

## 1. 重新打开官方规则

读 `competitions/mcm/current_rules.md`，打开其中的 COMAP 链接核对当届版本，结果写进 `decision_log.stages.9.compliance_checks`。

**先跑脚本，再人工核**：

```bash
cp paper_output/main.pdf paper_output/<control number>.pdf
python <skill>/scripts/check_compliance.py --paper paper_output/<control number>.pdf
```

它从 `state/decision_log.json` 读控制号、`required_deliverables` 与 AI 台账，查：

| 项 | 级别 |
|---|---|
| PDF < 25 MB；文件名 = 控制号.pdf | FAIL |
| 第 1 页是 Summary Sheet（Problem Chosen / Control Number / Summary） | FAIL |
| Summary 没溢出到第 2 页、第 1 页没混进目录/Introduction | FAIL / WARN |
| 每页页眉有控制号；第 2 页起有页码 | FAIL / WARN |
| **解答 ≤ 25 页**（以 "Report on Use of AI" 所在页为界） | FAIL |
| 正文字号 ≥ 12pt | FAIL |
| 全英文（中文字符残留） | FAIL（>20 字）/ WARN |
| 有目录；有参考文献 | WARN / FAIL |
| 题面交付物（letter / memo / policy brief / report）在 25 页内 | FAIL |
| 用了 AI → 有 Report on Use of AI；AI 工具列进参考文献 | FAIL / WARN |
| 无队员/导师身份字段；正文无机构名；PDF 元数据无作者 | FAIL / WARN / FAIL |
| 无 `??`；无模板占位符 | WARN / FAIL |

退出码非零就是有 FAIL，**不得提交**。`--json` 输出里的 `compliance_checks` 可直接写进 decision_log；
其中 `null` 表示没测到，必须人工确认后改成布尔值。脚本末尾列出的人工项逐条确认（Summary 质量、letter/memo 读者、图表单位、非自制图片出处、AI 生成的引用是否核对过）。

任何未解决的规则违反：`submission_ready=false`，verdict `block`。

## 2. 反模式清单

逐条过 `competitions/mcm/anti_patterns.md`（条目数以 `doctor.py` 报告为准，不要抄记忆里的数）。重点是 **M 组**（美赛特有）与 A 组（Summary）。高危命中必须修；接受的中危项写明理由。

## 3. 证据链核对

```bash
# 论文里的数字都能在 results/ 找到
python <skill>/scripts/check_numbers.py --paper paper_output/main.tex --results results/

# 自检承诺与 Weaknesses 全部了结（Stage 8 改写可能新增承诺句或让引用失配，所以再跑一次）
python <skill>/scripts/check_selfaudit.py --ledger state/self_audit.json \
    --paper paper_output/main.tex --workspace paper_workspace/ --results results/

# 图文件与交叉引用
python <skill>/scripts/check_figures.py --workspace paper_workspace/ --figures figures/ --topic <A-F>
```

- `check_numbers.py`：论文数字多半是手抄的，抄错一位不报错，评委能核出来
- `check_figures.py`：FAIL = 缺图文件、`\ref` 无 `\label`、`\label` 重复；WARN = 图表数量低于 O 奖 p25（**经验分布不是规则**）、有图未引用
- 另外人工确认：被放弃的模型没有残留在 Summary/Conclusion；符号含义前后一致；外部论断都有来源

## 4. 呈现

- 最终 PDF 尺寸下标签、单位、图例、公式、图题都可读；灰度下系列可区分
- 表格单位与精度一致
- 没有 `??`、缺字方框、被裁切的图、大面积 overfull box
- 所有节都在编译后的 PDF 里（不只是磁盘上有 .tex）

## 5. 五视角 Panel

按 `references/feedback_layer3_panel.md` 运行，personas 来自 `competitions/mcm/rubric_overlay.json`：
**30-Second Judge**（只看 Summary 和图）、Rigor、Modeling Contribution、Communication、Stakeholder Reader（题面不要 letter/memo 时换成 Reproducibility）。

每个 high-severity 问题回指到一个源节文件并定向修补，只重跑受影响的检查与视角。不要让 panel 预测奖项；只用 `ready` / `refine` / `block`。

## 6. AI 披露终检

```bash
python <skill>/scripts/render_ai_usage.py --decision-log state/decision_log.json --paper-workspace paper_workspace/
```

- 台账非空：确认 `12_ai_use_report.md` 在 25 页之后渲染了一次；`ai_tool_references.md` 的条目已进参考文献；正文使用处有 inline citation
- 台账为 `[]`：确认没有残留的 AI 报告；提交表单 AI uses statement 选 **No**
- 台账为 `null`：不允许提交，先和队伍核对

## 7. 编译与最终目检

用 `render_paper.py` 重新编译（它报解答页数与 TeX 报错数）。翻看：第 1 页、公式密集页、宽表、图多的页、letter/memo、参考文献、AI 报告。

最终提交：`<control number>.pdf`，通过 <https://forms.comap.org/241335097294056> 提交（需要控制号、Advisor ID、题号、AI uses statement）。不发确认邮件；每队只交一次。

## 8. 写入终审结果

```json
{
  "anti_patterns_check": {"total": null, "passed": null, "fixed": null, "deferred": null},
  "compliance_checks": {
    "rules_verified": null,
    "anonymity_passed": null,
    "page_limit_passed": null,
    "ai_disclosure_passed": null,
    "deliverables_passed": null
  },
  "final_pdf_path": "paper_output/<control number>.pdf",
  "submission_ready": null
}
```

上面的 `null` 只是 schema 占位。写入前全部换成实际观测值；不要抄示例。

## L1 Rubric（阶段级 5 维）

Stage 9 有两层反馈：这张是 **L1 阶段级**打分；L3 五视角 panel 另见 `references/feedback_layer3_panel.md`。

<!-- RUBRIC:BEGIN 9 -->
| 维度 | 满分行为 |
|------|---------|
| 1. 反模式覆盖 (`1_anti_pattern_coverage`) | `competitions/mcm/anti_patterns.md` 的全部索引项都过了一遍（数量以 `doctor.py` 报告为准），命中的每一条**要么已修，要么在论文里写明为什么不适用**；不允许"看过了" |
| 2. 图表定稿质量 (`2_visual_polish`) | 逐张过 `figures/README.md` 的硬规矩：轴标签带单位、无双纵轴、≥2 系列有图例、只标结论点、顺序色非彩虹；灰度校样已翻过一遍 |
| 3. Panel 共识 (`3_panel_consensus`) | L3 五视角无 high-severity 未决项；verdict 不靠权重覆盖异议（任一 high-severity 保持 `block`） |
| 4. 瓶颈已处理 (`4_bottleneck_addressed`) | 最低分维度与高影响 issue 已**定向修补并让受影响视角复核**，不是记录在案就算完 |
| 5. 提交件可编可查 (`5_pdf_compile_clean`) | `check_compliance.py` 无 FAIL：第 1 页是 Summary Sheet、解答 ≤25 页、每页页眉含控制号与页码、正文 ≥12pt、全英文、文件名=控制号.pdf 且 <25 MB、题面交付物齐全、用了 AI 则有 Report on Use of AI、无身份信息 |
<!-- RUBRIC:END 9 -->

第 5 维由 `check_compliance.py` 判定，不接受人工"应该没问题"。

## 退出条件

- `check_compliance.py` 退出码 0，`compliance_checks` 全部为 `true`（无 `null`）
- `check_numbers.py`、`check_selfaudit.py`、`check_figures.py` 退出码 0（数量类 WARN 逐条读完再决定）
- 当届规则已核对，无未解决违规；反模式与一致性检查完成
- panel 的 high-severity 问题全部解决
- PDF 已编译并目检；AI 披露完整
- `decision_log.stages.9.submission_ready == true`

然后把最终提交包交还队伍。
