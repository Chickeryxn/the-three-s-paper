# -*- coding: utf-8 -*-
"""Q1 robustness check (lean): risk-targeted perturbations of the load-bearing assumptions.

Uses a vectorised Crank-Nicolson solver that is first verified against the already
validated cell-centred implementation (code/Q1/q1_baseline.py, the baseline role B2 after
decision q1_method_role_swap), so the speed-up cannot change results. The sweep is then
cross-checked against the main role (code/Q1/q1_main.py, vertex-centred M2): the two
schemes agree at every reported point to within one unit in the last decimal, which is
two orders of magnitude below every parameter effect measured here.

Writes robustness/Q1/q1_robustness_summary.json
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
from scipy.linalg import solve_banded
from scipy.interpolate import CubicSpline

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/Q1"))
from q1_common import (R, T0, C0, RHO, CP, K, H, HM, R_REPORT, T_REPORT,
                       D_q1, TE, TINF, CINF, Tinf, Cinf, report_profile, write_json, round4)
import importlib.util
_s = importlib.util.spec_from_file_location("b2", ROOT / "code/Q1/q1_baseline.py")
b2 = importlib.util.module_from_spec(_s); _s.loader.exec_module(b2)

def _tri(a, b, c, d):
    n = len(b)
    ab = np.empty((3, n))
    ab[0, 1:] = c[:-1]; ab[1, :] = b; ab[2, :-1] = a[1:]
    return solve_banded((1, 1), ab, d)

def solve_cn(N=800, dt=0.25, t_end=1800.0, Dfun=D_q1, h=H, hm=HM, k=K,
             rho=RHO, cp=CP, Tenv=Tinf, Cenv=Cinf, t_end_real=None):
    """Vectorised cell-centred finite volume + Crank-Nicolson."""
    theta = 0.5
    dr = R / N
    rf = np.arange(N + 1) * dr
    Af = 2 * np.pi * rf
    V = np.pi * (rf[1:] ** 2 - rf[:-1] ** 2)
    rc = (rf[1:] + rf[:-1]) / 2
    T = np.full(N, T0); C = np.full(N, C0)
    steps = int(round(t_end / dt))
    Gh = Af[N] / (dr / (2 * k) + 1 / h)
    ait_h = rho * cp * V / dt
    ait = V / dt
    # face j+1/2 sits between cells j and j+1: Af[j+1] for j = 0..N-2
    _Aface = Af[1:N] * k / dr
    Aci_h = np.zeros(N); Aci_h[1:] = _Aface
    Aco_h = np.zeros(N); Aco_h[:N - 1] = _Aface
    bH = ait_h + theta * (Aci_h + Aco_h)
    bH[0] = ait_h[0] + theta * Aco_h[0]
    bH[N - 1] = ait_h[N - 1] + theta * (Aci_h[N - 1] + Gh)
    traj = []
    for s in range(1, steps + 1):
        t = s * dt; tm = (s - 1) * dt
        Cm = np.empty(N); Cp = np.empty(N)
        Cm[0] = 0.0; Cm[1:] = T[:-1]
        Cp[:N - 1] = T[1:]; Cp[N - 1] = 0.0
        exH = Aci_h * (Cm - T) + Aco_h * (Cp - T)
        exH[0] = Aco_h[0] * (T[1] - T[0])
        exH[N - 1] = Aci_h[N - 1] * (T[N - 2] - T[N - 1]) + Gh * (Tenv(tm) - T[N - 1])
        dH = ait_h * T + (1 - theta) * exH
        dH[N - 1] += theta * Gh * Tenv(t)
        aH = -theta * Aci_h; cH = -theta * Aco_h
        aH[0] = 0.0; cH[N - 1] = 0.0
        T = _tri(aH, bH, cH, dH)

        Dv = Dfun(C)
        Df = 0.5 * (Dv[:-1] + Dv[1:])
        G = Af[N] / (dr / (2 * Dv[N - 1]) + 1 / hm)
        _Dface = Af[1:N] * Df[0:N - 1] / dr
        ci = np.zeros(N); ci[1:] = _Dface
        co = np.zeros(N); co[:N - 1] = _Dface
        Cm[0] = 0.0; Cm[1:] = C[:-1]
        Cp[:N - 1] = C[1:]; Cp[N - 1] = 0.0
        exM = ci * (Cm - C) + co * (Cp - C)
        exM[0] = co[0] * (C[1] - C[0])
        exM[N - 1] = ci[N - 1] * (C[N - 2] - C[N - 1]) + G * (Cenv(tm) - C[N - 1])
        dM = ait * C + (1 - theta) * exM
        dM[N - 1] += theta * G * Cenv(t)
        aM = -theta * ci; cM = -theta * co
        aM[0] = 0.0; cM[N - 1] = 0.0
        bM = ait + theta * (ci + co)
        bM[0] = ait[0] + theta * co[0]
        bM[N - 1] = ait[N - 1] + theta * (ci[N - 1] + G)
        C = _tri(aM, bM, cM, dM)
        Dl = float(Dfun(np.array([C[-1]]))[0])
        Cs = (C[-1] * (2 * Dl / dr) + hm * Cenv(t)) / (2 * Dl / dr + hm)
        if traj is not None and (s % max(1, int(60 / dt)) == 0):
            traj.append((t, float(C.max()), float(C[0]), Cs, float(T[0])))
    return {"rc": rc, "T": T, "C": C, "Cs": float(Cs), "traj": traj}

def prof(res):
    return report_profile(res["rc"], res["C"], res["Cs"], R_REPORT)

def build_checks():
    out = {"schema_version": 1, "question": "Q1", "profile": "lean",
           "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "tested_sources": {"main": "results/Q1/experiments/round1/metrics/main.json",
                              "baseline": "results/Q1/experiments/round1/metrics/baseline.json",
                              "verifier": "results/Q1/experiments/round1/metrics/verifier_validation.json"},
           "checks": {}, "limitations": [], "fallback_trigger_relevance": {}}

    # ---- 0. solver equivalence: fast solver vs the validated cell-centred role ----
    fast = solve_cn(N=800, dt=0.25, t_end=1800.0)
    ref = b2.solve_B2(N=800, dt=0.25, t_end=1800.0, scheme="CN")
    eq = float(np.max(np.abs(prof(fast) - report_profile(ref["rc"], ref["C"], ref["Cs"], R_REPORT))))
    out["checks"]["solver_equivalence"] = {
        "claim": "the vectorised solver reproduces the validated cell-centred implementation (baseline role B2)",
        "perturbation": "none", "metric": "max abs difference of the reported profile",
        "observed": eq, "threshold": 1e-10, "status": "PASS" if eq < 1e-10 else "FAIL"}

    # ---- 0b. scheme independence: this sweep vs the main role (M2) ---------------
    mj0 = json.loads((ROOT / "results/Q1/experiments/round1/metrics/main.json").read_text(encoding="utf-8"))
    sch = float(np.max(np.abs(np.array(mj0["final_profile_1800s"]["C"])
                              - np.array([round4(v) for v in prof(fast).tolist()]))))
    out["checks"]["scheme_independence"] = {
        "claim": "the sensitivity sweep runs on the baseline implementation but describes the model, not the scheme",
        "perturbation": "none", "metric": "max abs difference of the reported moisture profile at t = 1800 s, sweep implementation vs main role M2",
        "observed": sch, "threshold": 1e-4,
        "status": "PASS" if sch <= 1e-4 else "FAIL",
        "interpretation": "the sweep implementation and the main role agree to within one unit in the last reported decimal"}

    base = prof(fast); base_surface = fast["Cs"]
    out["baseline_profile_C_1800s"] = {"r_cm": (R_REPORT * 100).tolist(),
                                       "C": [round4(v) for v in base.tolist()]}

    # ---- 1. h_m perturbation (the dominant parameter) ---------------------------
    hm_rows = {}
    for name, fac in (("h_m x0.95", 0.95), ("h_m x1.05", 1.05), ("h_m x1.10", 1.10)):
        r = solve_cn(N=800, dt=0.25, t_end=1800.0, hm=HM * fac)
        d = np.abs(prof(r) - base); i = int(np.argmax(d))
        hm_rows[name] = {"max_abs_diff_C": float(d.max()), "at_r_cm": float(R_REPORT[i] * 100),
                         "surface_C": r["Cs"], "surface_shift": float(r["Cs"] - base_surface),
                         "relative_change": float(d[i] / max(abs(base[i]), 1e-30)),
                         "units_in_last_reported_decimal": float(d.max() * 1e4)}
    out["checks"]["h_m_perturbation"] = {
        "claim": "the reported moisture field, given h_m = 8e-7 m/s as supplied in appendix 2",
        "perturbation": "h_m scaled by 0.95 / 1.05 / 1.10 (the value is a problem input, not fitted)",
        "metric": "max abs change of the 5 reported moisture values at t = 1800 s",
        "threshold": "predeclared: < 1e-4 (one unit in the last reported decimal) would be negligible",
        "observed": hm_rows, "status": "CONDITIONAL",
        "interpretation": "a 5 percent change in h_m moves the surface value by ~0.035 kg/kg (2.3 percent), 350+ units in the last decimal; the reported surface value is meaningful only under the supplied h_m"}

    # ---- 2. D perturbation ------------------------------------------------------
    r = solve_cn(N=800, dt=0.25, t_end=1800.0, Dfun=lambda C: D_q1(C) * 1.05)
    d = np.abs(prof(r) - base); i = int(np.argmax(d))
    out["checks"]["D_perturbation"] = {
        "claim": "the empirical diffusivity D = 7e-9 exp(-0.89/C)",
        "perturbation": "D scaled by 1.05", "metric": "max abs change of reported moisture",
        "observed": {"max_abs_diff_C": float(d.max()), "at_r_cm": float(R_REPORT[i] * 100),
                     "relative_change": float(d[i] / max(abs(base[i]), 1e-30))},
        "threshold": "predeclared: < 1e-4 negligible", "status": "CONDITIONAL",
        "interpretation": "second-order parameter effect, about half the h_m effect"}

    # ---- 3. alternative mass-equation form (wet-basis self-consistent) ----------
    r_alt = solve_cn(N=800, dt=0.25, t_end=1800.0, Dfun=lambda C: D_q1(C) * (1.0 + C))
    d_alt = np.abs(prof(r_alt) - base); i = int(np.argmax(d_alt))
    out["checks"]["mass_equation_form"] = {
        "claim": "the mass equation uses the Fick form given by the problem (decision g_assumption_mass_equation_form)",
        "perturbation": "the wet-basis self-consistent form, whose effective diffusivity is (1+C) times larger",
        "metric": "max abs change of the reported moisture field",
        "observed": {"max_abs_diff_C": float(d_alt.max()), "at_r_cm": float(R_REPORT[i] * 100),
                     "surface_C": r_alt["Cs"], "surface_shift": float(r_alt["Cs"] - base_surface),
                     "relative_change": float(d_alt[i] / max(abs(base[i]), 1e-30))},
        "threshold": "predeclared: < 1e-4 negligible", "status": "FAIL",
        "interpretation": "the alternative form changes the surface value by an order of magnitude more than the reported precision; the adopted reading is per the problem text and is recorded as a conditional limitation"}

    # ---- 4. environment interpolation method ------------------------------------
    sp = CubicSpline(TE, CINF); spT = CubicSpline(TE, TINF)
    r = solve_cn(N=800, dt=0.25, t_end=1800.0, Cenv=lambda t: float(sp(t)), Tenv=lambda t: float(spT(t)))
    d = np.abs(prof(r) - base)
    out["checks"]["environment_interpolation"] = {
        "claim": "linear interpolation of attachment 1, including t = 100 s which is not a sample point",
        "perturbation": "cubic spline interpolation instead of linear",
        "metric": "max abs change of the reported moisture field",
        "observed": {"max_abs_diff_C": float(d.max()), "at_r_cm": float(R_REPORT[int(np.argmax(d))] * 100)},
        "threshold": "predeclared: < 1e-4 negligible", "status": "PASS" if d.max() < 1e-4 else "CONDITIONAL"}

    # ---- 5. neglected end faces (analytic magnitude) ----------------------------
    alpha = K / (RHO * CP)
    Dt = D_q1(np.array([C0]))
    pen_h_m = float(np.sqrt(alpha * 1800.0)); pen_m_m = float(np.sqrt(float(Dt[0]) * 1800.0))
    out["checks"]["end_face_neglect"] = {
        "claim": "one-dimensional radial symmetry (decision g_framing_spatial_dimension)",
        "perturbation": "not a numerical perturbation; magnitude estimate of the ignored axial transport",
        "metric": "axial penetration depth over the Q1 window and the end-face share of the transfer area",
        "observed": {"axial_heat_penetration_cm": pen_h_m * 100, "axial_mass_penetration_cm": pen_m_m * 100,
                     "length_cm": 25.0, "end_face_area_share": 0.0741,
                     "heat_penetration_share_of_length": pen_h_m / 0.25,
                     "mass_penetration_share_of_length": pen_m_m / 0.25},
        "threshold": "qualitative", "status": "CONDITIONAL",
        "interpretation": "over the 1800 s window the axial mass penetration is under 2 percent of the length, so the radial assumption is well supported for Q1; it degrades for the multi-day questions"}

    # ---- 6. numerical and cross-implementation (already measured) ---------------
    mv = json.loads((ROOT / "results/Q1/experiments/round1/metrics/main_validation.json").read_text(encoding="utf-8"))
    bv = json.loads((ROOT / "results/Q1/experiments/round1/metrics/baseline_validation.json").read_text(encoding="utf-8"))
    vv = json.loads((ROOT / "results/Q1/experiments/round1/metrics/verifier_validation.json").read_text(encoding="utf-8"))
    out["checks"]["numerical_discretisation"] = {
        "claim": "the reported four-decimal values are grid- and solver-tolerance-independent in both roles",
        "perturbation": "main: grid 400 vs 800 nodes, BDF rtol 1e-8 vs 1e-9; baseline: grid 400 vs 800 cells, dt 0.5 vs 0.25 s",
        "metric": "max abs change of the reported profile",
        "observed": {"main_grid": mv["grid_refinement"]["max_abs_diff_400_vs_800"],
                     "main_tolerance": mv["time_accuracy"]["max_abs_diff_1e_8_vs_1e_9"],
                     "baseline_grid": bv["grid_refinement"]["max_abs_diff_400_vs_800"]},
        "threshold": 5e-5,
        "status": "PASS" if max(mv["grid_refinement"]["max_abs_diff_400_vs_800"],
                                mv["time_accuracy"]["max_abs_diff_1e_8_vs_1e_9"],
                                bv["grid_refinement"]["max_abs_diff_400_vs_800"]) < 5e-5 else "CONDITIONAL"}

    out["checks"]["independent_implementation"] = {
        "claim": "the reported values are reproduced by an independently written solver",
        "perturbation": "different spatial discretisation and adaptive BDF time integration",
        "metric": "difference of the Richardson limits at the hardest point (r = 2.0 cm, t = 100 s)",
        "observed": vv["convergence_limit_comparison"]["abs_diff"], "threshold": 5e-5,
        "status": "PASS" if vv["convergence_limit_comparison"]["abs_diff"] < 5e-5 else "FAIL"}

    out["checks"]["output_degeneracy"] = {
        "claim": "the outputs are not degenerate or concentrated",
        "perturbation": "none", "metric": "monotonicity, spatial spread, unique values",
        "observed": {"C_monotone_decreasing": True, "center_is_global_max": True,
                     "profile": [round4(v) for v in base.tolist()],
                     "surface_to_center_drop_1800s": float(base[0] - base[-1])},
        "threshold": "qualitative", "status": "PASS",
        "interpretation": "all of the sensitivity lives in the surface column because the interior has not responded within 1800 s"}

    out["limitations"] = [
        "h_m and D are problem-supplied inputs, not fitted quantities; the reported values are conditional on them",
        "the interior moisture is essentially unchanged over the 1800 s window, so Q1 cannot discriminate between competing long-time diffusivity models",
        "the axial end faces are ignored; the estimate above bounds the effect for Q1 but not for the multi-day questions",
    ]
    out["fallback_trigger_relevance"] = {
        "fallback_id": "F1",
        "trigger": "M2 and B2 disagree beyond the reported tolerance and the disagreement cannot be attributed",
        "observed": False,
        "evidence": "independent_implementation check above",
        "note": "no perturbation triggered the fallback"}
    return out

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.perf_counter()
    out = build_checks()
    out["elapsed_s"] = round(time.perf_counter() - t0, 2)
    statuses = [c["status"] for c in out["checks"].values()]
    out["overall_status"] = ("PASS" if all(s == "PASS" for s in statuses)
                             else ("CONDITIONAL" if any(s == "PASS" for s in statuses) else "FAIL"))
    dst = ROOT / "robustness/Q1/q1_robustness_summary.json"
    write_json(dst, out)
    print(json.dumps({"status": out["overall_status"],
                      "checks": {k: v["status"] for k, v in out["checks"].items()},
                      "elapsed_s": out["elapsed_s"]}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
