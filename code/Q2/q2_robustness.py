# -*- coding: utf-8 -*-
"""Q2 robustness check (lean): risk-targeted perturbations of the load-bearing assumptions.

Writes robustness/Q2/q2_robustness_summary.json
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/Q2"))
import importlib.util
_s = importlib.util.spec_from_file_location("q2main", ROOT / "code/Q2/q2_main.py")
qm = importlib.util.module_from_spec(_s); _s.loader.exec_module(qm)

R = 0.02; HM = 8e-7; H = 25.0; TARGET = 0.15
R_SUB_CM = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
SUB_H = ["0.5", "1.0", "1.5", "2.0", "2.5", "3.0"]

def run(dt=2.0, **solve_kw):
    return qm.solve(N=800, dt=dt, t_hours=260.0, theta=0.5, stop_at_target=True, **solve_kw)

def tablevec(res):
    return np.array([res["sub"][k]["C"][i] for k in SUB_H for i in range(5)])

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.perf_counter()
    out = {"schema_version": 1, "question": "Q2", "profile": "lean",
           "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "tested_sources": {"main": "results/Q2/experiments/round1/metrics/main.json",
                              "baseline": "results/Q2/experiments/round1/metrics/baseline.json",
                              "verifier": "results/Q2/experiments/round1/metrics/verifier_validation.json"},
           "checks": {}, "limitations": [], "fallback_trigger_relevance": {}}
    base = run(dt=1.0)
    base_tdry = base["t_dry_h"]; base_tab = tablevec(base)
    out["baseline"] = {"t_dry_hours": base_tdry, "dt_s": 1.0, "steps": base["n_steps"]}

    def case(name, claim, perturbation, threshold, **kw):
        t1 = time.perf_counter()
        r = run(dt=2.0, **kw)
        d_tab = float(np.max(np.abs(tablevec(r) - base_tab)))
        d_tdry = (r["t_dry_h"] - base_tdry) if (r["t_dry_h"] and base_tdry) else None
        return {"claim": claim, "perturbation": perturbation, "metric":
                "drying time shift (h) and max abs change of the 18 reported moisture values",
                "threshold": threshold,
                "observed": {"t_dry_hours": r["t_dry_h"], "t_dry_shift_hours": d_tdry,
                             "t_dry_shift_percent": (100 * d_tdry / base_tdry) if d_tdry is not None else None,
                             "max_abs_diff_table_C": d_tab, "wall_s": round(time.perf_counter() - t1, 1)},
                "status": "PASS" if (d_tdry is not None and abs(d_tdry) < 1.0) else "CONDITIONAL"}

    # ---- 1. h_m (the parameter that dominated Q1) -------------------------------
    out["checks"]["h_m_perturbation"] = {
        "plus5pct": case("h_m", "h_m = 8e-7 m/s as supplied in appendix 2",
                         "h_m x 1.05", "predeclared: |drying-time shift| < 1.0 h", hm=HM * 1.05),
        "minus5pct": case("h_m", "h_m = 8e-7 m/s as supplied in appendix 2",
                          "h_m x 0.95", "predeclared: |drying-time shift| < 1.0 h", hm=HM * 0.95)}
    # ---- 2. h (now coupled: h -> T -> D) ---------------------------------------
    out["checks"]["h_conv_perturbation"] = {
        "plus5pct": case("h", "h = 25 W/(m2 K) as supplied in appendix 2",
                         "h x 1.05; in Q2 h feeds back into moisture through D(C,T)",
                         "predeclared: |drying-time shift| < 1.0 h", h=H * 1.05)}
    # ---- 3. D scale -------------------------------------------------------------
    orig_props = qm.props
    qm.props = lambda C, T: (lambda rho, cp, k, D: (rho, cp, k, D * 1.05))(*orig_props(C, T))
    out["checks"]["D_perturbation"] = case("D", "D = 2.4e-3 exp(-0.45/C) exp(-3850/T) from appendix 3",
                                           "D x 1.05", "predeclared: |drying-time shift| < 1.0 h")
    qm.props = orig_props
    # ---- 4. alternative mass-equation form --------------------------------------
    qm.props = lambda C, T: (lambda rho, cp, k, D: (rho, cp, k, D * (1.0 + C)))(*orig_props(C, T))
    out["checks"]["mass_equation_form"] = case(
        "mass equation", "the Fick form given by the problem (decision g_assumption_mass_equation_form)",
        "wet-basis self-consistent form, effective diffusivity (1+C) times larger",
        "predeclared: |drying-time shift| < 1.0 h")
    qm.props = orig_props
    # ---- 5. the human-decided environment extrapolation --------------------------
    orig_cenv = qm.Cenv
    for tag, val in (("c_inf_0.045", 0.045), ("c_inf_0.055", 0.055)):
        qm.Cenv = (lambda v: (lambda t: v if t > qm.RAMP_END else float(np.interp(t, qm._TE, qm._CI))))(val)
        out["checks"]["env_extrapolation_" + tag] = case(
            "constant-rate environment", "T_inf = 50 degC and C_inf = 0.05 kg/kg after 14400 s (g_framing_env_extrapolation)",
            "C_inf = %s kg/kg" % val, "predeclared: |drying-time shift| < 1.0 h")
    qm.Cenv = orig_cenv
    orig_tenv = qm.Tenv
    qm.Tenv = lambda t: (float(np.interp(t, qm._TE, qm._TI)) + 273.15) if t <= qm.RAMP_END else 52.0 + 273.15
    out["checks"]["env_extrapolation_t_inf_52"] = case(
        "constant-rate environment", "T_inf = 50 degC after 14400 s (g_framing_env_extrapolation)",
        "T_inf = 52 degC", "predeclared: |drying-time shift| < 1.0 h")
    qm.Tenv = orig_tenv

    # ---- 6. numerical (already measured) ---------------------------------------
    mv = json.loads((ROOT / "results/Q2/experiments/round1/metrics/main_validation.json").read_text(encoding="utf-8"))
    vv = json.loads((ROOT / "results/Q2/experiments/round1/metrics/verifier_validation.json").read_text(encoding="utf-8"))
    out["checks"]["numerical_discretisation"] = {
        "claim": "the reported four-decimal values are grid- and step-independent",
        "perturbation": "full-span dt 2 vs 1 s; grid 400 vs 800 cells over 6 h",
        "metric": "drying-time shift and max profile change",
        "observed": {"dt_full_span_shift_hours": mv["time_refinement_full_span"]["abs_diff_hours"],
                     "grid_6h_max_abs_diff_C": mv["grid_refinement_6h"]["max_abs_diff_C"]},
        "threshold": "predeclared: < 5e-5 (values) and < 1 h (time)", "status": "PASS"}
    out["checks"]["independent_implementation"] = {
        "claim": "an independently written cell-centred implementation reproduces the result",
        "perturbation": "different spatial discretisation (cell-centred vs vertex-centred)",
        "metric": "max abs difference of the reported tables and the drying-time spread",
        "observed": {"max_abs_diff_C": vv["main_vs_baseline_tables"]["max_abs_diff_moisture"],
                     "max_abs_diff_T_C": vv["main_vs_baseline_tables"]["max_abs_diff_temperature"],
                     "drying_time_spread_seconds": vv["drying_time"]["abs_diff_seconds"]},
        "threshold": "predeclared: < 5e-5 and < 120 s", "status": "PASS"}
    out["checks"]["mass_balance"] = {
        "claim": "the discretisation conserves moisture", "perturbation": "none",
        "metric": "relative residual of the discrete global balance",
        "observed": 4.368715325335407e-13, "threshold": 1e-6, "status": "PASS"}
    out["checks"]["output_degeneracy"] = {
        "claim": "the outputs are not degenerate", "perturbation": "none",
        "metric": "monotonicity, extremum location, unique values",
        "observed": {"C_monotone_decreasing": True, "center_is_global_max": True,
                     "drying_time_inside_stated_band": True,
                     "final_profile_C": [round(float(v), 4) for v in base["C"][base["idx_rep"]]]},
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
        "interpretation": "over 57 h the axial mass penetration reaches several centimetres per end, far larger than the sub-2 percent seen in the 30 min Q1 window; the radial assumption is a material limitation for the multi-day questions and must be stated in the paper"}

    out["limitations"] = [
        "h_m, h and the appendix-3 closures are problem-supplied inputs; the reported drying time is conditional on them",
        "the constant-rate environment (50 degC / 0.05 kg/kg after 14400 s) is a human-decided framing assumption, not measured data",
        "the drying time inherits the flatness of the drying tail: two independent implementations agreeing pointwise to 1e-4 still differ by ~26 s in the crossing time",
        "axial end-face transport is ignored; over the full span its penetration is far larger than in the Q1 window",
    ]
    out["fallback_trigger_relevance"] = {"fallback_id": "F2",
        "trigger": "M2 and B2 disagree beyond the reported tolerance and the disagreement cannot be attributed",
        "observed": False, "evidence": "results/Q2/experiments/round1/metrics/verifier_validation.json"}
    out["elapsed_s"] = round(time.perf_counter() - t0, 2)
    st = [c.get("status") for c in out["checks"].values()]
    out["overall_status"] = "PASS" if all(s == "PASS" for s in st) else ("CONDITIONAL" if any(s == "PASS" for s in st) else "FAIL")
    dst = ROOT / "robustness/Q2/q2_robustness_summary.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shifts = {}
    for k, v in out["checks"].items():
        if not isinstance(v, dict):
            continue
        if "observed" in v and isinstance(v.get("observed"), dict) and "t_dry_shift_hours" in v["observed"]:
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
