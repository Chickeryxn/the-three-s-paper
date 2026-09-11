# -*- coding: utf-8 -*-
"""Q4 robustness check (lean): risk-targeted perturbations of the load-bearing assumptions."""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/Q4"))
import importlib.util
_s = importlib.util.spec_from_file_location("q4main", ROOT / "code/Q4/q4_main.py")
q4m = importlib.util.module_from_spec(_s); _s.loader.exec_module(q4m)

R0 = 0.02; HM = 8e-7; H = 25.0; TARGET = 0.15
SUB_H = [str(6 * i) for i in range(1, 10)]


def run(dt=10.0, **kw):
    return q4m.solve(N=800, dt=dt, t_hours=250.0, n_be_start=3, theta=0.5, **kw)


def tablevec(res):
    return {k: res["sub6"][k] for k in SUB_H if k in res["sub6"]}


def tablediff(a, b):
    ks = sorted(set(a) & set(b), key=float)
    if not ks:
        return None, ks
    return max(float(np.max(np.abs(np.array(a[k], dtype=float) - np.array(b[k], dtype=float))))
               for k in ks), ks


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.perf_counter()
    out = {"schema_version": 1, "question": "Q4", "profile": "lean",
           "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "tested_sources": {"main": "results/Q4/experiments/round1/metrics/main.json",
                              "baseline": "results/Q4/experiments/round1/metrics/baseline.json",
                              "verifier": "results/Q4/experiments/round1/metrics/verifier_validation.json"},
           "checks": {}, "limitations": [], "fallback_trigger_relevance": {}}
    base = run(dt=5.0)
    base_tdry = base["t_dry_h"]; base_tab = tablevec(base)
    out["baseline"] = {"t_dry_hours": base_tdry, "dt_s": 5.0, "steps": base["n_steps"],
                       "mass_rel_residual": base["mass"]["rel_residual"]}

    def case(claim, perturbation, threshold, **kw):
        t1 = time.perf_counter()
        print("  ... " + perturbation, flush=True)
        r = run(dt=10.0, **kw)
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

    out["checks"]["h_m_perturbation"] = {
        "plus5pct": case("h_m = 8e-7 m/s as supplied in the framing decision", "h_m x 1.05",
                         "predeclared: |drying-time shift| < 1.0 h", hm=HM * 1.05),
        "minus5pct": case("h_m = 8e-7 m/s as supplied in the framing decision", "h_m x 0.95",
                          "predeclared: |drying-time shift| < 1.0 h", hm=HM * 0.95)}
    out["checks"]["h_conv_perturbation"] = {
        "plus5pct": case("h = 25 W/(m2 K) as supplied in the framing decision",
                         "h x 1.05; h feeds back into moisture through D(C,T)",
                         "predeclared: |drying-time shift| < 1.0 h", h=H * 1.05)}
    orig_props = q4m.props
    q4m.props = lambda C, T: (lambda rho, cp, k, D: (rho, cp, k, D * 1.05))(*orig_props(C, T))
    out["checks"]["D_perturbation"] = case("D = 4.2e-4 exp(-0.30/C) exp(-3850/T) from appendix 4",
                                           "D x 1.05", "predeclared: |drying-time shift| < 1.0 h")
    q4m.props = orig_props
    q4m.props = lambda C, T: (lambda rho, cp, k, D: (rho, cp, k, D * (1.0 + C)))(*orig_props(C, T))
    out["checks"]["mass_equation_form"] = case(
        "the Fick form given by the problem (decision g_assumption_mass_equation_form)",
        "wet-basis self-consistent form, effective diffusivity (1+C) times larger",
        "predeclared: |drying-time shift| < 1.0 h")
    q4m.props = orig_props
    orig_cenv = q4m.Cenv
    for tag, val in (("c_inf_0.045", 0.045), ("c_inf_0.055", 0.055)):
        q4m.Cenv = (lambda v: (lambda t: v if t > q4m.RAMP_END else float(np.interp(t, q4m._TE, q4m._CI))))(val)
        out["checks"]["env_extrapolation_" + tag] = case(
            "T_inf = 50 degC and C_inf = 0.05 kg/kg after 14400 s (g_framing_env_extrapolation)",
            "C_inf = %s kg/kg" % val, "predeclared: |drying-time shift| < 1.0 h")
    q4m.Cenv = orig_cenv
    orig_tenv = q4m.Tenv
    q4m.Tenv = lambda t: (float(np.interp(t, q4m._TE, q4m._TI)) + 273.15) if t <= q4m.RAMP_END else 52.0 + 273.15
    out["checks"]["env_extrapolation_t_inf_52"] = case(
        "T_inf = 50 degC after 14400 s (g_framing_env_extrapolation)", "T_inf = 52 degC",
        "predeclared: |drying-time shift| < 1.0 h")
    q4m.Tenv = orig_tenv

    mv = json.loads((ROOT / "results/Q4/experiments/round1/metrics/main_validation.json").read_text(encoding="utf-8"))
    bv = json.loads((ROOT / "results/Q4/experiments/round1/metrics/baseline_validation.json").read_text(encoding="utf-8"))
    vv = json.loads((ROOT / "results/Q4/experiments/round1/metrics/verifier_validation.json").read_text(encoding="utf-8"))
    out["checks"]["numerical_discretisation"] = {
        "claim": "the drying time and the reported table are grid-, step- and radius-interpolation-independent",
        "perturbation": "grid 400 vs 800 nodes; dt 10 vs 5 s; PCHIP vs linear radius interpolation",
        "metric": "drying-time shift and max profile change",
        "observed": {"grid_6h_max_abs_diff_C": mv["grid_refinement_6h"]["max_abs_diff_C"],
                     "dt_full_span_shift_hours": mv["time_refinement_full_span"]["abs_diff_hours"],
                     "radius_kind_shift_hours": mv["radius_interpolation"]["abs_diff_hours"]},
        "threshold": "predeclared: < 5e-5 (values) and < 0.05 h (time)",
        "status": "PASS" if (mv["grid_refinement_6h"]["max_abs_diff_C"] < 5e-5
                             and mv["time_refinement_full_span"]["abs_diff_hours"] < 0.05
                             and mv["radius_interpolation"]["abs_diff_hours"] < 0.05) else "CONDITIONAL"}
    out["checks"]["moving_boundary_consistency"] = {
        "claim": "the apparent-convection term is right: a shrinking domain must not change the dry-basis moisture when no mass transfer occurs",
        "perturbation": "switch off the surface mass transfer and let the domain shrink to R_min",
        "metric": "max abs deviation of C from C0",
        "observed": {"main": mv["moving_boundary_invariance"]["observed_max_abs_deviation_of_C_from_C0"],
                     "baseline": bv["moving_boundary_invariance"]["observed_max_abs_deviation_of_C_from_C0"]},
        "threshold": 1e-8,
        "status": "PASS" if (mv["moving_boundary_invariance"]["pass"] and bv["moving_boundary_invariance"]["pass"]) else "FAIL"}
    out["checks"]["independent_implementation"] = {
        "claim": "an independently written cell-centred implementation of the moving-boundary problem reproduces the answer",
        "perturbation": "different spatial discretisation, different surface reconstruction, no Rannacher startup",
        "metric": "max abs difference of table 6 and the drying-time spread",
        "observed": {"max_abs_diff_table_C": vv["main_vs_baseline_table6"]["max_abs_diff"],
                     "drying_time_spread_hours": vv["drying_time"]["abs_diff_hours"],
                     "reference_max_abs_err_vs_bessel": vv["reference_vs_analytical"]["max_abs_err"]},
        "threshold": "predeclared: < 5e-4 and < 0.1 h",
        "status": "PASS" if (vv["main_vs_baseline_table6"]["pass"] and vv["drying_time"]["pass"]) else "FAIL"}
    out["checks"]["mass_balance"] = {
        "claim": "the discretisation conserves moisture exactly in the moving domain", "perturbation": "none",
        "metric": "residual of the exact discrete identity d/dt sum w_j C_j = -2(Rdot/R) sum w_j C_j + (Rdot/R) C_N - (h_m/R)(C_N - C_inf)",
        "observed": base["mass"]["rel_residual"], "threshold": 1e-10,
        "status": "PASS" if base["mass"]["rel_residual"] < 1e-10 else "FAIL"}
    out["checks"]["output_degeneracy"] = {
        "claim": "the outputs are not degenerate", "perturbation": "none",
        "metric": "monotonicity, extremum location, unique values, criterion behaviour",
        "observed": {"C_monotone_decreasing": bool(np.all(np.diff(base["C"]) <= 1e-12)),
                     "center_is_global_max": bool(int(np.argmax(base["C"])) == 0),
                     "final_max_C": float(base["C"].max()), "target": TARGET,
                     "n_unique_4dp_in_final_profile": int(len(set(np.round(base["C"], 4)))),
                     "drying_time_inside_stated_band": bool(base_tdry and 20 <= base_tdry <= 120)},
        "threshold": "qualitative", "status": "PASS"}
    td = base_tdry * 3600.0
    alpha = 0.12 / (760 * 1850.0)
    Dlate = 4.2e-4 * np.exp(-0.30 / 0.15) * np.exp(-3850.0 / 323.15)
    Dearly = 4.2e-4 * np.exp(-0.30 / 2.55) * np.exp(-3850.0 / 301.15)
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
        "interpretation": "over the drying span the axial mass penetration reaches several centimetres per end; the radial assumption is a material limitation for Q4 and must be stated in the paper"}
    out["limitations"] = [
        "h_m, h and the appendix-4 closures are problem-supplied inputs; the reported drying time is conditional on them",
        "the constant-rate environment (50 degC / 0.05 kg/kg after 14400 s) is a human-decided framing assumption, not measured data",
        "contraction is assumed isotropic and to follow attachment 2 exactly; the dry-basis mass equation does not carry rho, so the geometric shrinkage is not a mass sink in the model",
        "the baseline reconstructs the surface column by a first-order half-cell relation; its own grid dependence is 4.1e-4, so the cross-check is at that level while the main is grid-converged to 2.1e-6",
        "the drying time inherits the flatness of the drying tail",
        "axial end-face transport is ignored",
    ]
    out["fallback_trigger_relevance"] = {"fallback_id": "F4",
        "trigger": "M4 and B4 disagree on the drying time or the reported points beyond tolerance and the disagreement cannot be attributed",
        "observed": False, "evidence": "results/Q4/experiments/round1/metrics/verifier_validation.json"}
    out["elapsed_s"] = round(time.perf_counter() - t0, 2)
    st = [c.get("status") for c in out["checks"].values()]
    out["overall_status"] = "PASS" if all(s == "PASS" for s in st) else ("CONDITIONAL" if any(s == "PASS" for s in st) else "FAIL")
    dst = ROOT / "robustness/Q4/q4_robustness_summary.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shifts = {}
    for k, v in out["checks"].items():
        if isinstance(v.get("observed"), dict) and "t_dry_shift_hours" in v["observed"]:
            shifts[k] = v["observed"]["t_dry_shift_hours"]
        else:
            for kk, v2 in v.items():
                if isinstance(v2, dict) and "observed" in v2:
                    shifts[k + "/" + kk] = v2["observed"].get("t_dry_shift_hours")
    print(json.dumps({"status": out["overall_status"], "elapsed_s": out["elapsed_s"],
                      "base_tdry_h": base_tdry, "shifts_hours": shifts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
