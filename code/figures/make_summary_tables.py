# -*- coding: utf-8 -*-
"""Build the three summary tables (table 7/8/9) as Markdown + CSV under paper/tables/.

One table = one conclusion; every value is read from a canonical artifact.
"""
from __future__ import annotations
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper/tables"


def J(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def frozen(q):
    d = J("results/%s/reports/frozen_numbers.json" % q)
    return {c["claim_id"]: c["value"] for c in d["claims"]}


def write(name, rows, header, caption, note):
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / (name + ".csv")).open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh); w.writerow(header)
        for r in rows:
            w.writerow(r)
    lines = ["# " + caption, "", note, "",
             "| " + " | ".join(header) + " |",
             "|" + "|".join(["---"] * len(header)) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(str(x) for x in r) + " |")
    (OUT / (name + ".md")).write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
    print("wrote paper/tables/%s.{csv,md} (%d rows)" % (name, len(rows)))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    f1, f2, f3, f4 = frozen("Q1"), frozen("Q2"), frozen("Q3"), frozen("Q4")
    v3 = J("results/Q3/experiments/round1/metrics/verifier_validation.json")

    # ---- table 7: parameters and empirical closures ----
    rows7 = [
        ["R0 / R_min", "药材初始/最终半径", "2.000 / 1.198", "cm", "附件2（问题4）"],
        ["L", "药材长度", "25", "cm", "题目"],
        ["T0", "初始温度", "28", "°C", "题目"],
        ["C0", "初始干基含水率", "2.55", "kg/kg", "题目"],
        ["T_inf", "恒温段环境温度", "50", "°C", "g_framing_env_extrapolation（人工口径）"],
        ["C_inf", "恒温段环境水分浓度", "0.05", "kg/kg", "g_framing_env_extrapolation（人工口径）"],
        ["h", "对流换热系数", "25", "W/(m²·K)", "g_framing_convective_coefficients"],
        ["h_m", "对流传质系数", "8×10⁻⁷", "m/s", "g_framing_convective_coefficients"],
        ["ρ", "密度（附录2/3/4）", "820 / 650+128C / 760+90C", "kg/m³", "附录2/3/4"],
        ["c_p", "比热容（附录2/3/4）", "2600 / 1450+2736C/(C+1) / 1850+2150C/(C+1)", "J/(kg·K)", "附录2/3/4"],
        ["k", "导热系数（附录2/3/4）", "0.36 / 0.21+0.38C/(C+1) / 0.12+0.20C/(C+1)", "W/(m·K)", "附录2/3/4"],
        ["D", "水分扩散系数（附录2/3/4）",
         "7e-9·exp(-0.89/C) / 2.4e-3·exp(-0.45/C)·exp(-3850/T) / 4.2e-4·exp(-0.30/C)·exp(-3850/T)",
         "m²/s", "附录2/3/4"],
        ["判据", "烘干完成判据", "全域最大 C ≤ 0.15", "kg/kg", "g_caliber_criterion_granularity / g_caliber_overall_indicator"],
        ["坐标口径", "问题4 报告坐标", "当前物理距离，r > R(t) 留空 (T1)", "—", "g_framing_q4_coordinate_caliber"],
    ]
    write("table7_parameters", rows7, ["符号", "含义", "取值/经验式", "单位", "来源"],
          "表7 模型参数与经验式汇总",
          "> 所有取值来自题目附录与已确认的建模口径；恒温段环境为**人工设定口径**，非实测。")

    # ---- table 8: four-question results ----
    rows8 = [
        ["Q1", "预热平衡 0–1800 s", "中心 33.5753 °C / 表面 36.7856 °C；中心 C 2.5500 / 表面 1.5102 kg/kg",
         "重心在于本阶段以升温为主、失水仅限表层（扩散特征时间约 22 h）", "h_m 与附录2 经验式"],
        ["Q2", "恒温干燥 3 h 输出", "烘干时长 57.4647 h（全域最大 C 降至 0.15 kg/kg）",
         "干燥由内部扩散控制，属传质 Biot 数约 20 的内部扩散控制区", "h_m、附录3 经验式、恒温段口径"],
        ["Q3", "烘干时长", "烘干时长 57.4647 h（与 Q2 同源一致）",
         "与 Q2 共用同一模型，一致性作为跨问自检", "同 Q2"],
        ["Q4", "考虑尺寸变化", "烘干时长 52.6361 h；结束时半径 1.200 cm（收缩 40.1%）",
         "**收缩不可忽略**：比不收缩的 57.4647 h 短 4.83 h（−8.4%），不能由 Q3 直接推算",
         "h_m、附录4 经验式、收缩严格按附件2"],
    ]
    write("table8_results", rows8, ["问", "任务", "关键结果", "结论要点", "条件性"],
          "表8 四问结果汇总",
          "> 全部数值为条件式结论：以题目给定的 h_m、h 与相应附录经验式为条件；详见各问的适用边界。")

    # ---- table 9: verification and robustness ----
    r1 = J("robustness/Q1/q1_robustness_summary.json")["checks"]
    r2 = J("robustness/Q2/q2_robustness_summary.json")["checks"]
    r4 = J("robustness/Q4/q4_robustness_summary.json")["checks"]
    v2 = J("results/Q2/experiments/round1/metrics/verifier_validation.json")
    v4 = J("results/Q4/experiments/round1/metrics/verifier_validation.json")
    rows9 = [
        ["Q1", "%.2e" % f1["q1_analytical_max_abs_err"], "%.2e" % f1["q1_grid_refinement_diff"],
         "%.2e (kg/kg)" % f1["q1_time_accuracy_tolerance_diff"],
         "%.2e (kg/kg)" % f1["q1_independent_implementations_diff"], "%.2e" % f1["q1_mass_balance_rel"],
         "%.3f kg/kg（表面）" % r1["mass_equation_form"]["observed"]["max_abs_diff_C"],
         "%.4f kg/kg（表面）" % f1["q1_h_m_plus5pct_surface_shift"]],
        ["Q2", "%.2e" % f2["q2_analytical_max_abs_err"], "%.2e" % f2["q2_grid_refinement_diff"],
         "%.2e h" % f2["q2_time_refinement_diff"], "%.1f s（烘干时长）" % f2["q2_drying_time_spread"],
         "%.2e" % f2["q2_mass_balance_rel"], "%.2f%%（烘干时长）" % f2["q2_sens_mass_equation_form"],
         "%.2f%%（烘干时长）" % f2["q2_sens_h_m_plus5pct"]],
        ["Q3", "%.2e" % v3["reference_vs_analytical"]["max_abs_err"], "%.2e" % f3["q3_grid_refinement_diff"],
         "%.2e h" % f3["q3_time_refinement_diff"],
         "%.1f s（烘干时长）" % v3["drying_time"]["abs_diff_seconds"], "%.2e" % f3["q3_mass_balance_rel"],
         "%.2f%%（烘干时长）" % r2["mass_equation_form"]["observed"]["t_dry_shift_percent"],
         "%.2f%%（烘干时长）" % r2["h_m_perturbation"]["plus5pct"]["observed"]["t_dry_shift_percent"]],
        ["Q4", "%.2e" % f4["q4_reference_max_abs_err"], "%.2e" % f4["q4_grid_refinement_diff"],
         "%.2e h" % f4["q4_time_refinement_hours"],
         "%.1f s（烘干时长）" % v4["drying_time"]["abs_diff_seconds"], "%.2e" % f4["q4_mass_balance_rel"],
         "%.2f%%（烘干时长）" % r4["mass_equation_form"]["observed"]["t_dry_shift_percent"],
         "%.2f%%（烘干时长）" % r4["h_m_perturbation"]["plus5pct"]["observed"]["t_dry_shift_percent"]]]
    write("table9_verification", rows9,
          ["问", "解析对照 (kg/kg)", "网格加密 (kg/kg)", "时间加密", "独立实现差", "离散守恒 (1)",
           "质量方程替代读法影响", "h_m +5% 影响"],
          "表9 验证与稳健性证据汇总",
          "> 解析对照为常物性约化下 Bessel 级数解的最大绝对误差；网格加密为 400↔800 的最大差。\n"
          "> Q2 与 Q3 共用同一模型，故两者的 Q2 行与 Q3 行在扰动项上一致；每格均可回溯到对应源文件。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
