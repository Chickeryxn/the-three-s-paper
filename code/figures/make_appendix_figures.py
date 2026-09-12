# -*- coding: utf-8 -*-
"""Generate the three appendix figures (Type 4) into paper/figures/."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import LogFormatterMathtext

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figure_style import (PALETTE as P, apply_style, finish, panel_label, DEFAULT_CHECKS,
                           CMAP_TEMP, CMAP_MOIST)
import make_paper_figures as mk


def figA1():
    rowsT = mk.read_sheet("results/Q1/experiments/round1/result1.xlsx", "温度")
    rowsC = mk.read_sheet("results/Q1/experiments/round1/result1.xlsx", "水分浓度")
    tT, T = mk.to_array(rowsT); tC, C = mk.to_array(rowsC)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6), sharey=True)
    for ax, Z, name, unit, cm in ((axes[0], T, "温度 T", "°C", CMAP_TEMP),
                           (axes[1], C, "含水率 C", "kg/kg", CMAP_MOIST)):
        pcm = ax.pcolormesh(mk.R_COLS_CM, tT / 60.0, Z, cmap=cm, shading="auto",
                            vmin=float(np.nanmin(Z)), vmax=float(np.nanmax(Z)))
        cb = fig.colorbar(pcm, ax=ax, pad=0.02)
        cb.set_label("%s / %s" % (name, unit), fontsize=8.5)
        cb.ax.tick_params(labelsize=7.5)
        ax.set_xlabel(r"$\mathbf{r}$ / $\mathbf{cm}$")
    axes[0].set_ylabel(r"$\mathbf{t}$ / $\mathbf{min}$")
    axes[0].set_title("温度")
    axes[1].set_title("含水率")
    fig.tight_layout(w_pad=1.4)
    finish(fig, "figA1_q1_field_map",
           {"data": "results/Q1/experiments/round1/result1.xlsx",
            "note": "Type 4 appendix: full-field view behind figure 2"},
           DEFAULT_CHECKS)


def figA2():
    """问题三含水率场：上为沿整个直径对称展开的时空分布，下为四个时刻的截面圆盘。"""
    t, C = mk.to_array(mk.read_sheet("results/Q3/experiments/round1/result3.xlsx"))
    fig = plt.figure(figsize=(7.4, 2.9))
    gs = fig.add_gridspec(1, 1,
                          left=0.085, right=0.97, top=0.95, bottom=0.07)
    ax = fig.add_subplot(gs[0])
    # 沿 r = 0 对称展开成整个直径：负半径一侧是镜像
    xr = np.concatenate([-mk.R_COLS_CM[::-1], mk.R_COLS_CM[1:]])
    Zm = np.hstack([C[:, ::-1], C[:, 1:]])
    pcm = ax.pcolormesh(t / 3600.0, xr, Zm.T, cmap=CMAP_MOIST, shading="auto",
                        vmin=0.0, vmax=2.55)
    ax.axvline(57.4647, color="black", lw=0.9, ls="--")
    for v in (-1.0, 1.0):
        ax.axhline(v, color="black", lw=0.8, ls=":")
    ax.text(1.2, 2.04, "表面", fontsize=9.0, va="bottom", ha="left")
    cb = fig.colorbar(pcm, ax=ax, pad=0.02)
    cb.set_label(r"$\mathbf{C}$ / ($\mathbf{kg/kg}$)", fontsize=9.0)
    cb.ax.tick_params(labelsize=8.0)
    cb.outline.set_linewidth(0.5)
    ax.set_xlabel(r"$\mathbf{t}$ / $\mathbf{h}$")
    ax.set_ylabel(r"$\mathbf{r}$ / $\mathbf{cm}$")
    ax.set_title("含水率场")
    ax.set_xlim(0, 58)
    ax.set_ylim(-2.1, 2.65)
    # 距离没有负值：刻度一律用绝对值标注
    yt = [-2, -1, 0, 1, 2]
    ax.set_yticks(yt)
    ax.set_yticklabels([str(abs(v)) for v in yt])

    hours = [6, 18, 36, 54]
    idx = [int(np.argmin(np.abs(t - h * 3600.0))) for h in hours]
    knots_r = np.append(mk.R_COLS_CM[:20], 2.0)
    finish(fig, "figA2_q3_full_field",
           {"data": "results/Q3/experiments/round1/result3.xlsx",
            "note": "Type 4 appendix: full-field view behind figure 3; mirrored about r = 0 to show the whole diameter"},
           DEFAULT_CHECKS)

def figA3():
    """问题四收缩域含水率场：上为沿整个直径对称展开的时空分布，下为四个时刻的截面圆盘。

    交付表的最后一列是「药材表面」，位于 r = R(t) 而非固定的 2.0 cm；色场按 |r| <= R(t)
    裁剪，并把负半径一侧按镜像补全，从而显示整个直径。
    """
    import csv
    t, C = mk.to_array(mk.read_sheet("results/Q4/experiments/round1/result4.xlsx"))
    with (mk.ROOT / "workspace/data_clean/attachment2_radius.csv").open(encoding="utf-8") as fh:
        b = np.array([[float(x) for x in r] for r in list(csv.reader(fh))[1:]])
    from scipy.interpolate import PchipInterpolator
    Rf = PchipInterpolator(b[:, 0], b[:, 1])
    Rt = Rf(np.minimum(t, b[-1, 0]))
    cols = np.round(np.arange(20) * 0.1, 10)

    stride = 4
    grid = np.concatenate([-np.arange(0.0, 2.0 + 1e-9, 0.05)[::-1][:-1],
                           np.arange(0.0, 2.0 + 1e-9, 0.05)])
    edges = np.arange(-2.025, 2.0 + 0.025 + 1e-9, 0.05)
    field = np.full((t[::stride].size, grid.size), np.nan)
    for k, i in enumerate(range(0, t.size, stride)):
        row = C[i]
        inner = np.where(~np.isnan(row[:20]))[0]
        m = int(inner[-1]) if inner.size else 0
        knots_r = np.append(cols[:m + 1], Rt[i])
        knots_v = np.append(row[:m + 1], row[20])
        inside = np.abs(grid) <= Rt[i]
        field[k, inside] = np.interp(np.abs(grid[inside]), knots_r, knots_v)

    fig = plt.figure(figsize=(7.4, 2.9))
    gs = fig.add_gridspec(1, 1,
                          left=0.085, right=0.97, top=0.95, bottom=0.07)
    ax = fig.add_subplot(gs[0])
    ts = t[::stride]
    ye = np.empty(ts.size + 1)
    ye[1:-1] = 0.5 * (ts[:-1] + ts[1:])
    ye[0] = ts[0] - 0.5 * (ts[1] - ts[0])
    ye[-1] = ts[-1] + 0.5 * (ts[-1] - ts[-2])
    pcm = ax.pcolormesh(ye / 3600.0, edges, field.T, cmap=CMAP_MOIST, shading="flat",
                        vmin=0.0, vmax=2.55)
    ax.plot(ts / 3600.0, Rt[::stride], color="black", lw=1.0)
    ax.plot(ts / 3600.0, -Rt[::stride], color="black", lw=1.0)
    ax.axvline(52.6361, color="black", lw=0.9, ls="--")
    ax.text(52.0, 2.10, "烘干结束 52.6361 h", fontsize=9.0, ha="right", va="bottom")
    ax.text(30, 1.34, r"边界 $\mathbf{R}(t)$", fontsize=9.0, va="bottom")
    cb = fig.colorbar(pcm, ax=ax, pad=0.02)
    cb.set_label(r"$\mathbf{C}$ / ($\mathbf{kg/kg}$)", fontsize=9.0)
    cb.ax.tick_params(labelsize=8.0)
    cb.outline.set_linewidth(0.5)
    ax.set_xlabel(r"$\mathbf{t}$ / $\mathbf{h}$")
    ax.set_ylabel(r"$\mathbf{r}$ / $\mathbf{cm}$")
    ax.set_title("收缩域含水率场")
    ax.set_xlim(0, 58)
    ax.set_ylim(-2.1, 2.65)
    # 距离没有负值：刻度一律用绝对值标注
    yt = [-2, -1, 0, 1, 2]
    ax.set_yticks(yt)
    ax.set_yticklabels([str(abs(v)) for v in yt])

    hours = [6, 18, 36, 51]
    idx = [int(np.argmin(np.abs(t - h * 3600.0))) for h in hours]
    finish(fig, "figA3_q4_shrinking_field",
           {"data": ["results/Q4/experiments/round1/result4.xlsx",
                     "workspace/data_clean/attachment2_radius.csv"],
            "note": "Type 4 appendix: full-diameter view behind figure 4; the field is clipped at R(t) "
                    "and mirrored about r = 0"},
           DEFAULT_CHECKS)

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    apply_style()
    figA1(); figA2(); figA3()
    print("appendix done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
