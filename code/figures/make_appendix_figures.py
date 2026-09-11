# -*- coding: utf-8 -*-
"""Generate the three appendix figures (Type 4) into paper/figures/."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import LogFormatterMathtext

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figure_style import PALETTE as P, apply_style, finish, panel_label, DEFAULT_CHECKS
import make_paper_figures as mk


def figA1():
    rowsT = mk.read_sheet("results/Q1/experiments/round1/result1.xlsx", "温度")
    rowsC = mk.read_sheet("results/Q1/experiments/round1/result1.xlsx", "水分浓度")
    tT, T = mk.to_array(rowsT); tC, C = mk.to_array(rowsC)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6), sharey=True)
    for ax, Z, name, unit in ((axes[0], T, "温度 T", "°C"), (axes[1], C, "含水率 C", "kg/kg")):
        pcm = ax.pcolormesh(mk.R_COLS_CM, tT / 60.0, Z, cmap="viridis", shading="auto",
                            vmin=float(np.nanmin(Z)), vmax=float(np.nanmax(Z)))
        cb = fig.colorbar(pcm, ax=ax, pad=0.02)
        cb.set_label("%s / %s" % (name, unit), fontsize=7.5)
        cb.ax.tick_params(labelsize=6.5)
        ax.set_xlabel("r / cm")
    axes[0].set_ylabel("t / min")
    axes[0].set_title("温度：整体抬升")
    axes[1].set_title("含水率：仅表层响应")
    for ax, lab in zip(axes, "ab"):
        panel_label(ax, lab)
    fig.tight_layout(w_pad=1.4)
    finish(fig, "figA1_q1_field_map",
           {"data": "results/Q1/experiments/round1/result1.xlsx",
            "note": "Type 4 appendix: full-field view behind figure 2"},
           DEFAULT_CHECKS)


def figA2():
    t, C = mk.to_array(mk.read_sheet("results/Q3/experiments/round1/result3.xlsx"))
    fig = plt.figure(figsize=(7.4, 2.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1.0], wspace=0.28)
    ax = fig.add_subplot(gs[0, 0])
    pcm = ax.pcolormesh(mk.R_COLS_CM, t / 3600.0, C, cmap="viridis", shading="auto",
                        vmin=0.0, vmax=2.55)
    ax.axhline(57.4647, color="white", lw=0.9, ls="--")
    ax.axvline(1.0, color="white", lw=0.8, ls=":")
    ax.axvline(2.0, color="white", lw=0.8, ls=":")
    ax.text(2.02, 52, "表面", color="white", fontsize=7, va="top", ha="right")
    ax.text(1.02, 52, "r = 1.0 cm", color="white", fontsize=7, va="top", ha="right")
    cb = fig.colorbar(pcm, ax=ax, pad=0.02)
    cb.set_label("C / (kg/kg)", fontsize=7.5); cb.ax.tick_params(labelsize=6.5)
    ax.set_xlabel("r / cm"); ax.set_ylabel("t / h")
    ax.set_title("Q2/Q3 完整含水率场（0–57.46 h）")
    ax2 = fig.add_subplot(gs[0, 1])
    for hh, ls in ((6, "-"), (18, "--"), (36, "-."), (54, ":")):
        i = int(np.argmin(np.abs(t - hh * 3600.0)))
        ax2.plot(mk.R_COLS_CM, C[i], ls=ls, lw=1.3,
                 label="%d h" % hh, color=P["primary"] if hh < 30 else P["accent1"])
    ax2.axhline(0.15, color=P["criterion"], lw=1.0, ls="--")
    ax2.set_xlabel("r / cm"); ax2.set_ylabel("C / (kg/kg)")
    ax2.set_title("四个时刻的径向剖面")
    ax2.legend(fontsize=7.2)
    for ax_, lab in zip([ax, ax2], "ab"):
        panel_label(ax_, lab)
    finish(fig, "figA2_q3_full_field",
           {"data": "results/Q3/experiments/round1/result3.xlsx",
            "note": "Type 4 appendix: full-field view behind figure 3; Q2 shares the model"},
           DEFAULT_CHECKS)


def figA3():
    import csv
    t, C = mk.to_array(mk.read_sheet("results/Q4/experiments/round1/result4.xlsx"))
    with (mk.ROOT / "workspace/data_clean/attachment2_radius.csv").open(encoding="utf-8") as fh:
        b = np.array([[float(x) for x in r] for r in list(csv.reader(fh))[1:]])
    tr, rr = b[:, 0], b[:, 1]
    from scipy.interpolate import PchipInterpolator
    Rf = PchipInterpolator(tr, rr)
    Rt = Rf(np.minimum(t, tr[-1]))
    cols = np.round(np.arange(20) * 0.1, 10)          # 0 .. 1.9 cm (physical columns)
    xmesh = np.append(cols, 2.0)                      # the last cell carries the surface value
    mesh = C.copy()
    fig = plt.figure(figsize=(7.4, 2.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1.0], wspace=0.28)
    ax = fig.add_subplot(gs[0, 0])
    pcm = ax.pcolormesh(xmesh, t / 3600.0, mesh, cmap="viridis", shading="auto",
                        vmin=0.0, vmax=2.55)
    ax.plot(Rt, t / 3600.0, color="white", lw=1.3)
    ax.text(1.02, 48, "R(t)", color="white", fontsize=7.5)
    ax.axhline(52.6361, color="white", lw=0.9, ls="--")
    cb = fig.colorbar(pcm, ax=ax, pad=0.02)
    cb.set_label("C / (kg/kg)", fontsize=7.5); cb.ax.tick_params(labelsize=6.5)
    ax.set_xlabel("r / cm"); ax.set_ylabel("t / h")
    ax.set_xlim(0, 2.0); ax.set_ylim(0, 54)
    ax.set_title("Q4 收缩域含水率场（物理坐标，域外留空）")
    ax2 = fig.add_subplot(gs[0, 1])
    for hh, ls in ((6, "-"), (18, "--"), (36, "-."), (51, ":")):
        i = int(np.argmin(np.abs(t - hh * 3600.0)))
        ax2.plot(cols, C[i][:20], ls=ls, lw=1.3,
                 color=P["primary"] if hh < 30 else P["accent1"])
        ax2.plot([Rt[i]], [C[i][20]], marker="o", ms=3.2,
                 color=P["primary"] if hh < 30 else P["accent1"],
                 label="%d h（表面 %.2f cm）" % (hh, Rt[i]))
    ax2.axhline(0.15, color=P["criterion"], lw=1.0, ls="--")
    ax2.set_xlabel("r / cm"); ax2.set_ylabel("C / (kg/kg)")
    ax2.set_title("剖面随 R(t) 内移")
    ax2.legend(fontsize=7.2, loc="upper right")
    for ax_, lab in zip([ax, ax2], "ab"):
        panel_label(ax_, lab)
    finish(fig, "figA3_q4_shrinking_field",
           {"data": ["results/Q4/experiments/round1/result4.xlsx",
                     "workspace/data_clean/attachment2_radius.csv"],
            "note": "Type 4 appendix: full-field view behind figure 4; the boundary R(t) is drawn on top and cells with r > R(t) are blank in the deliverable"},
           DEFAULT_CHECKS)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    apply_style()
    figA1(); figA2(); figA3()
    print("appendix done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
