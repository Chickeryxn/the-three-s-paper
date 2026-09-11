# -*- coding: utf-8 -*-
"""Emit the three summary tables as LaTeX fragments (values via frozen macros)."""
from __future__ import annotations
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from latex_assembly import sanitize_macro_name

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper/tables"


def J(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def M(cid):
    return "\\" + sanitize_macro_name(cid)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    f = {q: {c["claim_id"]: c for c in J("results/%s/reports/frozen_numbers.json" % q)["claims"]}
         for q in ("Q1", "Q2", "Q3", "Q4")}

    t7 = ["\\begin{table}[H]", "  \\centering",
          "  \\caption{四问所用的物性与经验式汇总}\\label{tab:params}", "  \\small",
          "  \\begin{tabular}{llll}", "    \\toprule",
          "    参数 & 第 (1) 问（附录 2） & 第 (2)(3) 问（附录 3） & 第 (4) 问（附录 4） \\\\",
          "    \\midrule",
          "    密度 / (kg/m$^3$) & $820$ & $650+128C$ & $760+90C$ \\\\",
          "    比热容 / (J/(kg$\\cdot$K)) & $2600$ & $1450+\\dfrac{2736C}{C+1}$ & $1850+\\dfrac{2150C}{C+1}$ \\\\",
          "    导热系数 / (W/(m$\\cdot$K)) & $0.36$ & $0.21+\\dfrac{0.38C}{C+1}$ & $0.12+\\dfrac{0.20C}{C+1}$ \\\\",
          "    扩散系数 / (m$^2$/s) & $7\\times10^{-9}e^{-0.89/C}$ & $2.4\\times10^{-3}e^{-0.45/C}e^{-3850/T}$ & $4.2\\times10^{-4}e^{-0.30/C}e^{-3850/T}$ \\\\",
          "    \\midrule",
          "    对流传热系数 $h$ / (W/(m$^2\\cdot$K)) & \\multicolumn{3}{c}{$25$} \\\\",
          "    对流传质系数 $h_m$ / (m/s) & \\multicolumn{3}{c}{$8\\times10^{-7}$} \\\\",
          "    初始温度 / $^\\circ$C & \\multicolumn{3}{c}{$28$} \\\\",
          "    初始干基含水率 / (kg/kg) & \\multicolumn{3}{c}{$2.55$} \\\\",
          "    烘干判据 / (kg/kg) & \\multicolumn{3}{c}{全域最大 $\\le 0.15$} \\\\",
          "    \\bottomrule", "  \\end{tabular}",
          "  \\par\\smallskip\\footnotesize 表中 $T$ 在经验式内为热力学温度，单位为 K；其余各处温度均为摄氏度。",
          "\\end{table}", ""]
    (OUT / "table7_parameters.tex").write_text(chr(10).join(t7), encoding="utf-8")

    rows8 = [
        ("第 (1) 问", "预热平衡 $0\\sim1800$~s",
         "$33.5753$ / $36.7856$", "$2.5500$ / $1.5102$",
         "以升温为主，失水仅限表层"),
        ("第 (2) 问", "恒温干燥全过程", "—", "—", "烘干时长 " + M("q2_drying_time")),
        ("第 (3) 问", "烘干时长", "—", "—", "烘干时长 " + M("q3_drying_time")),
        ("第 (4) 问", "考虑尺寸收缩", "—", "—",
         "烘干时长 " + M("q4_drying_time_hours") + "，收缩至 " + M("q4_R_at_drying_end_cm")),
    ]
    t8 = ["\\begin{table}[H]", "  \\centering",
          "  \\caption{四个问题的结果汇总}\\label{tab:results}", "  \\small",
          "  \\begin{tabularx}{\\textwidth}{l l c c X}", "    \\toprule",
          "    问题 & 任务 & 中心/表面温度 & 中心/表面含水率 & 关键结论 \\\\", "    \\midrule"]
    for r in rows8:
        t8.append("    " + " & ".join(r) + " \\\\")
    t8 += ["    \\bottomrule", "  \\end{tabularx}",
           "  \\par\\smallskip\\footnotesize 第 (1) 问的温度与含水率单位为 $^\\circ$C 与 kg/kg，取 $1800$~s 时刻的值；",
           "  时间单位均为小时。", "\\end{table}", ""]
    (OUT / "table8_results.tex").write_text(chr(10).join(t8), encoding="utf-8")

    def cell(q, cid):
        return M(cid)
    t9 = ["\\begin{table}[H]", "  \\centering",
          "  \\caption{四问的检验量汇总}\\label{tab:verify}", "  \\footnotesize",
          "  \\begin{tabularx}{\\textwidth}{l *{5}{>{\\centering\\arraybackslash}X}}", "    \\toprule",
          "    问题 & 解析对照/(kg/kg) & 网格加密/(kg/kg) & 时间加密 & 独立实现差 & 离散守恒 \\\\",
          "    \\midrule",
          "    第 (1) 问 & " + M("q1_analytical_max_abs_err") + " & " + M("q1_grid_refinement_diff") +
          " & " + M("q1_time_accuracy_tolerance_diff") + " & " + M("q1_independent_implementations_diff") +
          " & " + M("q1_mass_balance_rel") + " \\\\",
          "    第 (2) 问 & " + M("q2_analytical_max_abs_err") + " & " + M("q2_grid_refinement_diff") +
          " & " + M("q2_time_refinement_diff") + " & " + M("q2_drying_time_spread") +
          " & " + M("q2_mass_balance_rel") + " \\\\",
          "    第 (3) 问 & " + M("q3_drying_time") + " & " + M("q3_grid_refinement_diff") +
          " & " + M("q3_time_refinement_diff") + " & " + M("q3_consistency_with_Q2") +
          " & " + M("q3_mass_balance_rel") + " \\\\",
          "    第 (4) 问 & " + M("q4_reference_max_abs_err") + " & " + M("q4_grid_refinement_diff") +
          " & " + M("q4_time_refinement_hours") + " & " + M("q4_baseline_drying_time_seconds") +
          " & " + M("q4_mass_balance_rel") + " \\\\",
          "    \\bottomrule", "  \\end{tabularx}",
          "  \\par\\smallskip\\footnotesize 第 (3) 问的解析对照取与其同模型的第 (2) 问结果；",
          "  第 (4) 问的时间加密一列为内部步长减半引起的烘干时长变化。", "\\end{table}", ""]
    (OUT / "table9_verification.tex").write_text(chr(10).join(t9), encoding="utf-8")
    for n in ("table7_parameters", "table8_results", "table9_verification"):
        print("wrote paper/tables/%s.tex" % n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
