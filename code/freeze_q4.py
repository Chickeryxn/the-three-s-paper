# -*- coding: utf-8 -*-
"""Freeze the approved numerical claims for Q4 from the experiment artifacts.

Every value is read from its source file; nothing is typed by hand. Companion of
code/freeze_q1q3.py, which freezes Q1-Q3.
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
    S = "results/Q4/experiments/round1/metrics/"
    m = load(S + "main.json")
    mv = load(S + "main_validation.json")
    vv = load(S + "verifier_validation.json")
    rv = load("robustness/Q4/q4_robustness_summary.json")
    q3 = load("results/Q3/experiments/round1/metrics/main.json")
    D = "q4_package_signoff"
    claims = [
        claim("q4_drying_time_hours", m["drying_time_hours"], "h", S + "main.json",
              "$.drying_time_hours", D),
        claim("q4_R_at_drying_end_cm", m["radius"]["R_at_drying_end_cm"], "cm", S + "main.json",
              "$.radius.R_at_drying_end_cm", D),
        claim("q4_shrinkage_percent", m["radius"]["shrinkage_percent"], "%", S + "main.json",
              "$.radius.shrinkage_percent", D),
        claim("q4_table6_t6_center", m["table6_moisture_kg_per_kg"]["6"][0], "kg/kg", S + "main.json",
              "$.table6_moisture_kg_per_kg['6'][0]", D),
        claim("q4_table6_t6_surface", m["table6_moisture_kg_per_kg"]["6"][4], "kg/kg", S + "main.json",
              "$.table6_moisture_kg_per_kg['6'][4]", D),
        claim("q4_table6_end_center", m["table6_end_row"]["C"][0], "kg/kg", S + "main.json",
              "$.table6_end_row.C[0]", D),
        claim("q4_table6_end_surface", m["table6_end_row"]["C"][4], "kg/kg", S + "main.json",
              "$.table6_end_row.C[4]", D),
        claim("q4_reference_max_abs_err", vv["reference_vs_analytical"]["max_abs_err"], "kg/kg",
              S + "verifier_validation.json", "$.reference_vs_analytical.max_abs_err", D),
        claim("q4_moving_boundary_dev",
              mv["moving_boundary_invariance"]["observed_max_abs_deviation_of_C_from_C0"], "kg/kg",
              S + "main_validation.json",
              "$.moving_boundary_invariance.observed_max_abs_deviation_of_C_from_C0", D),
        claim("q4_mass_balance_rel", mv["mass_balance"]["rel_residual"], "", S + "main_validation.json",
              "$.mass_balance.rel_residual", D),
        claim("q4_grid_refinement_diff", mv["grid_refinement_6h"]["max_abs_diff_C"], "kg/kg",
              S + "main_validation.json", "$.grid_refinement_6h.max_abs_diff_C", D),
        claim("q4_time_refinement_hours", mv["time_refinement_full_span"]["abs_diff_hours"], "h",
              S + "main_validation.json", "$.time_refinement_full_span.abs_diff_hours", D),
        claim("q4_radius_interp_hours", mv["radius_interpolation"]["abs_diff_hours"], "h",
              S + "main_validation.json", "$.radius_interpolation.abs_diff_hours", D),
        claim("q4_baseline_table6_diff", vv["main_vs_baseline_table6"]["max_abs_diff"], "kg/kg",
              S + "verifier_validation.json", "$.main_vs_baseline_table6.max_abs_diff", D),
        claim("q4_baseline_drying_time_seconds", vv["drying_time"]["abs_diff_seconds"], "s",
              S + "verifier_validation.json", "$.drying_time.abs_diff_seconds", D),
        claim("q4_sens_h_m_plus5pct_hours",
              rv["checks"]["h_m_perturbation"]["plus5pct"]["observed"]["t_dry_shift_hours"], "h",
              "robustness/Q4/q4_robustness_summary.json",
              "$.checks.h_m_perturbation.plus5pct.observed.t_dry_shift_hours", D),
        claim("q4_sens_D_plus5pct_hours", rv["checks"]["D_perturbation"]["observed"]["t_dry_shift_hours"], "h",
              "robustness/Q4/q4_robustness_summary.json",
              "$.checks.D_perturbation.observed.t_dry_shift_hours", D),
        claim("q4_sens_T_inf_plus2C_hours",
              rv["checks"]["env_extrapolation_t_inf_52"]["observed"]["t_dry_shift_hours"], "h",
              "robustness/Q4/q4_robustness_summary.json",
              "$.checks.env_extrapolation_t_inf_52.observed.t_dry_shift_hours", D),
        claim("q4_sens_mass_equation_form_hours",
              rv["checks"]["mass_equation_form"]["observed"]["t_dry_shift_hours"], "h",
              "robustness/Q4/q4_robustness_summary.json",
              "$.checks.mass_equation_form.observed.t_dry_shift_hours", D),
        claim("q4_vs_q3_drying_time_hours", m["drying_time_hours"] - q3["drying_time_hours"], "h",
              S + "main.json", "$.drying_time_hours (minus results/Q3/.../main.json $.drying_time_hours)", D),
    ]
    p = ROOT / "results/Q4/reports/frozen_numbers.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"claims": claims}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("frozen Q4: %d claims -> %s" % (len(claims), p.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
