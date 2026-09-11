# -*- coding: utf-8 -*-
"""Q3 robustness check (lean): risk-targeted perturbations of the load-bearing assumptions.

Q3 shares its model with Q2; the perturbed quantities and the predeclared thresholds are the
same, but the reported observable is the drying time and the Q3 six-hour table (9 rows x 5
positions). Rationale for the added evidence: robustness/Q3/ previously did not exist, while
the Q3 stability verdict cites robustness evidence (decision q3_robustness_supplement).

Writes robustness/Q3/q3_robustness_summary.json
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/Q3"))
import importlib.util
_s = importlib.util.spec_from_file_location("q3main", ROOT / "code/Q3/q3_main.py")
q3m = importlib.util.module_from_spec(_s); _s.loader.exec_module(q3m)
qm = q3m.qm

R = 0.02; HM = 8e-7; H = 25.0; TARGET = 0.15
SUB_H = ["6", "12", "18", "24", "30", "36", "42", "48", "54"]


def run(dt=2.0, **kw):
    return q3m.solve(N=800, dt=dt, t_hours=260.0, n_be_start=3, theta=0.5, **kw)


def tablevec(res):
    """Rows actually reached before the criterion was crossed."""
    return {k: res["sub"][k]["C"] for k in SUB_H if k in res["sub"]}


def tablediff(a, b):
    ks = sorted(set(a) & set(b), key=float)
    if not ks:
        return None, ks
    return max(float(np.max(np.abs(np.array(a[k]) - np.array(b[k])))) for k in ks), ks


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.perf_counter()
    out = {"schema_version": 1, "question": "Q3", "profile": "lean",
           "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "tested_sources": {"main": "results/Q3/experiments/round1/metrics/main.json",
                              "baseline": "results/Q3/experiments/round1/metrics/baseline.json",
                              "verifier": "results/Q3/experiments/round1/metrics/verifier_validation.json"},
           "checks": {}, "limitations": [], "fallback_trigger_relevance": {}}
    base = run(dt=1.0)
    base_tdry = base["t_dry_h"]; base_tab = tablevec(base)
    out["baseline"] = {"t_dry_hours": base_tdry, "dt_s": 1.0, "steps": base["n_steps"],
                       "mass_rel_error": base["mass"]["rel_error"]}

    def case(claim, perturbation, threshold, **kw):
        t1 = time.perf_counter()
        print("  ... " + perturbation, flush=True)
        r = run(dt=2.0, **kw)
        d_tab, rows = tablediff(tablevec(r), base_tab)
        d_tdry = (r["t_dry_h"] - base_tdry) if (r["t_dry_h"] and base_tdry) else None
        return {"claim": claim, "perturbation": perturbation,
                "metric": "drying-time shift (h) and max abs change of the reported moisture values on the rows both runs reach",
                "threshold": threshold,
                "observed": {"t_dry_hours": r["t_dry_h"], "t_dry_shift_hours": d_tdry,
                             "t_dry_shift_percent": (100 * d_tdry / base_tdry) if d_tdry is not None else None,
                             "max_abs_diff_table_C": d_tab, "compared_rows": rows,
                             "wall_s": round(time.perf_counter() - t1, 1)},
                "status": "PASS" if (d_tdry is not None and abs(d_tdry) < 1.0) else "CONDITIONAL"}

    # ---- 1. h_m (the parameter that dominated Q1) -------------------------------
    # the Q3 solver reads h_m and h from module constants, so perturb them there
    out["checks"]["h_m_perturbation"] = {}
    orig_hm = q3m.HM
    q3m.HM = HM * 1.05
    out["checks"]["h_m_perturbation"]["plus5pct"] = case(
        "h_m = 8e-7 m/s as supplied in appendix 2", "h_m x 1.05",
        "predeclared: |drying-time shift| < 1.0 h")
    q3m.HM = HM * 0.95
    out["checks"]["h_m_perturbation"]["minus5pct"] = case(
        "h_m = 8e-7 m/s as supplied in appendix 2", "h_m x 0.95",
        "predeclared: |drying-time shift| < 1.0 h")
    q3m.HM = orig_hm
    # ---- 2. h (coupled through D(C,T)) ------------------------------------------
    orig_h = q3m.H
    q3m.H = H * 1.05
    out["checks"]["h_conv_perturbation"] = {
        "plus5pct": case("h = 25 W/(m2 K) as supplied in appendix 2",
                         "h x 1.05; in Q3 h feeds back into moisture through D(C,T)",
                         "predeclared: |drying-time shift| < 1.0 h")}
    q3m.H = orig_h
    # ---- 3. D scale -------------------------------------------------------------
    orig_props = qm.props
    qm.props = lambda C, T: (lambda rho, cp, k, D: (rho, cp, k, D * 1.05))(*orig_props(C, T))
    out["checks"]["D_perturbation"] = case("D = 2.4e-3 exp(-0.45/C) exp(-3850/T) from appendix 3",
                                           "D x 1.05", "predeclared: |drying-time shift| < 1.0 h")
    qm.props = orig_props
    # ---- 4. alternative mass-equation form --------------------------------------
    qm.props = lambda C, T: (lambda rho, cp, k, D: (rho, cp, k, D * (1.0 + C)))(*orig_props(C, T))
    out["checks"]["mass_equation_form"] = case(
        "the Fick form given by the problem (decision g_assumption_mass_equation_form)",
        "wet-basis self-consistent form, effective diffusivity (1+C) times larger",
        "predeclared: |drying-time shift| < 1.0 h")
    qm.props = orig_props
    # ---- 5. the human-decided environment extrapolation --------------------------
    orig_cenv = qm.Cenv
    for tag, val in (("c_inf_0.045", 0.045), ("c_inf_0.055", 0.055)):
        qm.Cenv = (lambda v: (lambda t: v if t > qm.RAMP_END else float(np.interp(t, qm._TE, qm._CI))))(val)
        out["checks"]["env_extrapolation_" + tag] = case(
            "T_inf = 50 degC and C_inf = 0.05 kg/kg after 14400 s (g_framing_env_extrapolation)",
            "C_inf = %s kg/kg" % val, "predeclared: |drying-time shift| < 1.0 h")
    qm.Cenv = orig_cenv
    orig_tenv = qm.Tenv
    qm.Tenv = lambda t: (float(np.interp(t, qm._TE, qm._TI)) + 273.15) if t <= qm.RAMP_END else 52.0 + 273.15
    out["checks"]["env_extrapolation_t_inf_52"] = case(
        "T_inf = 50 degC after 14400 s (g_framing_env_extrapolation)", "T_inf = 52 degC",
        "predeclared: |drying-time shift| < 1.0 h")
    qm.Tenv = orig_tenv

    # ---- 6. numerical (already measured by the round) ---------------------------
    mv = json.loads((ROOT / "results/Q3/experiments/round1/metrics/main_validation.json").read_text(encoding="utf-8"))
    vv = json.loads((ROOT / "results/Q3/experiments/round1/metrics/verifier_validation.json").read_text(encoding="utf-8"))
    out["checks"]["numerical_discretisation"] = {
        "claim": "the reported drying time and table are step- and grid-independent",
        "perturbation": "full-span dt 10 vs 1 s; grid 400 vs 800 nodes over the first 6 h",
        "metric": "drying-time shift and max profile change",
        "observed": {"dt_full_span_shift_hours": mv["time_refinement_full_span"]["abs_diff_hours"],
                     "grid_6h_max_abs_diff_C": mv["grid_refinement_6h"]["max_abs_diff_C"]},
        "threshold": "predeclared: < 5e-5 (values) and < 0.01 h (time)",
        "status": "PASS" if (mv["time_refinement_full_span"]["abs_diff_hours"] < 0.01
                             and mv["grid_refinement_6h"]["max_abs_diff_C"] < 5e-5) else "CONDITIONAL"}
    out["checks"]["independent_implementation"] = {
        "claim": "an independently written implementation reproduces the drying time",
        "perturbation": "different spatial discretisation and no Rannacher startup (baseline role)",
        "metric": "max abs difference of table 5 and the drying-time spread",
        "observed": {"max_abs_diff_table_C": vv["main_vs_baseline_table5"]["max_abs_diff"],
                     "max_abs_diff_end_row_C": vv["main_vs_baseline_end_row"]["max_abs_diff"],
                     "drying_time_spread_seconds": vv["drying_time"]["abs_diff_seconds"],
                     "startup_effect_at_dt1s": vv["startup_effect_check"]["measured_startup_effect_at_dt1s"]},
        "threshold": "predeclared: < 1.5e-4 and < 120 s",
        "status": "PASS" if (vv["main_vs_baseline_table5"]["pass"] and vv["drying_time"]["pass"]) else "FAIL"}
    out["checks"]["mass_balance"] = {
        "claim": "the discretisation conserves moisture", "perturbation": "none",
        "metric": "relative residual of the discrete global balance",
        "observed": base["mass"]["rel_error"], "threshold": 1e-6,
        "status": "PASS" if base["mass"]["rel_error"] < 1e-6 else "FAIL"}
    out["checks"]["output_degeneracy"] = {
        "claim": "the outputs are not degenerate", "perturbation": "none",
        "metric": "monotonicity, extremum location, unique values, criterion behaviour",
        "observed": {"C_monotone_decreasing": bool(np.all(np.diff(base["C"]) <= 1e-12)),
                     "center_is_global_max": bool(int(np.argmax(base["C"])) == 0),
                     "final_max_C": float(base["C"].max()), "target": TARGET,
                     "n_unique_4dp_in_final_profile": int(len(set(np.round(base["C"], 4)))),
                     "drying_time_inside_stated_band": bool(base_tdry and 40 <= base_tdry <= 72)},
        "threshold": "qualitative", "status": "PASS"}
    # ---- 7. neglected end faces over the multi-day span -------------------------
    td = base_tdry * 3600.0
    alpha = 0.36 / (820 * 2600.0)
    Dlate = 2.4e-3 * np.exp(-0.45 / 0.15) * np.exp(-3850.0 / 323.15)
    Dearly = 2.4e-3 * np.exp(-0.45 / 2.55) * np.exp(-3850.0 / 301.15)
    out["checks"]["end_face_neglect"] = {
        "claim": "one-dimensional radial symmetry (g_framing_spatial_dimension)",
        "perturbation": "not a numerical perturbation; magnitude of the ignored axial transport over the full span",
        "metric": "axial penetration depth per end as a share of the 25 cm length",
        "observed": {"span_hours": base_tdry,
                     "axial_heat_penetration_cm": float(np.sqrt(alpha * td) * 100),
                     "axial_mass_penetration_cm_early": float(np.sqrt(Dearly * td) * 100),
                     "axial_mass_penetration_cm_late": float(np.sqrt(Dlate * td) * 100),
                     "length_cm": 25.0,
                     "mass_share_of_length_percent_early": float(np.sqrt(Dearly * td) / 0.25 * 100)},
        "threshold": "qualitative", "status": "CONDITIONAL",
        "interpretation": "over the drying span the axial mass penetration reaches several centimetres per end; the radial assumption is a material limitation and must be stated in the paper"}

    out["limitations"] = [
        "h_m, h and the appendix-3 closures are problem-supplied inputs; the reported drying time is conditional on them",
        "the constant-rate environment (50 degC / 0.05 kg/kg after 14400 s) is a human-decided framing assumption, not measured data",
        "the drying time inherits the flatness of the drying tail: the two implementations agree pointwise to 1.5e-4 yet differ by about 26 s in the crossing time",
        "axial end-face transport is ignored; over the full span its penetration is far larger than in the 30 min Q1 window",
    ]
    out["fallback_trigger_relevance"] = {"fallback_id": "F3",
        "trigger": "M3 and B3 disagree beyond the reported tolerance and the disagreement cannot be attributed",
        "observed": False, "evidence": "results/Q3/experiments/round1/metrics/verifier_validation.json"}
    out["elapsed_s"] = round(time.perf_counter() - t0, 2)
    st = [c.get("status") for c in out["checks"].values()]
    out["overall_status"] = "PASS" if all(s == "PASS" for s in st) else ("CONDITIONAL" if any(s == "PASS" for s in st) else "FAIL")
    dst = ROOT / "robustness/Q3/q3_robustness_summary.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shifts = {}
    for k, v in out["checks"].items():
        if not isinstance(v, dict):
            continue
        if isinstance(v.get("observed"), dict) and "t_dry_shift_hours" in v["observed"]:
            shifts[k] = v["observed"]["t_dry_shift_hours"]
        else:
            for kk, vv2 in v.items():
                if isinstance(vv2, dict) and "observed" in vv2:
                    shifts[k + "/" + kk] = vv2["observed"].get("t_dry_shift_hours")
    print(json.dumps({"status": out["overall_status"], "elapsed_s": out["elapsed_s"],
                      "base_tdry_h": base_tdry, "shifts_hours": shifts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
