# -*- coding: utf-8 -*-
"""Generate the six paper figures (Type 3) into paper/figures/ with render evidence."""
from __future__ import annotations
import csv, importlib.util, json, sys
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrow, FancyBboxPatch, Rectangle, Patch
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator, FuncFormatter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figure_style import (ROOT, PALETTE, apply_style, finish, panel_label, DEFAULT_CHECKS,
                           CMAP_TEMP, CMAP_MOIST)

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


# ------------------------------------------------------- figure 0 (method schematic)
def fig_mesh():
    """顶点型有限体积离散示意：单幅图，左侧截面取样行经箭头放大为右侧节点/控制体排布。

    未知量放在原始网格节点上（顶点法）；若放在单元中心则为格心法。
    网格尺寸取正文关键数据：R = 2.0 cm、N = 800，故 Δr = 25 μm。示意图内不出现公式，
    两种交换只以色箭头标示，含义由图注说明。
    """
    fig = plt.figure(figsize=(7.4, 3.4))
    ax = fig.add_subplot(111)
    ax.set_aspect("equal")
    ax.axis("off")
    HEAT, MOIST, WARM = "#E8A0A0", "#1B3A6B", "#D98324"
    R = 1.45

    # ---- 圆柱截面：取样行贯穿整个直径 ----
    ax.add_patch(Circle((0, 0), R, facecolor=P["primary_pale"], edgecolor=P["primary"],
                        lw=1.3, zorder=1))
    ncell = 10
    xs = np.linspace(-R, R, ncell + 1)
    for i in range(ncell):
        ax.add_patch(Rectangle((xs[i], -0.13), xs[i + 1] - xs[i], 0.26,
                               facecolor="white", edgecolor="black", lw=0.5, zorder=3))
    ax.plot(xs, np.zeros(ncell + 1), "k.", ms=3.4, zorder=4)
    ax.add_patch(Rectangle((-R - 0.12, -0.27), 2 * R + 0.24, 0.54, fill=False,
                           edgecolor="black", lw=1.2, ls=(0, (4, 2)), zorder=6))

    # ---- 圆周外两组箭头交替排布 ----
    for k, ang in enumerate(np.linspace(0, 360, 12, endpoint=False)):
        th = np.deg2rad(ang)
        ux, uy = np.cos(th), np.sin(th)
        if k % 2 == 0:
            ax.annotate("", xy=(1.06 * R * ux, 1.06 * R * uy),
                        xytext=(1.44 * R * ux, 1.44 * R * uy),
                        arrowprops=dict(arrowstyle="-|>", color=HEAT, lw=1.5))
        else:
            ax.annotate("", xy=(1.44 * R * ux, 1.44 * R * uy),
                        xytext=(1.06 * R * ux, 1.06 * R * uy),
                        arrowprops=dict(arrowstyle="-|>", color=MOIST, lw=1.5))

    # ---- 图例：文字保留，只把“浅红向内/深蓝向外”换成对应颜色的箭头 ----
    ax.annotate("", xy=(-0.85, -2.62), xytext=(-2.15, -2.62),
                arrowprops=dict(arrowstyle="-|>", color=HEAT, lw=1.8))
    ax.text(-0.70, -2.62, "：与热风的热量交换", ha="left", va="center", fontsize=9.5,
            color="#C0504D")
    ax.annotate("", xy=(-0.85, -3.22), xytext=(-2.15, -3.22),
                arrowprops=dict(arrowstyle="-|>", color=MOIST, lw=1.8))
    ax.text(-0.70, -3.22, "：水分交换", ha="left", va="center", fontsize=9.5, color=MOIST)

    # ---- 从虚线框出发的放大箭头 ----
    ax.annotate("", xy=(4.30, 0.0), xytext=(R + 0.18, 0.0),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.6))

    # ---- 放大后的节点与对偶控制体：格宽加大，CV 字样完整落在格内 ----
    nodes = 4.80 + np.arange(7) * 2.35
    Rr = float(nodes[-1])
    faces = np.concatenate([[nodes[0]], (nodes[:-1] + nodes[1:]) / 2.0, [Rr]])
    names = ["", "CV$_1$", "CV$_2$", "CV$_i$", "CV$_{i+1}$", "CV$_{N-1}$", ""]
    for j in range(7):
        lo, hi = float(faces[j]), float(faces[j + 1])
        ax.add_patch(Rectangle((lo, -0.52), hi - lo, 1.04,
                               facecolor=P["primary_pale"] if j % 2 == 0 else "#DCE9F7",
                               edgecolor="black", lw=0.7, zorder=2))
        if names[j]:
            ax.text((lo + hi) / 2.0, -0.26, names[j], ha="center", va="center", fontsize=9.5,
                    zorder=5)
    ax.plot([float(nodes[0]), Rr], [0.24, 0.24], color="black", lw=0.9, zorder=3)
    ax.plot(nodes, np.full(7, 0.24), "o", color=P["primary"], ms=5.0, zorder=6)
    for fx, lab in ((float(nodes[3]), "$F_{i-1/2}$"), (float(nodes[4]), "$\mathbf{F}_{i+1/2}$")):
        ax.annotate("", xy=(fx + 0.36, 0.92), xytext=(fx - 0.36, 0.92),
                    arrowprops=dict(arrowstyle="-|>", color="black", lw=1.1))
        ax.text(fx, 1.06, lab, ha="center", va="bottom", fontsize=9.5)

    # ---- Δr 只需一处标注 ----
    ax.annotate("", xy=(float(nodes[2]), -0.86), xytext=(float(nodes[1]), -0.86),
                arrowprops=dict(arrowstyle="<->", color="black", lw=0.9))
    ax.text(float(nodes[1]) + 1.0, -0.84, "$\\Delta \mathbf{r}$ = 25 μm", ha="center", va="top",
            fontsize=9.5)

    # ---- 端点用箭头指认 ----
    ax.annotate("中心 $\mathbf{r}=0$", xy=(float(nodes[0]), -0.54), xytext=(float(nodes[0]) - 0.10, -1.75),
                ha="center", va="top", fontsize=9.5,
                arrowprops=dict(arrowstyle="->", lw=0.9, color="black"))
    ax.annotate("表面 $\mathbf{r}=\mathbf{R}$", xy=(Rr, -0.54), xytext=(Rr + 1.20, -1.75),
                ha="center", va="top", fontsize=9.5,
                arrowprops=dict(arrowstyle="->", lw=0.9, color="black"))

    # ---- 表面外侧用波浪线表示热风 ----
    ax.plot([Rr + 0.10, Rr + 0.10], [-1.55, 1.55], color=WARM, lw=1.6, zorder=4)
    yv = np.linspace(-1.55, 1.55, 160)
    for k in range(4):
        xw = Rr + 0.34 + k * 0.36
        ax.plot(xw + 0.11 * np.sin(yv * 5.0 + k * 1.1), yv, color=WARM, lw=1.0, zorder=4)
    ax.text((float(nodes[3]) + float(nodes[4])) / 2.0, 1.95,
            "节点在 $\mathbf{r}_j$，通量只在界面 $\mathbf{r}_{j\\pm 1/2}$ 上出现",
            ha="center", va="center", fontsize=9.5)
    ax.set_xlim(-2.35, Rr + 2.15)
    ax.set_ylim(-3.95, 2.35)
    finish(fig, "fig00_mesh_schematic",
           {"data": ["planning/symbol_table.md", "paper/sections/05_model_and_solution.tex"],
            "claims": ["vertex-centred finite-volume layout; unknowns sit on the nodes; R = 2.0 cm and N = 800 give dr = 25 um"]},
           DEFAULT_CHECKS + ["schematic figure: axes hidden, no data plotted"])

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
    ax.text(0.62, 0.09, "r", fontsize=9.5, fontweight="bold")
    ax.text(0.05, -0.14, "r = 0\n对称", fontsize=8.4, ha="left", va="top")
    for ang in np.linspace(-70, 70, 5):
        a = np.deg2rad(ang)
        ax.add_patch(FancyArrow(1.02 * np.cos(a), 1.02 * np.sin(a),
                                0.30 * np.cos(a), 0.30 * np.sin(a),
                                width=0.008, head_width=0.06, head_length=0.09,
                                color=P["primary"], length_includes_head=True))
    # No equations in the schematic: the Robin conditions are derived in the text
    # and a two-line formula block here only duplicated them at an unreadable size.
    ax.text(1.05, 1.16, "r = R(t)：第三类对流边界\n（表面对流换热与传质）",
            fontsize=10.0, ha="center", va="bottom")
    # split onto two lines: as one line it was wider than the disc and hugged the
    # panel edge once bbox_inches="tight" cropped the canvas
    ax.text(0.0, -1.22, "R(t)：2.000 cm $\\rightarrow$ 1.198 cm\n（收缩 40.1%）", fontsize=9.6,
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
    ax2.set_xlabel(r"$\mathbf{t}$ / $\mathbf{h}$"); ax2.set_ylabel(r"$\mathbf{T_\infty}$ / $\mathbf{^\circ C}$")

    ax2.axvline(4.0, color=P["neutral_mid"], lw=0.8, ls=":")
    ax2.text(4.15, 33, "14400 s", fontsize=8.6)
    ax3 = ax2.twinx()
    ax3.plot(te / 3600.0, ci, color=P["primary"], lw=1.6, label="$C_\\infty$ 实测（附件1）")
    ax3.plot(txt / 3600.0, ci_x, color=P["primary"], lw=1.1, ls="--",
             label="$C_\\infty$ 外推口径（0.05 kg/kg）")
    ax3.set_ylabel(r"$\mathbf{C_\infty}$ / ($\mathbf{kg/kg}$)")

    h1, l1 = ax2.get_legend_handles_labels(); h2, l2 = ax3.get_legend_handles_labels()
    ax2.legend(h1 + h2, l1 + l2, loc="center right", fontsize=8.2)
    ax2.set_title("环境温度")
    panel_label(ax2, "b")
    finish(fig, "fig01_model_setup_and_environment",
           {"env": "workspace/data_clean/attachment1_env.csv",
            "radius": "workspace/data_clean/attachment2_radius.csv",
            "decisions": ["g_framing_env_extrapolation", "g_framing_spatial_dimension"]},
           DEFAULT_CHECKS + ["schematic axes hidden; schematic is not data-bearing"])


# ---------------------------------------------------------------- figure 2
_T_LAB = r"$\mathbf{T}$ / $\mathbf{^\circ C}$"
_C_LAB = r"$\mathbf{C}$ / ($\mathbf{kg/kg}$)"
_R_LAB = r"$\mathbf{r}$ / $\mathbf{cm}$"
_T_MIN_LAB = r"$\mathbf{t}$ / $\mathbf{min}$"


def _surf_axes(fig, spec):
    """3D panel: no gridlines, no pane fill, all axes and ticks black."""
    ax = fig.add_subplot(spec, projection="3d")
    ax.grid(False)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        # pane.fill=False drops the pane outline in this matplotlib version, which
        # leaves the box open on the left; a white pane with a black outline keeps
        # the background unchanged while drawing the complete box
        axis.pane.fill = True
        axis.pane.set_facecolor("white")
        axis.pane.set_edgecolor("none")     # the frame is drawn once, by _box()
        # hide matplotlib's own axis line: it sits a hair off the data limits and
        # showed up as a second line running parallel to the box edge. Tick marks are
        # separate artists and stay, landing exactly on the box edge drawn by _box().
        axis.line.set_color("none")
        axis.line.set_linewidth(0.7)
        axis.set_major_locator(MaxNLocator(4))
    ax.tick_params(labelsize=8.5, pad=-2, colors="black")
    # the radius span (2 cm) is far shorter than the time span (30 min); without a
    # stretched box the surface degenerates into an unreadable ribbon
    ax.set_box_aspect((1.0, 1.45, 0.95))
    ax.view_init(elev=26, azim=-62)
    return ax


def _box(ax):
    """Draw the complete 12-edge box.

    matplotlib only strokes the pane outlines, which leaves the box open; the missing
    edges are added here so the axes read as a closed frame.
    """
    xs, ys, zs = sorted(ax.get_xlim()), sorted(ax.get_ylim()), sorted(ax.get_zlim())
    (x0, x1), (y0, y1), (z0, z1) = xs, ys, zs
    # The three edges meeting at the far corner (x0, y1, z0) lie behind everything the
    # view ray passes through, so they are left out: drawing them puts spurious lines
    # across the plot area.
    near = (x1, y0, z1)
    segs = []
    for y in (y0, y1):
        for z in (z0, z1):
            segs.append(((x0, y, z), (x1, y, z)))
    for x in (x0, x1):
        for z in (z0, z1):
            segs.append(((x, y0, z), (x, y1, z)))
    for x in (x0, x1):
        for y in (y0, y1):
            segs.append(((x, y, z0), (x, y, z1)))
    for a, b in segs:
        if (abs(a[0] - near[0]) < 1e-9 and abs(a[1] - near[1]) < 1e-9 and abs(a[2] - near[2]) < 1e-9) or \
           (abs(b[0] - near[0]) < 1e-9 and abs(b[1] - near[1]) < 1e-9 and abs(b[2] - near[2]) < 1e-9):
            continue
        ax.plot(*zip(a, b), color="black", lw=0.6)


def _disc(ax, cx, rad, knots_r, knots_v, cm, norm):
    """One circular cross section: colour at radius rho is the value at r = rho*R."""
    n = 600
    yy, xx = np.mgrid[-1:1:complex(n), -1:1:complex(n)]
    rho = np.sqrt(xx ** 2 + yy ** 2)
    vals = np.interp(rho * knots_r[-1], knots_r, knots_v, right=np.nan)
    vals = np.where(rho <= 1.0, vals, np.nan)
    im = ax.imshow(vals, extent=(cx - rad, cx + rad, -rad, rad), origin="lower",
                   cmap=cm, norm=norm, interpolation="bilinear", zorder=2)
    # Clip the raster to the exact circle: masking on the pixel grid alone leaves a
    # jagged rim and visible blocks, and a coarser mask also leaves gaps at the edge.
    edge = Circle((cx, 0), rad, fill=False, edgecolor="black", lw=0.7, zorder=3)
    ax.add_patch(edge)
    im.set_clip_path(edge)


def fig02():
    """预热阶段温度与水分场：三维面图 + 关键时刻的截面圆盘。

    (a)(b) 为 T(r,t) 与 C(r,t) 的三维面图，颜色即该量本身；
    (c)(d) 把七个关键时刻的径向截面画成圆盘——盘心到盘缘对应 r = 0 到 R，
    相邻时刻之间用箭头标出经过的分钟数。
    """
    rowsT = read_sheet("results/Q1/experiments/round1/result1.xlsx", "温度")
    rowsC = read_sheet("results/Q1/experiments/round1/result1.xlsx", "水分浓度")
    t, T = to_array(rowsT)
    _, C = to_array(rowsC)
    with (ROOT / "workspace/data_clean/attachment2_radius.csv").open(encoding="utf-8") as fh:
        b = np.array([[float(x) for x in r] for r in list(csv.reader(fh))[1:]])
    Rf = PchipInterpolator(b[:, 0], b[:, 1])
    times = [100, 300, 600, 900, 1200, 1500, 1800]
    idx = [int(np.where(t == v)[0][0]) for v in times]
    cmT, cmC = CMAP_TEMP, CMAP_MOIST

    fig = plt.figure(figsize=(7.4, 7.8))
    # 圆盘两排用等比例坐标，绘图区会被压扁并在格内居中留白；
    # 把两排的格子高度压到贴合内容，两排才会真正靠拢
    gs = fig.add_gridspec(3, 2, height_ratios=[2.05, 0.72, 0.72],
                          hspace=0.02, wspace=0.26,
                          left=0.075, right=0.905, top=0.985, bottom=0.03)

    # ---- (a)(b) 三维面图（去掉面片网格线，只留颜色） ----
    # 重采样到细网格：原来的 60x21 采样会让曲面边缘出现阶梯状刻面
    tt_f = np.linspace(float(t[0]), float(t[-1]), 240)
    rr_f = np.linspace(0.0, 2.0, 101)
    Rg, Tg = np.meshgrid(rr_f, tt_f / 60.0)
    for k, (mat, cm, zl, tag) in enumerate(((T, cmT, _T_LAB, "a"),
                                            (C, cmC, _C_LAB, "b"))):
        ax = _surf_axes(fig, gs[0, k])
        Zt = np.column_stack([np.interp(tt_f, t, mat[:, j]) for j in range(mat.shape[1])])
        Z = np.vstack([np.interp(rr_f, R_COLS_CM, Zt[i]) for i in range(Zt.shape[0])])
        # rasterized=True is what actually removes the mesh: the seams only appear in
        # the vector PDF, where every quad is stroked independently, and are invisible
        # in the PNG. The surface is embedded as a 400 dpi raster instead.
        s = ax.plot_surface(Rg, Tg, Z, cmap=cm, linewidth=0, antialiased=False,
                            shade=False, edgecolor="none", rasterized=True,
                            rcount=Z.shape[0], ccount=Z.shape[1])
        ax.set_xlim(0, 2)
        ax.set_ylim(0, 30)
        # 时间轴的 0 与距离轴的终点重合，删掉这个刻度标注
        ax.yaxis.set_major_formatter(
            FuncFormatter(lambda v, _p: "" if abs(v) < 1e-9 else "%g" % v))
        _box(ax)
        # built-in 3D axis titles: matplotlib centres each one alongside its own
        # axis, which hand-placed text2D cannot do
        ax.set_xlabel(_R_LAB, fontsize=9.5, labelpad=-2)
        ax.set_ylabel(_T_MIN_LAB, fontsize=9.5, labelpad=-2)
        cb = fig.colorbar(s, ax=ax, shrink=0.62, aspect=13, pad=0.05)
        cb.set_label(zl, fontsize=9.5)
        cb.ax.tick_params(labelsize=8.5)
        cb.outline.set_linewidth(0.5)

    # ---- (c)(d) 关键时刻的截面圆盘 ----
    xstep, rad = 1.35, 0.45
    for k, (mat, cm, zl, tag) in enumerate(((T, cmT, _T_LAB, "c"),
                                            (C, cmC, _C_LAB, "d"))):
        ax = fig.add_subplot(gs[1 + k, :])
        ax.set_aspect("equal")
        ax.axis("off")
        last = (k == 1)          # 上下两排的时间点相同，只在下面一排标一次
        shown = np.concatenate([mat[i][~np.isnan(mat[i])] for i in idx])
        norm = plt.Normalize(float(shown.min()), float(shown.max()))
        for j, i in enumerate(idx):
            row = mat[i]
            knots_r = np.append(R_COLS_CM[:20], float(Rf(min(float(t[i]), b[-1, 0]))))
            knots_v = np.append(row[:20], row[-1])
            cx = j * xstep
            _disc(ax, cx, rad, knots_r, knots_v, cm, norm)
            if last:
                ax.text(cx, -rad - 0.16, "%d s" % int(t[i]), ha="center", va="top",
                    fontsize=8.5)
            if j < len(idx) - 1:
                ax.annotate("", xy=(cx + xstep - rad - 0.06, 0),
                            xytext=(cx + rad + 0.06, 0),
                            arrowprops=dict(arrowstyle="-|>", color="black", lw=0.9,
                                            shrinkA=0, shrinkB=0))
        ax.set_xlim(-0.85, xstep * (len(idx) - 1) + 0.85)
        ax.set_ylim(-1.05, 1.05)
        if k == 0:
            smT = plt.cm.ScalarMappable(norm=norm, cmap=cm)
        else:
            smC = plt.cm.ScalarMappable(norm=norm, cmap=cm)
            # 两个色卡都放在右侧，并在右侧分左右并排
            for sm, x0, lab, side in ((smT, 0.906, _T_LAB, "left"),
                                      (smC, 0.968, _C_LAB, "right")):
                cax = fig.add_axes([x0, 0.075, 0.013, 0.275])
                cb = fig.colorbar(sm, cax=cax)
                cb.set_label(lab, fontsize=9.5)
                # 两个色卡并排时标签分别朝外，避免互相压字
                cb.ax.yaxis.set_label_position(side)
                cb.ax.yaxis.set_ticks_position(side)
                cb.ax.tick_params(labelsize=8.5)
                cb.outline.set_linewidth(0.5)

    finish(fig, "fig02_preheat_fields",
           {"data": "results/Q1/experiments/round1/result1.xlsx",
            "claims": ["q1_T_center_1800s", "q1_T_surface_1800s", "q1_C_center_1800s",
                       "q1_C_surface_1800s"],
            "grid": "1800 rows x 21 columns (1 s x 0.1 cm)"},
           DEFAULT_CHECKS)

# ---------------------------------------------------------------- figure 3
def fig03():
    """长时程烘干：左为各位置含水率时程，右为参数敏感性。

    全域最大含水率随时间的变化与各位置时程是同一信息，故只保留后者。
    """
    t, C = to_array(read_sheet("results/Q3/experiments/round1/result3.xlsx"))
    th = t / 3600.0
    tdry = load_json("results/Q3/experiments/round1/metrics/main.json")["drying_time_hours"]
    fig = plt.figure(figsize=(7.4, 2.9))
    # 右侧的 y 轴类别标签较长，wspace 太小会顶进左图
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.08], wspace=0.55)
    ax2 = fig.add_subplot(gs[0, 0])
    ax2.plot(th, C[:, 0], color=P["primary"], lw=1.5, label="中心")
    ax2.plot(th, C[:, 10], color=P["accent1"], lw=1.5, ls="-.", label=r"$\mathbf{r}$ = 1.0 cm")
    ax2.plot(th, C[:, -1], color=P["negative"], lw=1.5, ls="--", label="表面")
    ax2.axhline(0.15, color=P["criterion"], lw=1.0, ls="--")
    ax2.axvline(tdry, color=P["negative"], lw=0.9, ls=":")
    ax2.annotate("%.4f h" % tdry, xy=(tdry, 1.35), xytext=(tdry - 24, 1.75), fontsize=9.0,
                 color=P["negative"],
                 arrowprops=dict(arrowstyle="->", color=P["negative"], lw=0.8))
    ax2.set_xlabel(r"$\mathbf{t}$ / $\mathbf{h}$")
    ax2.set_ylabel(r"$\mathbf{C}$ / ($\mathbf{kg/kg}$)")
    ax2.set_title("含水率时程")
    ax2.set_ylim(0, 2.75)
    ax2.legend(fontsize=9.0)

    ax3 = fig.add_subplot(gs[0, 1])
    rv = load_json("robustness/Q3/q3_robustness_summary.json")["checks"]
    base = 57.46472222222222
    items = [(r"$\mathbf{h_m}$ ±5%", [rv["h_m_perturbation"]["minus5pct"]["observed"]["t_dry_shift_hours"],
                                       rv["h_m_perturbation"]["plus5pct"]["observed"]["t_dry_shift_hours"]]),
             (r"$\mathbf{C_\infty}$ ±0.005", [rv["env_extrapolation_c_inf_0.045"]["observed"]["t_dry_shift_hours"],
                                               rv["env_extrapolation_c_inf_0.055"]["observed"]["t_dry_shift_hours"]]),
             (r"$\mathbf{D}$ +5%", [rv["D_perturbation"]["observed"]["t_dry_shift_hours"]]),
             (r"$\mathbf{T_\infty}$ = 52 °C", [rv["env_extrapolation_t_inf_52"]["observed"]["t_dry_shift_hours"]])]
    ypos = np.arange(len(items))[::-1]
    for y, (lab, vals) in zip(ypos, items):
        for k, v in enumerate(vals):
            off = 0.0 if len(vals) == 1 else (0.17 if k else -0.17)
            ax3.barh(y + off, 100 * v / base, height=(0.30 if len(vals) > 1 else 0.42),
                     color=P["positive"] if v > 0 else P["negative"], edgecolor="black", lw=0.5)
            ax3.text(100 * v / base + (0.16 if v > 0 else -0.16), y + off,
                     "%+.2f%%" % (100 * v / base), fontsize=8.5, va="center",
                     ha="left" if v > 0 else "right")
    ax3.axvline(0, color="k", lw=0.8)
    ax3.set_yticks(ypos)
    ax3.set_yticklabels([it[0] for it in items], fontsize=9.5)
    ax3.set_xlabel(r"烘干时长变化 / $\mathbf{\%}$")
    ax3.set_xlim(-8.6, 2.4)
    ax3.set_ylim(-0.6, len(items) - 0.4)
    ax3.set_title("敏感性")
    finish(fig, "fig03_drying_curve_and_sensitivity",
           {"data": "results/Q3/experiments/round1/result3.xlsx (Q2 shares the same model)",
            "robustness": "robustness/Q3/q3_robustness_summary.json",
            "claims": ["q2_drying_time", "q3_drying_time", "q2_sens_h_m_plus5pct",
                       "q2_sens_D_plus5pct", "q2_sens_T_inf_plus2C"]},
           DEFAULT_CHECKS)

# ---------------------------------------------------------------- figure 4
def fig04():
    """尺寸收缩效应：三幅合为一幅对照带图。

    上带为不考虑几何收缩（半径恒为 2.000 cm），下带为考虑收缩（半径收缩到 1.198 cm）。
    两条带各自在自己的烘干时长处被截断，截断时刻的表面含水率直接标在带上，
    两个截断时刻之差即收缩带来的烘干提前量。
    """
    env, rad = load_env()
    tr, rr = rad[:, 0], rad[:, 1]
    t3, C3 = to_array(read_sheet("results/Q3/experiments/round1/result3.xlsx"))
    t4, C4 = to_array(read_sheet("results/Q4/experiments/round1/result4.xlsx"))
    m4 = load_json("results/Q4/experiments/round1/metrics/main.json")
    t_q4 = float(m4["drying_time_hours"])
    t_q3 = 57.4647
    R_end = float(m4["radius"]["R_min_cm"])
    shrink = float(m4["radius"]["shrinkage_percent"])
    Rf = PchipInterpolator(tr, rr)
    surf3 = float(C3[-1, -1])
    surf4 = float(C4[-1, -1])
    gap_h = t_q3 - t_q4

    fig = plt.figure(figsize=(7.4, 3.0))
    ax = fig.add_subplot(111)
    UP, DN, HALF = 0.0, 0.0, 2.0   # 两条带重叠在同一中心线上

    # 上带：不考虑收缩，半径恒定
    ax.fill_between([0, t_q3], [UP - HALF] * 2, [UP + HALF] * 2,
                    color=P["baseline"], alpha=0.22, lw=0, zorder=1)
    ax.plot([0, t_q3], [UP + HALF] * 2, color=P["baseline"], lw=1.4, zorder=2)
    ax.plot([0, t_q3], [UP - HALF] * 2, color=P["baseline"], lw=1.4, zorder=2)
    ax.plot([t_q3, t_q3], [UP - HALF, UP + HALF], color=P["baseline"], lw=1.4, zorder=2)

    # 下带：考虑收缩，半径按附件 2 收缩
    th4 = np.linspace(0.0, t_q4, 300)
    Rt = Rf(np.minimum(th4 * 3600.0, tr[-1]))
    ax.fill_between(th4, DN - Rt, DN + Rt, color=P["primary"], alpha=0.20, lw=0, zorder=3)
    ax.plot(th4, DN + Rt, color=P["primary"], lw=1.5, zorder=4)
    ax.plot(th4, DN - Rt, color=P["primary"], lw=1.5, zorder=4)
    ax.plot([t_q4, t_q4], [DN - R_end, DN + R_end], color=P["primary"], lw=1.5, zorder=4)

    # 两条带的说明放在带外，避免压在色块边缘上

    # 两条带各自的截断时长与截断处的表面含水率：合并成两行写在带内，避免相互压字

    # 两个截断时刻之差 = 收缩带来的提前量
    ax.plot([t_q4, t_q4], [UP - 2.05, 3.90], color=P["primary"], lw=0.9, ls=":", zorder=2)
    ax.plot([t_q3, t_q3], [UP + 2.05, 3.90], color=P["baseline"], lw=0.9, ls=":", zorder=2)
    ax.annotate("", xy=(t_q4, 3.75), xytext=(t_q3, 3.75),
                arrowprops=dict(arrowstyle="<->", color=P["negative"], lw=1.2))
    ax.text(t_q4 - 1.5, 3.90, "收缩使烘干提前 -%.1f%%" % (100.0 * gap_h / t_q3),
            ha="right", va="bottom", fontsize=9.5, color=P["negative"])

    ax.set_xlabel(r"$\mathbf{t}$ / $\mathbf{h}$")
    ax.set_xlim(0, t_q3 * 1.06)
    ax.set_ylim(-2.85, 5.05)
    handles = [Patch(facecolor=P["baseline"], alpha=0.30, edgecolor=P["baseline"],
                     label=r"不考虑几何收缩，$\mathbf{R}$ = 2.000 cm 恒定"),
               Patch(facecolor=P["primary"], alpha=0.28, edgecolor=P["primary"],
                     label=r"考虑几何收缩，$\mathbf{R}$: 2.000 → %.3f cm" % R_end)]
    # 半径收缩百分比标在两条带边缘之间的空隙处
    ax.annotate("收缩 %.1f%%" % shrink, xy=(46.0, R_end), xytext=(29.0, 1.62),
                ha="center", va="center", fontsize=9.5, color=P["primary"],
                arrowprops=dict(arrowstyle="->", lw=0.9, color=P["primary"]))
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=2,
              frameon=False, fontsize=9.5)
    # 两条带都以 R 为半高，纵轴就是半径本身，故恢复刻度与轴名
    ax.set_yticks([-2, -1, 0, 1, 2])
    ax.set_ylabel(r"$\mathbf{R}$ / $\mathbf{cm}$")
    finish(fig, "fig04_shrinkage_effect",
           {"data": ["workspace/data_clean/attachment2_radius.csv",
                     "results/Q3/experiments/round1/result3.xlsx",
                     "results/Q4/experiments/round1/result4.xlsx"],
            "claims": ["q4_drying_time_hours", "q4_R_at_drying_end_cm", "q4_shrinkage_percent",
                       "q4_vs_q3_drying_time_hours", "q3_drying_time"]},
           DEFAULT_CHECKS)

# ---------------------------------------------------------------- figure 5
def fig05():
    Q = ["Q1", "Q2", "Q3", "Q4"]                 # metric-file keys (not shown)
    # 正文与图内一律用“问题一…四”，不用 Q 简写
    QLAB = ["问题一", "问题二", "问题三", "问题四"]
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
    ax.set_yscale("log"); ax.set_xticks(x); ax.set_xticklabels(QLAB)
    ax.set_ylabel(r"最大绝对差 / ($\mathbf{kg/kg}$)")
    ax.set_title("离散残差")
    ax.set_ylim(3e-7, 4e-4)
    ax.legend(fontsize=9.0, loc="upper left", ncol=2, columnspacing=1.0, handlelength=1.6)
    ax.text(3.42, 6.4e-5, "容差 $5\\times10^{-5}$", fontsize=9.6, color=P["criterion"],
            ha="right", va="bottom")

    ax2 = fig.add_subplot(gs[0, 1])
    bc = bessel()
    ref = np.array(load_json("results/Q4/experiments/round1/metrics/main.json")["reference_case"]["C_at_6h"])
    rr = np.linspace(0, 0.02, 200)
    ax2.plot(rr * 100, bc(rr, 21600.0, 1e-9, 8e-7, cinit=2.55, cinf=0.05),
             color=P["baseline"], lw=1.4, label="Bessel 解析")
    ax2.plot([0, 0.5, 1.0, 1.5, 2.0], ref, color=P["primary"], lw=1.4, marker="o",
             ms=4, ls="none", label="主方法")
    ax2.set_xlabel(r"$\mathbf{r}$ / $\mathbf{cm}$"); ax2.set_ylabel(r"$\mathbf{C}$ / ($\mathbf{kg/kg}$)")
    ax2.set_title("与解析解对照")
    ax2.set_ylim(0.0, 3.05)
    ax2.legend(fontsize=9.0, loc="upper right")

    ax3 = fig.add_subplot(gs[1, 0])
    # Q2's two implementations agree to 0.0 at the reported precision, which cannot be
    # drawn on a log axis: draw a floor bar and label the true value
    floor = 5e-7
    heights = [max(v, floor) for v in xdiff]
    ax3.bar(x, heights, width=0.55, color=P["accent3"], edgecolor="black", lw=0.5, hatch="///")
    ax3.axhline(1e-4, color=P["criterion"], lw=0.9, ls="--")
    ax3.set_yscale("log"); ax3.set_xticks(x); ax3.set_xticklabels(QLAB)
    ax3.set_ylim(1.5e-7, 6e-3)
    ax3.set_ylabel(r"逐点最大差 / ($\mathbf{kg/kg}$)")
    for xi, v, h in zip(x, xdiff, heights):
        ax3.text(xi, h * 1.5, ("0" if v == 0 else "%.0e" % v), fontsize=9.6, ha="center")
    ax3.set_title("主方法与独立实现")

    ax4 = fig.add_subplot(gs[1, 1])
    dev = [mv["Q4"]["moving_boundary_invariance"]["observed_max_abs_deviation_of_C_from_C0"],
           load_json("results/Q4/experiments/round1/metrics/baseline_validation.json")
           ["moving_boundary_invariance"]["observed_max_abs_deviation_of_C_from_C0"]]
    ax4.bar([0, 1], dev, width=0.5, color=[P["primary"], P["baseline"]], hatch="///",
            edgecolor="black", lw=0.5)
    ax4.axhline(1e-8, color=P["criterion"], lw=0.9, ls="--")
    ax4.set_yscale("log"); ax4.set_xticks([0, 1]); ax4.set_xticklabels(["主方法", "基线"])
    ax4.set_ylabel(r"$\max|\mathbf{C}-\mathbf{C}_0|$ / ($\mathbf{kg/kg}$)")
    ax4.set_title("移动边界")
    ax4.set_ylim(1e-14, 4e-7)
    ax4.text(0.60, 2.2e-9, "阈值 $10^{-8}$", fontsize=9.6, color=P["criterion"],
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
    fig_mesh(); fig01(); fig02(); fig03(); fig04(); fig05(); fig06()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())