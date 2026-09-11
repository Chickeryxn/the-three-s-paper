# -*- coding: utf-8 -*-
"""Generate the six paper figures (Type 3) into paper/figures/ with render evidence."""
from __future__ import annotations
import csv, importlib.util, json, sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrow, FancyBboxPatch
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figure_style import ROOT, PALETTE, apply_style, finish, panel_label, DEFAULT_CHECKS

P = PALETTE
R_COLS_CM = np.round(np.arange(21) * 0.1, 10)


def load_json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def read_sheet(rel, sheet=None):
    import openpyxl
    wb = openpyxl.load_workbook(ROOT / rel, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb.worksheets[0]
    rows = [[v for v in r] for r in ws.iter_rows(values_only=True)]
    wb.close()
    return rows


def to_array(rows):
    """rows[0] is the header; remaining rows are time + distance columns."""
    rows = [r for r in rows[1:] if r and r[0] is not None]
    t = np.array([float(r[0]) for r in rows])
    body = np.array([[np.nan if v is None else float(v) for v in r[1:]] for r in rows])
    return t, body


def load_env():
    with (ROOT / "workspace/data_clean/attachment1_env.csv").open(encoding="utf-8") as fh:
        a = np.array([[float(x) for x in r] for r in list(csv.reader(fh))[1:]])
    with (ROOT / "workspace/data_clean/attachment2_radius.csv").open(encoding="utf-8") as fh:
        b = np.array([[float(x) for x in r] for r in list(csv.reader(fh))[1:]])
    return a, b


def bessel():
    spec = importlib.util.spec_from_file_location("q4v", ROOT / "code/Q4/q4_verifier.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.bessel_C


# ---------------------------------------------------------------- figure 1
def fig01():
    env, rad = load_env()
    te, ti, ci = env[:, 0], env[:, 1], env[:, 2]
    fig = plt.figure(figsize=(7.2, 2.9))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.35], wspace=0.28)
    ax = fig.add_subplot(gs[0, 0])
    ax.set_aspect("equal")
    ax.add_patch(Circle((0, 0), 1.0, facecolor=P["primary_pale"], edgecolor=P["primary"], lw=1.4))
    # the shrinking radius is marked by LINE STYLE (dashed), not by colour: the
    # annotation text is black, so a red circle would be the only coloured
    # element left in an otherwise monochrome schematic
    ax.add_patch(Circle((0, 0), 0.599, facecolor="none", edgecolor="black",
                        lw=1.2, ls=(0, (4, 2))))
    ax.plot([0], [0], marker="+", color="k", ms=8, mew=1.2)
    ax.annotate("", xy=(1.0, 0), xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color="k", lw=1.0))
    ax.text(0.62, 0.09, "r", fontsize=9, fontweight="bold")
    ax.text(0.05, -0.14, "r = 0\n对称", fontsize=7.4, ha="left", va="top")
    for ang in np.linspace(-70, 70, 5):
        a = np.deg2rad(ang)
        ax.add_patch(FancyArrow(1.02 * np.cos(a), 1.02 * np.sin(a),
                                0.30 * np.cos(a), 0.30 * np.sin(a),
                                width=0.008, head_width=0.06, head_length=0.09,
                                color=P["primary"], length_includes_head=True))
    # No equations in the schematic: the Robin conditions are derived in the text
    # and a two-line formula block here only duplicated them at an unreadable size.
    ax.text(1.05, 1.16, "r = R(t)：第三类对流边界\n（表面对流换热与传质）",
            fontsize=9.0, ha="center", va="bottom")
    # split onto two lines: as one line it was wider than the disc and hugged the
    # panel edge once bbox_inches="tight" cropped the canvas
    ax.text(0.0, -1.22, "R(t)：2.000 cm $\\rightarrow$ 1.198 cm\n（收缩 40.1%）", fontsize=8.6,
            ha="center", va="top", linespacing=1.4)
    ax.set_xlim(-1.35, 1.45); ax.set_ylim(-1.45, 1.75)
    ax.axis("off")
    panel_label(ax, "a", dx=-0.02, dy=0.98)

    ax2 = fig.add_subplot(gs[0, 1])
    txt = np.linspace(0, 72000, 600)
    ti_x = np.interp(np.minimum(txt, te[-1]), te, ti)
    ti_x = np.where(txt <= te[-1], ti_x, 50.0)
    ci_x = np.interp(np.minimum(txt, te[-1]), te, ci)
    ci_x = np.where(txt <= te[-1], ci_x, 0.05)
    ax2.plot(te / 3600.0, ti, color=P["negative"], lw=1.6, label="$T_\\infty$ 实测（附件1）")
    ax2.plot(txt / 3600.0, ti_x, color=P["negative"], lw=1.1, ls="--",
             label="$T_\\infty$ 外推口径（50 °C）")
    ax2.set_xlabel("t / h"); ax2.set_ylabel("$T_\\infty$ / °C")

    ax2.axvline(4.0, color=P["neutral_mid"], lw=0.8, ls=":")
    ax2.text(4.15, 33, "14400 s", fontsize=7.6)
    ax3 = ax2.twinx()
    ax3.plot(te / 3600.0, ci, color=P["primary"], lw=1.6, label="$C_\\infty$ 实测（附件1）")
    ax3.plot(txt / 3600.0, ci_x, color=P["primary"], lw=1.1, ls="--",
             label="$C_\\infty$ 外推口径（0.05 kg/kg）")
    ax3.set_ylabel("$C_\\infty$ / (kg/kg)")

    h1, l1 = ax2.get_legend_handles_labels(); h2, l2 = ax3.get_legend_handles_labels()
    ax2.legend(h1 + h2, l1 + l2, loc="center right", fontsize=7.2)
    ax2.set_title("两阶段环境驱动：预热实测 + 恒温外推")
    panel_label(ax2, "b")
    finish(fig, "fig01_model_setup_and_environment",
           {"env": "workspace/data_clean/attachment1_env.csv",
            "radius": "workspace/data_clean/attachment2_radius.csv",
            "decisions": ["g_framing_env_extrapolation", "g_framing_spatial_dimension"]},
           DEFAULT_CHECKS + ["schematic axes hidden; schematic is not data-bearing"])


# ---------------------------------------------------------------- figure 2
def fig02():
    rowsT = read_sheet("results/Q1/experiments/round1/result1.xlsx", "温度")
    rowsC = read_sheet("results/Q1/experiments/round1/result1.xlsx", "水分浓度")
    tT, T = to_array(rowsT); tC, C = to_array(rowsC)
    times = [100, 300, 600, 900, 1200, 1500, 1800]
    idx = [int(np.where(tT == t)[0][0]) for t in times]
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.5))
    cmap = plt.get_cmap("viridis")
    for k, i in enumerate(idx):
        c = cmap(k / (len(idx) - 1))
        axes[0].plot(R_COLS_CM, T[i], color=c, lw=1.2, marker="o", ms=2.2,
                     label="%d s" % times[k])
        axes[1].plot(R_COLS_CM, C[i], color=c, lw=1.2, marker="o", ms=2.2)
    axes[0].set_xlabel("r / cm"); axes[0].set_ylabel("T / °C")
    axes[0].set_title("温度剖面在此阶段整体抬升")
    axes[0].legend(fontsize=7.2, ncol=2, loc="lower right")
    axes[1].set_xlabel("r / cm"); axes[1].set_ylabel("C / (kg/kg)")
    axes[1].set_title("含水率仅表层下降")
    axes[2].plot(tT, T[:, 0], color=P["primary"], lw=1.4, label="中心 T")
    axes[2].plot(tT, T[:, -1], color=P["primary"], lw=1.4, ls="--", label="表面 T")
    axes[2].plot(tC, C[:, 0], color=P["accent1"], lw=1.4, label="中心 C")
    axes[2].plot(tC, C[:, -1], color=P["accent1"], lw=1.4, ls="--", label="表面 C")
    axes[2].set_xlabel("t / s")
    axes[2].set_ylabel("$\\mathbf{T}$ / °C,  $\\mathbf{C}$ / (kg/kg)")
    axes[2].set_title("中心滞后、表面先行")
    axes[2].legend(fontsize=7.2, loc="center right")
        
    
    for ax, lab in zip(axes, "abc"):
        panel_label(ax, lab)
    fig.tight_layout(w_pad=3.0)
    finish(fig, "fig02_preheat_fields",
           {"data": "results/Q1/experiments/round1/result1.xlsx",
            "claims": ["q1_T_center_1800s", "q1_T_surface_1800s", "q1_C_center_1800s",
                       "q1_C_surface_1800s"],
            "grid": "1800 rows x 21 columns (1 s x 0.1 cm)"},
           DEFAULT_CHECKS)


# ---------------------------------------------------------------- figure 3
def fig03():
    rows = read_sheet("results/Q3/experiments/round1/result3.xlsx")
    t, C = to_array(rows)
    tmax = np.nanmax(C, axis=1)
    th = t / 3600.0
    tdry = load_json("results/Q3/experiments/round1/metrics/main.json")["drying_time_hours"]
    fig = plt.figure(figsize=(7.4, 2.7))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 1.0, 1.15], wspace=0.34)
    ax = fig.add_subplot(gs[0, 0])
    ax.plot(th, tmax, color=P["primary"], lw=1.6)
    ax.axhline(0.15, color=P["criterion"], lw=1.0, ls="--")
    ax.axvline(tdry, color=P["negative"], lw=0.9, ls=":")
    ax.annotate("57.4647 h", xy=(tdry, 1.4), xytext=(tdry - 22, 1.75), fontsize=7,
                color=P["negative"],
                arrowprops=dict(arrowstyle="->", color=P["negative"], lw=0.8))
    ax.text(1.0, 0.17, "判据 0.15 kg/kg", fontsize=7, color=P["criterion"])
    ax.set_xlabel("t / h"); ax.set_ylabel("max $\\mathbf{C}$ / (kg/kg)")
    ax.set_title("全域最大含水率与判据")
    ax.set_ylim(0, 2.75)
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(th, C[:, 0], color=P["primary"], lw=1.4, label="中心")
    ax2.plot(th, C[:, 10], color=P["accent1"], lw=1.4, ls="-.", label="r = 1.0 cm")
    ax2.plot(th, C[:, -1], color=P["negative"], lw=1.4, ls="--", label="表面")
    ax2.axhline(0.15, color=P["criterion"], lw=1.0, ls="--")
    ax2.set_xlabel("t / h"); ax2.set_ylabel("C / (kg/kg)")
    ax2.set_title("各位置含水率时程")
    ax2.legend(fontsize=7.2)
    ax3 = fig.add_subplot(gs[0, 2])
    rv = load_json("robustness/Q3/q3_robustness_summary.json")["checks"]
    base = 57.46472222222222
    items = [("h_m ±5%", [rv["h_m_perturbation"]["plus5pct"]["observed"]["t_dry_shift_hours"],
                          rv["h_m_perturbation"]["minus5pct"]["observed"]["t_dry_shift_hours"]]),
             ("$C_\\infty$ ±0.005", [rv["env_extrapolation_c_inf_0.045"]["observed"]["t_dry_shift_hours"],
                            rv["env_extrapolation_c_inf_0.055"]["observed"]["t_dry_shift_hours"]]),
             ("D +5%", [rv["D_perturbation"]["observed"]["t_dry_shift_hours"]]),
             ("$T_\\infty$ = 52 °C", [rv["env_extrapolation_t_inf_52"]["observed"]["t_dry_shift_hours"]]),
             ("湿基自洽式", [rv["mass_equation_form"]["observed"]["t_dry_shift_hours"]])]
    labels = [it[0] for it in items]
    ypos = np.arange(len(items))[::-1]
    for y, (lab, vals) in zip(ypos, items):
        for k, v in enumerate(vals):
            col = P["positive"] if v > 0 else P["negative"]
            ax3.barh(y + (0.16 if k else (-0.16 if len(vals) > 1 else 0)),
                     100 * v / base, height=(0.28 if len(vals) > 1 else 0.4),
                     color=col, edgecolor="black", lw=0.5)
            ax3.text(100 * v / base + (0.35 if v > 0 else -0.35),
                     y + (0.16 if k else (-0.16 if len(vals) > 1 else 0)),
                     "%+.2f%%" % (100 * v / base), fontsize=7.2,
                     va="center", ha="left" if v > 0 else "right")
    ax3.axvline(0, color="k", lw=0.8)
    ax3.set_yticks(ypos); ax3.set_yticklabels(labels, fontsize=8.0)
    ax3.set_xlabel("烘干时长变化 / %")
    ax3.set_xlim(-19, 6)
    ax3.set_title("敏感性：扩散与环境主导")
    for ax_, lab in zip([ax, ax2, ax3], "abc"):
        panel_label(ax_, lab)
    finish(fig, "fig03_drying_curve_and_sensitivity",
           {"data": "results/Q3/experiments/round1/result3.xlsx (Q2 shares the same model)",
            "robustness": "robustness/Q3/q3_robustness_summary.json",
            "claims": ["q2_drying_time", "q3_drying_time", "q2_sens_h_m_plus5pct",
                       "q2_sens_D_plus5pct", "q2_sens_T_inf_plus2C",
                       "q2_sens_mass_equation_form"]},
           DEFAULT_CHECKS)


# ---------------------------------------------------------------- figure 4
def fig04():
    env, rad = load_env()
    tr, rr = rad[:, 0], rad[:, 1]
    r3 = read_sheet("results/Q3/experiments/round1/result3.xlsx")
    t3, C3 = to_array(r3)
    r4 = read_sheet("results/Q4/experiments/round1/result4.xlsx")
    t4, C4 = to_array(r4)
    m4 = load_json("results/Q4/experiments/round1/metrics/main.json")
    m3 = load_json("results/Q3/experiments/round1/metrics/main.json")
    fig = plt.figure(figsize=(7.4, 2.6))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.25, 1.0], wspace=0.34)
    ax = fig.add_subplot(gs[0, 0])
    ax.plot(tr / 3600.0, rr, color=P["negative"], lw=1.6)
    ax.axhline(1.198, color=P["neutral_mid"], lw=0.8, ls=":")
    ax.annotate("1.198 cm", xy=(tr[-1] / 3600.0 * 0.98, 1.198), xytext=(20, 1.42),
                fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.8, color=P["neutral_dark"]))
    ax.annotate("2.000 cm", xy=(0.6, 2.0), xytext=(6, 2.05), fontsize=7)
    ax.set_xlabel("t / h"); ax.set_ylabel("R / cm")
    ax.set_title("附件2 半径收缩")
    ax.set_ylim(1.05, 2.2)
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(t3 / 3600.0, np.nanmax(C3, axis=1), color=P["baseline"], lw=1.6,
             label="Q3 不收缩（57.4647 h）")
    ax2.plot(t4 / 3600.0, np.nanmax(C4, axis=1), color=P["primary"], lw=1.6,
             label="Q4 收缩（52.6361 h）")
    ax2.axhline(0.15, color=P["criterion"], lw=1.0, ls="--")
    ax2.axvline(57.4647, color=P["baseline"], lw=0.8, ls=":")
    ax2.axvline(52.6361, color=P["primary"], lw=0.8, ls=":")
    ax2.annotate("", xy=(52.6361, 0.95), xytext=(57.4647, 0.95),
                 arrowprops=dict(arrowstyle="<->", color=P["negative"], lw=1.0))
    ax2.text(55.0, 0.72, "变化 -4.83 h\n(-8.4%)", fontsize=7, color=P["negative"], ha="center",
             va="top", bbox=dict(facecolor="white", edgecolor="none", pad=1.0))
    ax2.set_xlabel("t / h"); ax2.set_ylabel("max $\\mathbf{C}$ / (kg/kg)")
    ax2.set_title("收缩使烘干提前")
    ax2.set_ylim(0, 2.75)
    ax2.legend(fontsize=7.2, loc="upper right")
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.plot(t3 / 3600.0, C3[:, -1], color=P["baseline"], lw=1.6, label="Q3 表面 (r = 2.0 cm)")
    surf4 = C4[:, -1]
    ax3.plot(t4 / 3600.0, surf4, color=P["primary"], lw=1.6, label="Q4 表面 (r = R(t))")
    ax3.set_xlabel("t / h"); ax3.set_ylabel("C / (kg/kg)")
    ax3.set_title("表面含水率对比")
    ax3.legend(fontsize=7.2)
    for ax_, lab in zip([ax, ax2, ax3], "abc"):
        panel_label(ax_, lab)
    finish(fig, "fig04_shrinkage_effect",
           {"data": ["workspace/data_clean/attachment2_radius.csv",
                     "results/Q3/experiments/round1/result3.xlsx",
                     "results/Q4/experiments/round1/result4.xlsx"],
            "claims": ["q4_drying_time_hours", "q4_R_at_drying_end_cm", "q4_shrinkage_percent",
                       "q4_vs_q3_drying_time_hours", "q3_drying_time"]},
           DEFAULT_CHECKS)


# ---------------------------------------------------------------- figure 5
def fig05():
    Q = ["Q1", "Q2", "Q3", "Q4"]
    mv = {q: load_json("results/%s/experiments/round1/metrics/main_validation.json" % q) for q in Q}
    vv = {q: load_json("results/%s/experiments/round1/metrics/verifier_validation.json" % q) for q in Q}
    grid = [mv["Q1"]["grid_refinement"]["max_abs_diff_400_vs_800"],
            mv["Q2"]["grid_refinement_6h"]["max_abs_diff_C"],
            mv["Q3"]["grid_refinement_6h"]["max_abs_diff_C"],
            mv["Q4"]["grid_refinement_6h"]["max_abs_diff_C"]]
    ana = [mv["Q1"]["analytical_cross_check"]["max_abs_err"],
           vv["Q2"]["reference_vs_analytical"]["max_abs_err"],
           vv["Q3"]["reference_vs_analytical"]["max_abs_err"],
           vv["Q4"]["reference_vs_analytical"]["max_abs_err"]]
    xdiff = [vv["Q1"]["main_vs_baseline_real_problem"]["max_abs_diff_moisture"],
             vv["Q2"]["main_vs_baseline_tables"]["max_abs_diff_moisture"],
             vv["Q3"]["main_vs_baseline_table5"]["max_abs_diff"],
             vv["Q4"]["main_vs_baseline_table6"]["max_abs_diff"]]
    # 2x2 instead of 1x4: four panels side by side left every panel about 1.7 in
    # wide once the figure is scaled into the text block, which is what made the
    # tick labels and annotations unreadable.
    fig = plt.figure(figsize=(7.4, 5.3))
    gs = fig.add_gridspec(2, 2, wspace=0.30, hspace=0.46)
    ax = fig.add_subplot(gs[0, 0])
    x = np.arange(len(Q))
    ax.bar(x - 0.19, grid, width=0.34, color=P["primary"], edgecolor="black", lw=0.5, hatch="///",
           label="网格加密")
    ax.bar(x + 0.19, ana, width=0.34, color=P["accent1"], edgecolor="black", lw=0.5, hatch="...",
           label="解析对照")
    ax.axhline(5e-5, color=P["criterion"], lw=0.9, ls="--")
    ax.set_yscale("log"); ax.set_xticks(x); ax.set_xticklabels(Q)
    ax.set_ylabel("最大绝对差 / (kg/kg)")
    ax.set_title("离散残差与解析对照残差")
    ax.set_ylim(3e-7, 4e-4)
    ax.legend(fontsize=8.0, loc="upper left", ncol=2, columnspacing=1.0, handlelength=1.6)
    ax.text(3.42, 6.4e-5, "容差 $5\\times10^{-5}$", fontsize=8.6, color=P["criterion"],
            ha="right", va="bottom")

    ax2 = fig.add_subplot(gs[0, 1])
    bc = bessel()
    ref = np.array(load_json("results/Q4/experiments/round1/metrics/main.json")["reference_case"]["C_at_6h"])
    rr = np.linspace(0, 0.02, 200)
    ax2.plot(rr * 100, bc(rr, 21600.0, 1e-9, 8e-7, cinit=2.55, cinf=0.05),
             color=P["baseline"], lw=1.4, label="Bessel 解析")
    ax2.plot([0, 0.5, 1.0, 1.5, 2.0], ref, color=P["primary"], lw=1.4, marker="o",
             ms=4, ls="none", label="主方法")
    ax2.set_xlabel("r / cm"); ax2.set_ylabel("C / (kg/kg)")
    ax2.set_title("冻结半径算例与 Bessel 解析解")
    ax2.set_ylim(0.0, 3.05)
    ax2.legend(fontsize=8.0, loc="upper right")

    ax3 = fig.add_subplot(gs[1, 0])
    # Q2's two implementations agree to 0.0 at the reported precision, which cannot be
    # drawn on a log axis: draw a floor bar and label the true value
    floor = 5e-7
    heights = [max(v, floor) for v in xdiff]
    ax3.bar(x, heights, width=0.55, color=P["accent3"], edgecolor="black", lw=0.5, hatch="///")
    ax3.axhline(1e-4, color=P["criterion"], lw=0.9, ls="--")
    ax3.set_yscale("log"); ax3.set_xticks(x); ax3.set_xticklabels(Q)
    ax3.set_ylim(1.5e-7, 6e-3)
    ax3.set_ylabel("逐点最大差 / (kg/kg)")
    for xi, v, h in zip(x, xdiff, heights):
        ax3.text(xi, h * 1.5, ("0" if v == 0 else "%.0e" % v), fontsize=8.6, ha="center")
    ax3.set_title("主方法与独立实现对比\n（虚线 = 1 个末位单位）", fontsize=9.5)

    ax4 = fig.add_subplot(gs[1, 1])
    dev = [mv["Q4"]["moving_boundary_invariance"]["observed_max_abs_deviation_of_C_from_C0"],
           load_json("results/Q4/experiments/round1/metrics/baseline_validation.json")
           ["moving_boundary_invariance"]["observed_max_abs_deviation_of_C_from_C0"]]
    ax4.bar([0, 1], dev, width=0.5, color=[P["primary"], P["baseline"]], hatch="///",
            edgecolor="black", lw=0.5)
    ax4.axhline(1e-8, color=P["criterion"], lw=0.9, ls="--")
    ax4.set_yscale("log"); ax4.set_xticks([0, 1]); ax4.set_xticklabels(["主方法", "基线"])
    ax4.set_ylabel("$\\max|C-C_0|$ / (kg/kg)")
    ax4.set_title("移动边界一致性")
    ax4.set_ylim(1e-14, 4e-7)
    ax4.text(0.60, 2.2e-9, "阈值 $10^{-8}$", fontsize=8.6, color=P["criterion"],
             ha="center", va="center")
    # a log-axis offset text ("0e+00") is positioned outside the tight bbox; the
    # mathtext log formatter prints the exponent in every label, so no offset is needed
    from matplotlib.ticker import LogFormatterMathtext
    for ax_ in fig.get_axes():
        if ax_.get_yscale() == "log":
            ax_.yaxis.set_major_formatter(LogFormatterMathtext())
        ax_.yaxis.get_offset_text().set_visible(False)
        ax_.xaxis.get_offset_text().set_visible(False)
    for ax_, lab in zip([ax, ax2, ax3, ax4], "abcd"):
        panel_label(ax_, lab, dx=-0.22, dy=1.10)
    finish(fig, "fig05_numerical_verification",
           {"data": ["results/Q*/experiments/round1/metrics/main_validation.json",
                     "results/Q*/experiments/round1/metrics/verifier_validation.json",
                     "results/Q*/experiments/round1/metrics/baseline_validation.json"],
            "claims": ["q1_analytical_max_abs_err", "q2_analytical_max_abs_err",
                       "q3_analytical_max_abs_err", "q4_reference_max_abs_err",
                       "q1_grid_refinement_diff", "q2_grid_refinement_diff",
                       "q3_grid_refinement_diff", "q4_grid_refinement_diff",
                       "q1_independent_implementations_diff", "q4_moving_boundary_dev"]},
           DEFAULT_CHECKS)


# ---------------------------------------------------------------- figure 6
def fig06():
    # 9.4 x 3.6 in was a 2.6:1 strip: scaled to the text width its height collapsed
    # to about 6 cm and the 6.4 pt labels ended up near 4 pt. The chart is now a
    # 1.5:1 block with ~9 pt type, and the two wide bands are split onto two lines
    # so they no longer have to shrink to fit.
    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 6.6)

    drawn = []                      # (x, y, w, h, text artist) for the fit check below

    def box(x, y, w, h, text, fc, fs=8.6, ec="black"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06,rounding_size=0.08",
                                    facecolor=fc, edgecolor=ec, lw=0.8))
        t = ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                    linespacing=1.35)
        drawn.append((x, y, w, h, text, t))

    def arrow(x1, y1, x2, y2, col="black", ls="-", lw=0.9):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=lw, ls=ls,
                                    shrinkA=1, shrinkB=1))

    CENTERS = (1.310, 3.770, 6.230, 8.690)
    EDGES = (0.140, 2.600, 5.060, 7.520)
    WQ = 2.34

    box(1.20, 5.85, 7.60, 0.62, "G1 口径：一维径向轴对称 · Fick 标准形式 · 环境与对流系数",
        P["neutral_light"], 8.8)
    box(2.50, 4.82, 5.00, 0.76, "控制方程骨架\n轴对称热传导与水分扩散（双向耦合）",
        P["primary_pale"], 9.2)
    arrow(5.0, 5.85, 5.0, 5.62)
    arrow(5.0, 4.82, 5.0, 4.52)
    ax.plot([CENTERS[0], CENTERS[3]], [4.52, 4.52], color="black", lw=0.9)
    for xc in CENTERS:
        arrow(xc, 4.52, xc, 4.06)

    # every line must fit inside WQ at fs: the previous 9 pt text overflowed the
    # box and ran into the neighbouring branch box
    qtext = [
        "问题一\n预热段 0–1800 s\n附录 2 物性\n顶点有限体积+BDF",
        "问题二\n恒温干燥全过程\n附录 3 物性\n顶点有限体积+二阶隐式",
        "问题三\n烘干时长\n附录 3 物性（同题二）\n顶点有限体积+二阶隐式",
        "问题四\n收缩域\n附录 4 物性\n归一化坐标+表观对流项",
    ]
    for xe, txt in zip(EDGES, qtext):
        box(xe, 2.60, WQ, 1.46, txt, P["primary_pale"], 8.4)
    for xc in CENTERS:
        arrow(xc, 2.60, xc, 2.18)

    box(0.140, 1.28, 9.72, 0.90,
        "三角色互不共享数值输入\n主方法（顶点有限体积）｜可用基线（格心／不同时间推进）｜独立验证（Bessel 半解析＋契约不变量）",
        P["neutral_light"], 8.6)
    arrow(5.0, 1.28, 5.0, 1.06)
    box(0.140, 0.16, 9.72, 0.90,
        "验证闭环\n解析对照 · 网格与时间加密 · 独立实现交叉验证 · 移动边界一致性 · 参数与口径敏感性",
        P["accent3"], 8.6)
    # A schematic's failure mode is caption text spilling out of its own box, which
    # neither the measured audit (text-vs-text only) nor a visual glance reliably
    # catches. Measure it here and record the worst slack in the render evidence.
    fig.canvas.draw()
    rr = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    worst = 0.0
    for (x, y, w, h, txt, t) in drawn:
        bb = t.get_window_extent(renderer=rr)
        (x0, y0) = inv.transform((bb.x0, bb.y0))
        (x1, y1) = inv.transform((bb.x1, bb.y1))
        worst = max(worst, x1 - (x + w), x - x0, y1 - (y + h), y - y0)
    unit_pt = 72.0 * fig.get_size_inches()[0] / 10.0          # 1 data-x unit in points
    fit = "text fits inside every box (worst overflow %.2f pt)" % (worst * unit_pt)
    assert worst <= 0.0, fit
    finish(fig, "fig06_method_and_roles",
           {"data": ["methods/Q1/q1_method_card.md", "methods/Q2/q2_method_card.md",
                     "methods/Q3/q3_method_card.md", "methods/Q4/q4_method_card.md",
                     "methods/*/q*_decisions.jsonl"],
            "claims": ["four-question method chain and role separation"]},
           DEFAULT_CHECKS + ["schematic figure: axes hidden, no data plotted", fit])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    apply_style()
    fig01(); fig02(); fig03(); fig04(); fig05(); fig06()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())