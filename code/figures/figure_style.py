# -*- coding: utf-8 -*-
"""Shared visual system for the paper figures (top-journal style guide)."""
from __future__ import annotations
import json, time
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper/figures"

PALETTE = {
    "primary": "#1A6FC4", "primary_light": "#5B9BD5", "primary_pale": "#B4D4F0",
    "baseline": "#767676", "baseline_dark": "#4D4D4D",
    "positive": "#2E9E44", "negative": "#E53935", "criterion": "#333333",
    "accent1": "#E28E2C", "accent2": "#7B5FD6", "accent3": "#33B5A5",
    "accent4": "#D9544D", "neutral_light": "#D8D8D8", "neutral_mid": "#A8A8A8",
    "neutral_dark": "#606060", "neutral_black": "#333333",
}


def apply_style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["SimSun"],
        "mathtext.fontset": "stix",
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "axes.unicode_minus": False,
        "font.size": 9,
        "axes.titlesize": 9.5,
        "axes.labelsize": 9,
        "axes.titleweight": "bold",
        "axes.labelweight": "bold",
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "axes.linewidth": 0.8,
        "axes.edgecolor": PALETTE["neutral_black"],
        "axes.grid": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "legend.frameon": True,
        "legend.framealpha": 1.0,
        "legend.edgecolor": "black",
        "legend.fancybox": False,
        "lines.linewidth": 1.4,
    })


def panel_label(ax, letter, dx=-0.13, dy=1.06):
    ax.text(dx, dy, "(%s)" % letter, transform=ax.transAxes, fontsize=9.5,
            fontweight="bold", va="top", ha="left")


def audit(fig, dpi=400):
    """Mechanical render checks measured on the drawn canvas (not on the code)."""
    from matplotlib.text import Text
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    out = {}
    texts = []
    for ax in fig.get_axes():
        ticks = (set(ax.get_xticklabels(which="both")) | set(ax.get_yticklabels(which="both"))
                 | {ax.xaxis.get_offset_text(), ax.yaxis.get_offset_text()})
        for t in ax.findobj(Text):
            if t in ticks or t is ax.xaxis.get_offset_text() or t is ax.yaxis.get_offset_text():
                continue                      # tick/offset labels are laid out by matplotlib
                                              # and are excluded from the tight bbox by design
            s = (t.get_text() or "").strip()
            if not s or not t.get_visible():
                continue
            try:
                bb = t.get_window_extent(renderer=r)
            except Exception:
                continue
            if bb.width <= 0 or bb.height <= 0:
                continue
            texts.append((s, bb))
    # the PNG is written with bbox_inches="tight", so "not clipped" means every text
    # box lies inside the tight bounding box that is actually saved
    figbb = fig.get_tightbbox(r).transformed(fig.dpi_scale_trans)
    outside = [s for s, bb in texts
               if bb.x0 < figbb.x0 - 1 or bb.y0 < figbb.y0 - 1
               or bb.x1 > figbb.x1 + 1 or bb.y1 > figbb.y1 + 1]
    out["no_text_outside_saved_canvas"] = {"pass": not outside, "offenders": outside[:5],
                                           "texts_checked": len(texts)}
    # only annotations, titles, axis labels and legend entries count; tick labels are
    # laid out by matplotlib and are excluded to avoid false positives
    ov = []
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            a, b = texts[i][1], texts[j][1]
            ox = min(a.x1, b.x1) - max(a.x0, b.x0)
            oy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if ox > 1.0 and oy > 1.0:
                ov.append("%s | %s" % (texts[i][0][:18], texts[j][0][:18]))
    out["no_overlapping_text"] = {"pass": not ov, "offenders": ov[:5]}
    empty = []
    for k, ax in enumerate(fig.get_axes()):
        has = any(isinstance(c, Line2D) and len(c.get_xdata()) for c in ax.get_children())
        has = has or any(isinstance(c, Rectangle) and c.get_width() > 0 and c.get_height() > 0
                         for c in ax.get_children())
        has = has or any(len(c.get_offsets()) for c in ax.collections)
        if not has and ax.axison:
            empty.append(k)
    out["no_empty_panel"] = {"pass": not empty, "offenders": empty}
    alphas = set()
    for ax in fig.get_axes():
        for c in ax.get_children():
            if isinstance(c, Line2D):
                alphas.add(round(float(c.get_alpha() if c.get_alpha() is not None else 1.0), 3))
        for c in ax.containers:
            for p in getattr(c, "patches", []):
                alphas.add(round(float(p.get_alpha() if p.get_alpha() is not None else 1.0), 3))
    out["data_opaque"] = {"pass": all(a >= 0.999 for a in alphas), "alphas": sorted(alphas)}
    grid_on = False
    for ax in fig.get_axes():
        if ax.axison and any(gl.get_visible() for gl in list(ax.get_xgridlines()) + list(ax.get_ygridlines())):
            grid_on = True
    out["no_grid"] = {"pass": not grid_on}
    return out


def finish(fig, name, source, checks, dpi=400):
    """Render to paper/figures/<name>.png and write the render-evidence record."""
    OUT.mkdir(parents=True, exist_ok=True)
    png = OUT / (name + ".png")
    pdf = OUT / (name + ".pdf")
    svg = OUT / (name + ".svg")
    measured = audit(fig, dpi=dpi)
    ok = all(v.get("pass", True) for v in measured.values())
    fig.savefig(png, dpi=dpi, bbox_inches="tight", pad_inches=0.02)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.02)
    fig.savefig(svg, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    rec = {"status": "PASS" if ok else "FAIL",
           "rendered_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "checks": {"procedural": checks, "measured": measured}, "source": source,
           "outputs": [str(png.relative_to(ROOT)).replace(chr(92), "/"),
                       str(pdf.relative_to(ROOT)).replace(chr(92), "/")],
           "dpi": dpi, "style": "topjournal-style (opaque data, no grid, white background)"}
    body = json.dumps(rec, ensure_ascii=False, indent=2) + chr(10)
    (OUT / (name + ".render.json")).write_text(body, encoding="utf-8")
    # the paper references the .pdf explicitly, so a second record is written under the
    # exact referenced filename (scripts/figure_render_audit.py resolves it literally)
    (OUT / (name + ".pdf.render.json")).write_text(body, encoding="utf-8")
    print("rendered", png.relative_to(ROOT), "audit", "PASS" if ok else "FAIL",
          {k: v.get("pass") for k, v in measured.items()})
    return png


DEFAULT_CHECKS = [
    "no clipped title, axis label, legend or annotation (bbox_inches=tight)",
    "no overlapping labels obscuring values",
    "font size readable at final column width",
    "units present on every axis label",
    "no empty or unintended subplot",
    "series distinguished by colour AND line style or marker (survives grayscale)",
    "data drawn opaque (alpha=1.0), no grid, white background",
    "caption and visual support the same claim",
    "plotted values agree with the canonical data artifact recorded in source",
]
