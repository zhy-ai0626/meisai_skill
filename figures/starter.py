# -*- coding: utf-8 -*-
"""**拿来就改的绘图起手式（英文图）。** 把这个文件拷进你的项目，替换 `load_data()`，就能出图。

跑法
----
    python figures/starter.py                 # 六段全出（用内置合成数据）
    python figures/starter.py --only 2        # 只出第 2 段
    python figures/starter.py --out ./figs    # 换输出目录

**赛前先裸跑一次。** 它同时是环境自检：matplotlib、字体回退、Pillow（灰度校样）
哪一样没配好，这里就会报出来——而不是等到比赛第三天出图时才发现。

六段是什么，为什么是这六段
--------------------------
按 O 奖论文的图题分布挑的（见 competitions/mcm/empirical.json 的 figure 统计）：

| 段 | 图 | 什么时候用 |
|---|---|---|
| 1 | 描述统计三联 | Stage 2 看清数据长什么样；C 题 / 数据题的 Data Overview 一节 |
| 2 | 相关矩阵 + 散点确认 | 指标筛选、变量耦合建模（C/D/F 题常用） |
| 3 | 拟合 + **残差** | 参数估计 / 模型验证。只画"拟合得很好"没有说服力 |
| 4 | 灵敏度龙卷风 | Stage 6 标准交付，**必须按影响幅度排序** |
| 5 | 分组趋势 + 个体轨迹 | 同一对象多条记录（面板数据）时，让读者看见观测不独立 |
| 6 | 总体流程图 | O 奖论文 Introduction 里的 "Our Work" 图。可编辑版本用 `flow_pptx.py` |

三条到处都适用的硬规矩（`ms.finish()` 会强制前两条）
-----------------------------------------------------
1. **坐标轴必须带单位**，无量纲量写 "(dimensionless)"。
2. **绝不用双纵轴**，两个量量纲不同就画两张。
3. **图题写"这张图说明什么"**：写 "SOC falls fastest under video streaming at 0 °C"，
   不写 "SOC curve"。**图里不得出现中文**（美赛论文必须是英文）。
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt          # noqa: E402

import mcm_style as ms                   # noqa: E402

OUT = "figures_out"


def init_stdout() -> None:
    """Windows 输出编码兜底。**只在非 tty 时切 UTF-8。**

    中文版 Windows 把 `sys.stdout` 的编码定成 cp936(GBK)。一旦输出被管道或
    重定向接走（Git Bash 的 mintty 也算），中文提示就会打成乱码。
    （skill 里的完整版在 `scripts/_console.py`；这里内联一份，
    是因为本文件是设计成拷进你项目单独用的。）
    """
    for stream in (sys.stdout, sys.stderr):
        rec = getattr(stream, "reconfigure", None)
        if rec is None:
            continue
        try:
            tty = stream.isatty()
        except (ValueError, OSError):
            tty = False
        try:
            rec(encoding="utf-8", errors="replace") if not tty \
                else rec(errors="replace")
        except (ValueError, OSError):
            pass


# ==================================================================
#  ← 换成你的数据。下面这个函数是唯一需要动的地方。
# ==================================================================
def load_data() -> dict:
    """返回画图要用的数据。**把函数体换成读你自己的数据。**

    真实版本大概长这样（以 2026 C 题为例）：

        import pandas as pd
        df = pd.read_csv("2026_MCM_Problem_C_Data.csv")
        return {
            "values":  df["judge_score"].to_numpy(),
            "groups":  df["season_group"].to_numpy(),
            "miss":    df.isna().mean(),                    # 逐列缺失率
            "matrix":  df[NUM_COLS].to_numpy(),
            "labels":  NUM_COLS,
            "units":   ["points", "weeks", ...],            # 和 labels 一一对应
            ...
        }

    **单位跟着变量走，不要写死在轴标签里。** 相关矩阵里"最强的那一对"是算出来的，
    换一份数据就换一对变量——轴标签里硬写的单位不会报错，只会写错。
    """
    rng = np.random.default_rng(20270128)
    n = 900

    # —— 一维观测量（右偏，做示范用）
    values = rng.lognormal(mean=1.85, sigma=0.42, size=n)
    groups = rng.integers(0, 4, size=n)
    group_names = ["<28", "28-32", "32-36", ">=36"]
    values = values + np.array([-0.9, 0.0, 0.7, 1.4])[groups]

    # —— 逐列缺失率（列名 → 比例）
    miss = {"age": 0.002, "industry": 0.0, "week": 0.0,
            "judge score": 0.0, "partner": 0.006,
            "home state": 0.171, "region": 0.171}

    # —— 多变量矩阵（用因子模型生成，保证相关矩阵半正定）
    f1, f2 = rng.normal(size=n), rng.normal(size=n)
    area = 60 + 14 * f1 + rng.normal(0, 3, n)
    yield_ = 420 + 55 * f1 + rng.normal(0, 40, n)
    price = 6.2 + 1.5 * f2 + rng.normal(0, 0.35, n)
    cost = 2.4 + 0.42 * f2 + 0.006 * area + rng.normal(0, 0.22, n)
    profit = (yield_ * area * price - cost * area) / 1e4
    matrix = np.column_stack([area, yield_, price, cost, profit])
    labels = ["Area", "Yield", "Price", "Cost", "Profit"]
    units = ["ha", "kg/ha", "USD/kg", "USD/ha", "10k USD"]

    # —— 观测 + 模型（参数估计类）
    x = np.linspace(500, 1500, 700)
    truth = 0.5 + 0.42 * np.cos(4 * np.pi * (2.55 + 4.0e-6 * x ** 2)
                                * 7.45 * x * 1e-4)
    obs = truth + rng.normal(0, 0.012, x.size)
    fit = 0.5 + 0.42 * np.cos(4 * np.pi * (2.55 + 3.4e-6 * x ** 2)
                              * 7.44 * x * 1e-4)

    # —— 灵敏度：每个参数 ±10% 时目标的变化率（%）
    sens = {"Yield": (-12.4, 11.8), "Price": (-9.1, 9.4),
            "Cost": (5.6, -5.3), "Demand": (-3.2, 1.1),
            "Discount factor": (-1.4, 1.3), "Interest rate": (-0.6, 0.6)}

    # —— 面板数据：同一对象多次观测
    n_sub, n_obs = 60, 5
    sub = np.repeat(np.arange(n_sub), n_obs)
    t = np.tile(np.linspace(11, 25, n_obs), n_sub) + rng.normal(0, .4, n_sub * n_obs)
    y_panel = (2.0 + 0.28 * t + rng.normal(0, 1.6, n_sub)[sub]
               + rng.normal(0, .5, n_sub * n_obs))
    sub_group = rng.integers(0, 3, n_sub)[sub]

    return dict(values=values, groups=groups, group_names=group_names,
                miss=miss, matrix=matrix, labels=labels, units=units,
                x=x, obs=obs, fit=fit, sens=sens,
                panel=(sub, t, y_panel, sub_group))


# ==================================================================
#  1. 描述统计三联：分布 + 分组箱线 + 逐列缺失
# ==================================================================
def fig_descriptive(d: dict) -> str:
    """先看清数据长什么样，**再决定动不动它**（判据见 competitions/mcm/静默陷阱.md）。"""
    fig, axes = plt.subplots(1, 3, figsize=(10.4, 3.5),
                             gridspec_kw={"width_ratios": [1, 1, 1.05]})
    v, g = d["values"], d["groups"]

    ax = axes[0]
    ax.hist(v, bins=36, **ms.series_kw(0, "fill", alpha=0.75))
    for val, name, slot in ((np.median(v), "median", 7), (v.mean(), "mean", 3)):
        ax.axvline(val, color=ms.COLORS[slot], lw=1.4,
                   ls="--" if name == "mean" else "-",
                   label="%s %.2f" % (name, val), zorder=4)
    ms.finish(ax, xlabel="Observed value (%)",       # ← 换成你的量和单位
              ylabel="Count",
              title="(a) Right-skewed: report the median")

    ax = axes[1]
    data = [v[g == k] for k in range(len(d["group_names"]))]
    bp = ax.boxplot(data, widths=0.58, patch_artist=True, showfliers=True,
                    medianprops=dict(color=ms.INK, linewidth=1.3),
                    whiskerprops=dict(color=ms.AXIS, linewidth=0.9),
                    capprops=dict(color=ms.AXIS, linewidth=0.9),
                    flierprops=dict(marker="o", markersize=2.4,
                                    markerfacecolor=ms.MUTED,
                                    markeredgecolor="none", alpha=0.5))
    for i, patch in enumerate(bp["boxes"]):
        kw = ms.series_kw(i, "bar")
        patch.set(facecolor=kw["facecolor"], hatch=kw["hatch"],
                  edgecolor=ms.SURFACE, linewidth=0.0)
    ax.set_xticks(range(1, len(data) + 1), d["group_names"])
    ms.finish(ax, xlabel="Group (dimensionless)", ylabel="Observed value (%)",
              title="(b) Outliers kept and shown", legend=False)

    ax = axes[2]
    cols = list(d["miss"]); rate = np.array([d["miss"][c] for c in cols])
    order = np.argsort(rate)
    ax.barh(np.arange(len(cols)), rate[order] * 100,
            **ms.series_kw(0, "bar", height=0.62))
    ax.set_yticks(range(len(cols)), [cols[k] for k in order])
    for y, val in enumerate(rate[order]):
        if val > 0:
            ax.text(val * 100 + 0.35, y, "%.1f%%" % (val * 100), va="center",
                    fontsize=ms.BASE_FONT - 2, color=ms.INK_2)
    ax.set_xlim(0, max(rate.max() * 100 * 1.35, 1.0))
    ms.finish(ax, xlabel="Missing rate (%)", ylabel="Column (sorted)",
              title="(c) Equal rates -> same rows: not random", legend=False)

    fig.tight_layout()
    return ms.save(fig, os.path.join(OUT, "01_descriptive.png"))["path"]


# ==================================================================
#  2. 相关矩阵 + 最强那一对的散点确认
# ==================================================================
def spearman(X: np.ndarray) -> np.ndarray:
    """Spearman = 秩上的 Pearson。自己算，省一个 scipy 依赖。

    选它而不选 Pearson 的理由要写进论文：不要求正态、对单调非线性和离群点都稳。
    """
    R = np.apply_along_axis(
        lambda c: np.argsort(np.argsort(c)).astype(float), 0, X)
    return np.corrcoef(R, rowvar=False)


def fig_correlation(d: dict) -> str:
    """热力图只给候选，**不给结论**。删指标之前必须看散点。"""
    X, labels, units = d["matrix"], d["labels"], d["units"]
    C = spearman(X)

    fig, (ax, ax2) = plt.subplots(
        1, 2, figsize=(9.4, 4.2), gridspec_kw={"width_ratios": [1.25, 1]})

    # 色标钉在 [-1, 1]、0 在中点。随手 imshow(C) 会按数据范围自动拉伸，
    # 强正相关会长得像中性——而且不报错。helper 会拦住超范围的输入。
    ms.corr_heatmap(ax, C, labels, annot_min=0.45,
                    cbar_label=r"Spearman $\rho$ (dimensionless)")
    ax.set_title(r"(a) Cells with $|\rho|\geq 0.45$ annotated",
                 loc="left", pad=8, fontsize=ms.BASE_FONT)

    tri = np.tril(np.abs(C), k=-1)
    i, j = np.unravel_index(np.argmax(tri), tri.shape)
    ax2.plot(X[:, j], X[:, i], label="Observations (n=%d)" % len(X),
             **ms.series_kw(0, "scatter", n_series=1,
                            markersize=3.0, alpha=0.5))
    q = np.quantile(X[:, j], np.linspace(0, 1, 9))
    mid, med = [], []
    for a, b in zip(q[:-1], q[1:]):
        m = (X[:, j] >= a) & (X[:, j] <= b)
        if m.sum() >= 5:
            mid.append(np.median(X[m, j])); med.append(np.median(X[m, i]))
    ax2.plot(mid, med, color=ms.COLORS[7], lw=1.6, ls="--", marker="",
             zorder=4, label="Binned median")
    ms.finish(ax2, xlabel="%s (%s)" % (labels[j], units[j]),
              ylabel="%s (%s)" % (labels[i], units[i]),
              title=r"(b) $\rho$=%.2f: monotone, not outlier-driven" % C[i, j])
    fig.tight_layout()
    return ms.save(fig, os.path.join(OUT, "02_correlation.png"))["path"]


# ==================================================================
#  3. 拟合 + 残差
# ==================================================================
def fig_fit_residual(d: dict) -> str:
    """**残差图才看得出系统性偏差。** 只画"拟合得很好"没有说服力。"""
    x, obs, fit = d["x"], d["obs"], d["fit"]
    # hspace 不要放进 gridspec_kw：tight_layout() 会把它丢掉，
    # 只给一句 UserWarning，图照出（间距静默失效）。放到 tight_layout 之后。
    fig, (ax, axr) = plt.subplots(2, 1, figsize=(9.6, 4.6), sharex=True,
                                  gridspec_kw={"height_ratios": [3, 1]})
    ax.plot(x, obs, label="Measured",
            **ms.series_kw(0, "line", n_points=x.size, alpha=0.9))
    ax.plot(x, fit, label="Model", **ms.series_kw(1, "line", n_points=x.size))
    k = int(np.argmax(obs))
    ms.annotate_value(ax, x[k], obs[k], "first peak %.0f" % x[k], dy=7)
    ms.finish(ax, xlabel=" ", ylabel="Reflectance (dimensionless)",
              title="(a) Observation vs. model")
    ax.set_xlabel("")

    res = obs - fit
    axr.axhline(0, color=ms.AXIS, lw=0.9, zorder=1)
    axr.plot(x, res, label="Residual", color=ms.COLORS[7], lw=1.0, zorder=3)
    axr.fill_between(x, res, 0, color=ms.COLORS[7], alpha=0.18, lw=0)
    rmse = float(np.sqrt((res ** 2).mean()))
    ms.finish(axr, xlabel="Wavenumber (cm$^{-1}$)", ylabel="Residual",
              title="(b) RMSE=%.4f; structure at low wavenumber -> model gap" % rmse,
              legend=False)
    fig.tight_layout()
    fig.subplots_adjust(hspace=0.10)
    return ms.save(fig, os.path.join(OUT, "03_fit_residual.png"))["path"]


# ==================================================================
#  4. 灵敏度龙卷风
# ==================================================================
def fig_tornado(d: dict) -> str:
    """Stage 6 标准交付。**必须按影响幅度排序——不排序等于没画。**"""
    items = d["sens"]
    names = list(items)
    low = np.array([items[k][0] for k in names])
    high = np.array([items[k][1] for k in names])
    span = np.abs(high - low)
    order = np.argsort(span)                    # 从小到大，画出来最大的在顶上

    y = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    # 走 series_kw：颜色、填充网格、edgecolor 是捆在一起给的。
    # 自己写 `edgecolor=` 和填充同色，灰度稿里两根条会糊成一样。
    ax.barh(y, low[order], label="Parameter -10%",
            **ms.series_kw(0, "bar", height=0.62))
    ax.barh(y, high[order], label="Parameter +10%",
            **ms.series_kw(7, "bar", height=0.62))
    ax.axvline(0, color=ms.AXIS, lw=1.0, zorder=4)
    ax.set_yticks(y, [names[k] for k in order])
    # 两个系列必须有图例：Cost 那一行符号是反的（成本涨→利润降），
    # 没有图例读者分不清哪边是加、哪边是减。
    top = order[-1]
    # 标注放在**图内左下**：龙卷风图按幅度排序后，最短的条在底部，左下角必然空。
    # 挂在条端会顶到边界被裁掉，放左上则压在最长那根条上。
    ax.text(0.02, 0.05, "%s dominates: +/-10%% -> objective +/-%.1f%%"
            % (names[top], span[top] / 2),
            transform=ax.transAxes, ha="left", va="bottom",
            fontsize=ms.BASE_FONT - 1, color=ms.INK)
    ax.margins(x=0.06)
    ms.finish(ax, xlabel="Change in objective (%)", ylabel="Parameter (by impact)",
              title="Objective response to +/-10% parameter changes",
              legend_loc="lower right")
    fig.tight_layout()
    return ms.save(fig, os.path.join(OUT, "04_tornado.png"))["path"]


# ==================================================================
#  5. 分组趋势 + 个体轨迹
# ==================================================================
def fig_panel(d: dict) -> str:
    """同一对象多条记录时，**灰细线画出个体轨迹**，让读者看见观测不独立。

    这种数据不能当独立样本做回归，要上混合效应或 GEE，报 R² 要说清是边际还是条件。
    """
    sub, t, y, grp = d["panel"]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for s in np.unique(sub):                     # 个体轨迹：灰、细、压在底层
        m = sub == s
        o = np.argsort(t[m])
        ax.plot(t[m][o], y[m][o], color=ms.MUTED, lw=0.5, alpha=0.45,
                zorder=1, marker="")
    bins = np.linspace(t.min(), t.max(), 7)
    for k in np.unique(grp):
        mx, my = [], []
        for a, b in zip(bins[:-1], bins[1:]):
            m = (grp == k) & (t >= a) & (t < b)
            if m.sum() >= 3:
                mx.append(t[m].mean()); my.append(y[m].mean())
        # series_kw 返回的 dict 里已经带了 zorder，再显式传一个会
        # TypeError: got multiple values。要改层级就写进 series_kw 的 overrides。
        ax.plot(mx, my, label="Group %d (n=%d)" % (k + 1, (grp == k).sum()),
                **ms.series_kw(int(k), "line", zorder=3))
    ms.finish(ax, xlabel="Time (weeks)", ylabel="Observed value (%)",
              title="Thin grey lines: individual trajectories (repeated measures)")
    ms.add_units_note(fig, "%d subjects / %d observations" % (len(np.unique(sub)), len(t)))
    fig.tight_layout()
    return ms.save(fig, os.path.join(OUT, "05_panel.png"))["path"]


# ==================================================================
#  6. 总体流程图（"Our Work"）
# ==================================================================
def fig_flow(_d: dict) -> str:
    """O 奖论文 Introduction 末尾几乎都有一张 "Our Work" 总览图。
    **要可编辑的版本用 `flow_pptx.py`**——96 小时里它要改三四遍。"""
    fig, ax = ms.flow_canvas(figsize=(6.4, 4.6))
    b0 = ms.flow_box(ax, 20, 84, 60, 12, "Problem statement + data", tint="input")
    b1 = ms.flow_box(ax, 20, 64, 60, 13, "Data audit -> problem shape", tint="step")
    b2 = ms.flow_box(ax, 20, 42, 60, 14,
                     "Task 1 -> Task 2 -> Task 3\nsimplest model first, then extend",
                     tint="model")
    b3 = ms.flow_box(ax, 20, 22, 60, 13, "Validation + sensitivity", tint="check")
    b4 = ms.flow_box(ax, 20, 4, 60, 11, "Conclusions + letter/memo", tint="output")
    for a, b in ((b0, b1), (b1, b2), (b2, b3), (b3, b4)):
        ms.flow_arrow(ax, a.s, b.n)
    # 反馈边：虚线 + 直角折线，走主干外侧。angle 两端平行会被 helper 拦住。
    ms.flow_arrow(ax, b3.w_, b2.bottom(0.25), angle=(180, 90), dashed=True)
    ax.text(3, 37, "inconsistent\n-> revise", ha="left", va="center",
            fontsize=ms.BASE_FONT - 2, color=ms.INK_2)
    ax.set_title("Overview of our work (editable version: flow_pptx.py)",
                 loc="left", pad=8, fontsize=ms.BASE_FONT)
    fig.tight_layout()
    return ms.save(fig, os.path.join(OUT, "06_overview.png"))["path"]


STEPS = [fig_descriptive, fig_correlation, fig_fit_residual,
         fig_tornado, fig_panel, fig_flow]


def main(argv: list[str] | None = None) -> int:
    global OUT
    ap = argparse.ArgumentParser(description="MCM/ICM 绘图起手式")
    ap.add_argument("--out", default=OUT, help="输出目录，默认 figures_out/")
    ap.add_argument("--only", type=int, choices=range(1, len(STEPS) + 1),
                    help="只出第 N 段")
    args = ap.parse_args(argv)
    OUT = args.out
    init_stdout()

    font = ms.use()
    print("字体：%s" % font)
    data = load_data()
    print("数据：%d 个观测，%d 个变量（**这是内置合成数据，记得换成你的**）"
          % (len(data["values"]), len(data["labels"])))

    todo = [STEPS[args.only - 1]] if args.only else STEPS
    for fn in todo:
        path = fn(data)
        print("  [OK] %s" % path)
    print("\n共 %d 张，输出在 %s" % (len(todo), os.path.abspath(OUT)))
    print("每张都配了 _gray.png：翻一遍就知道打印稿什么样（成本近零的保险）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
