# -*- coding: utf-8 -*-
"""Freeze the approved numerical claims for Q1-Q3 from the experiment artifacts.

Every value is read from its source file; nothing is typed by hand.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOW = time.strftime("%Y-%m-%dT%H:%M:%S%z")

def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def clean(v):
    """Round a frozen value to its reporting precision so the LaTeX macro prints a
    readable number: 4 decimals at or above 1e-3, otherwise 3 significant digits."""
    import math
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return v
    if v == 0:
        return 0.0
    if abs(v) >= 1e-3:
        return round(float(v), 4)
    d = 2 - math.floor(math.log10(abs(v)))
    return round(float(v), d)


def claim(cid, value, unit, src, loc, decision):
    return {"claim_id": cid, "value": clean(value), "unit": unit, "source_file": src,
            "source_locator": loc, "frozen_at": NOW,
            "frozen_by_skill": "solution-package-builder", "decision_id": decision}

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    out = {}

    # ---------------- Q1 ----------------
    m = load("results/Q1/experiments/round1/metrics/main.json")
    mv = load("results/Q1/experiments/round1/metrics/main_validation.json")
    vv = load("results/Q1/experiments/round1/metrics/verifier_validation.json")
    rv = load("robustness/Q1/q1_robustness_summary.json")
    S = "results/Q1/experiments/round1/metrics/"
    out["Q1"] = {"claims": [
        claim("q1_T_center_1800s", m["table1_temperature_C"]["1800"][0], "°C", S + "main.json", "$.table1_temperature_C['1800'][0]", "q1_package_signoff"),
        claim("q1_T_surface_1800s", m["table1_temperature_C"]["1800"][4], "°C", S + "main.json", "$.table1_temperature_C['1800'][4]", "q1_package_signoff"),
        claim("q1_C_center_1800s", m["table2_moisture_kg_per_kg"]["1800"][0], "kg/kg", S + "main.json", "$.table2_moisture_kg_per_kg['1800'][0]", "q1_package_signoff"),
        claim("q1_C_surface_1800s", m["table2_moisture_kg_per_kg"]["1800"][4], "kg/kg", S + "main.json", "$.table2_moisture_kg_per_kg['1800'][4]", "q1_package_signoff"),
        claim("q1_analytical_max_abs_err", mv["analytical_cross_check"]["max_abs_err"], "kg/kg", S + "main_validation.json", "$.analytical_cross_check.max_abs_err", "q1_package_signoff"),
        claim("q1_grid_refinement_diff", mv["grid_refinement"]["max_abs_diff_400_vs_800"], "kg/kg", S + "main_validation.json", "$.grid_refinement.max_abs_diff_400_vs_800", "q1_package_signoff"),
        claim("q1_time_accuracy_tolerance_diff", mv["time_accuracy"]["max_abs_diff_1e_8_vs_1e_9"], "kg/kg", S + "main_validation.json", "$.time_accuracy.max_abs_diff_1e_8_vs_1e_9", "q1_package_signoff"),
        claim("q1_mass_balance_rel", mv["mass_balance"]["rel_balance_error"], "", S + "main_validation.json", "$.mass_balance.rel_balance_error", "q1_package_signoff"),
        claim("q1_independent_implementations_diff", vv["convergence_limit_comparison"]["abs_diff"], "kg/kg", S + "verifier_validation.json", "$.convergence_limit_comparison.abs_diff", "q1_package_signoff"),
        claim("q1_h_m_plus5pct_surface_shift", rv["checks"]["h_m_perturbation"]["observed"]["h_m x1.05"]["surface_shift"], "kg/kg", "robustness/Q1/q1_robustness_summary.json", "$.checks.h_m_perturbation.observed['h_m x1.05'].surface_shift", "q1_package_signoff"),
    ]}

    # ---------------- Q2 ----------------
    m = load("results/Q2/experiments/round1/metrics/main.json")
    mv = load("results/Q2/experiments/round1/metrics/main_validation.json")
    vv = load("results/Q2/experiments/round1/metrics/verifier_validation.json")
    rv = load("robustness/Q2/q2_robustness_summary.json")
    S = "results/Q2/experiments/round1/metrics/"
    def sens(node, sub=None):
        d = rv["checks"][node]
        if sub:
            d = d[sub]
        return d["observed"]["t_dry_shift_percent"]
    out["Q2"] = {"claims": [
        claim("q2_drying_time", m["drying_time_hours"], "h", S + "main.json", "$.drying_time_hours", "q2_package_signoff"),
        claim("q2_T_center_3h", m["table3_temperature_C"]["3.0"][0], "°C", S + "main.json", "$.table3_temperature_C['3.0'][0]", "q2_package_signoff"),
        claim("q2_T_surface_3h", m["table3_temperature_C"]["3.0"][4], "°C", S + "main.json", "$.table3_temperature_C['3.0'][4]", "q2_package_signoff"),
        claim("q2_C_center_3h", m["table4_moisture_kg_per_kg"]["3.0"][0], "kg/kg", S + "main.json", "$.table4_moisture_kg_per_kg['3.0'][0]", "q2_package_signoff"),
        claim("q2_C_surface_3h", m["table4_moisture_kg_per_kg"]["3.0"][4], "kg/kg", S + "main.json", "$.table4_moisture_kg_per_kg['3.0'][4]", "q2_package_signoff"),
        claim("q2_analytical_max_abs_err", vv["reference_vs_analytical"]["max_abs_err"], "kg/kg", S + "verifier_validation.json", "$.reference_vs_analytical.max_abs_err", "q2_package_signoff"),
        claim("q2_grid_refinement_diff", mv["grid_refinement_6h"]["max_abs_diff_C"], "kg/kg", S + "main_validation.json", "$.grid_refinement_6h.max_abs_diff_C", "q2_package_signoff"),
        claim("q2_time_refinement_diff", mv["time_refinement_full_span"]["abs_diff_hours"], "h", S + "main_validation.json", "$.time_refinement_full_span.abs_diff_hours", "q2_package_signoff"),
        claim("q2_mass_balance_rel", mv["mass_balance"]["rel_error"], "", S + "main_validation.json", "$.mass_balance.rel_error", "q2_package_signoff"),
        claim("q2_drying_time_spread", vv["drying_time"]["abs_diff_seconds"], "s", S + "verifier_validation.json", "$.drying_time.abs_diff_seconds", "q2_package_signoff"),
        claim("q2_sens_mass_equation_form", sens("mass_equation_form"), "%", "robustness/Q2/q2_robustness_summary.json", "$.checks.mass_equation_form.observed.t_dry_shift_percent", "q2_package_signoff"),
        claim("q2_sens_T_inf_plus2C", sens("env_extrapolation_t_inf_52"), "%", "robustness/Q2/q2_robustness_summary.json", "$.checks.env_extrapolation_t_inf_52.observed.t_dry_shift_percent", "q2_package_signoff"),
        claim("q2_sens_D_plus5pct", sens("D_perturbation"), "%", "robustness/Q2/q2_robustness_summary.json", "$.checks.D_perturbation.observed.t_dry_shift_percent", "q2_package_signoff"),
        claim("q2_sens_h_m_plus5pct", sens("h_m_perturbation", "plus5pct"), "%", "robustness/Q2/q2_robustness_summary.json", "$.checks.h_m_perturbation.plus5pct.observed.t_dry_shift_percent", "q2_package_signoff"),
        claim("q2_table_region_env_insensitivity", max(rv["checks"]["env_extrapolation_c_inf_0.045"]["observed"]["max_abs_diff_table_C"],
                                                      rv["checks"]["env_extrapolation_c_inf_0.055"]["observed"]["max_abs_diff_table_C"]), "kg/kg", "robustness/Q2/q2_robustness_summary.json", "$.checks.env_extrapolation_c_inf_0.045.observed.max_abs_diff_table_C", "q2_package_signoff"),
    ]}

    # ---------------- Q3 ----------------
    m = load("results/Q3/experiments/round1/metrics/main.json")
    mv = load("results/Q3/experiments/round1/metrics/main_validation.json")
    bm = load("results/Q2/experiments/round1/metrics/main.json")
    S = "results/Q3/experiments/round1/metrics/"
    out["Q3"] = {"claims": [
        claim("q3_drying_time", m["drying_time_hours"], "h", S + "main.json", "$.drying_time_hours", "q3_package_signoff"),
        claim("q3_C_center_at_end", m["table5_end_row"]["C"][0], "kg/kg", S + "main.json", "$.table5_end_row.C[0]", "q3_package_signoff"),
        claim("q3_C_surface_at_end", m["table5_end_row"]["C"][4], "kg/kg", S + "main.json", "$.table5_end_row.C[4]", "q3_package_signoff"),
        claim("q3_C_center_54h", m["table5_moisture_kg_per_kg"]["54"][0], "kg/kg", S + "main.json", "$.table5_moisture_kg_per_kg['54'][0]", "q3_package_signoff"),
        claim("q3_consistency_with_Q2", bm["drying_time_hours"], "h", "results/Q2/experiments/round1/metrics/main.json", "$.drying_time_hours", "q3_package_signoff"),
        claim("q3_grid_refinement_diff", mv["grid_refinement_6h"]["max_abs_diff_C"], "kg/kg", S + "main_validation.json", "$.grid_refinement_6h.max_abs_diff_C", "q3_package_signoff"),
        claim("q3_time_refinement_diff", mv["time_refinement_full_span"]["abs_diff_hours"], "h", S + "main_validation.json", "$.time_refinement_full_span.abs_diff_hours", "q3_package_signoff"),
        claim("q3_mass_balance_rel", mv["mass_balance"]["rel_error"], "", S + "main_validation.json", "$.mass_balance.rel_error", "q3_package_signoff"),
    ]}

    for q, d in out.items():
        p = ROOT / ("results/%s/reports/frozen_numbers.json" % q)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("frozen %s: %d claims -> %s" % (q, len(d["claims"]), p.relative_to(ROOT)))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
