# 美赛交付包（kit）

给人读的配套手册。skill 本体就是仓库根目录（`SKILL.md` + `references/` + `competitions/mcm/` + `scripts/` ……）。

| 文件 | 用法 |
|---|---|
| `0_开赛操作手册.md` | 赛前一周怎么装和自检、开赛当天每一步的命令、提交前必跑的检查、提交流程 |
| `2_提示词模板.md` | 不装 skill 也能用的独立提示词：六题预扫与选题 / 单题深挖 / 按题型深挖（六类）/ 求解呈现 / Summary Sheet / letter-memo / 终审 / 纠偏 |
| `5_算法讲解手册.md` | 通用算法讲解（ODE、优化、统计、机器学习等九族），每条"什么时候用 / 核心 / 参数与坑 / 代码骨架 / 别用它的时候"。**出处栏沿用上游国赛版**（算法本身通用） |

## 三件最该先读的

1. **`../competitions/mcm/current_rules.md`**：25 页覆盖哪些部分、北京时间截止、AI 披露怎么写、2026 年六道题各自要什么交付物。
2. **`../competitions/mcm/abstract_template.md`**：Summary Sheet 怎么写（评委最看重的一页）。
3. **`../competitions/mcm/anti_patterns.md` 的 M 组**：美赛特有的失分点，每条都有可查出处。

## 安装与自检

```bash
git clone https://github.com/zhy-ai0626/meisai_skill ~/.claude/skills/mcm-icm
python ~/.claude/skills/mcm-icm/scripts/doctor.py --require-renderer
```

`latex-smoke` 一项会**真编译一次** `templates/latex/mcm/smoke.tex`；`gates-smoke` 给每个提交门喂一份故意有问题的输入，要求它们真的报出来。
