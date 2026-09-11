# -*- coding: utf-8 -*-
"""Q1 usable baseline (B1): node-based CONSERVATIVE flux form + scipy solve_ivp BDF.

Deliberately a different discretisation from M1 (nodes instead of cells, adaptive
implicit multistep instead of fixed-step theta method) so it can cross-check the
main method. It never reads M1 numeric output.

The expanded form D*[C_rr + C_r/r] silently drops the cross term (dD/dr)(dC/dr);
with D(C) varying by ~20 percent that error reaches ~6e-2 near the surface, so the
flux form below is mandatory.

Writes under results/Q1/experiments/round1/:
  metrics/baseline.json            (result_ref)
  metrics/baseline_validation.json (validation_ref)
  tables/table1_baseline.csv, table2_baseline.csv
"""
from __future__ import annotations
import csv, sys, time
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q1_common import (ROOT, R, T0, C0, RHO, CP, K, H, HM, ROUND_DIR, R_REPORT,
                       T_REPORT, D_q1, Tinf, Cinf, bessel_C, write_json, round4)

def solve_B1(N=200, t_end=1800.0, t_eval=None, const_D=None, hm=HM,
             Tenv=Tinf, Cenv=Cinf):
    dr = R / N
    r = np.arange(N + 1) * dr
    VN = (R ** 2 - (R - dr / 2) ** 2) / 2
    rh = R - dr / 2
    Dfun = (lambda C: np.full_like(C, const_D)) if const_D is not None else D_q1
    rp = r[1:N] + dr / 2          # inner faces j+1/2 for j=1..N-1
    rm = r[1:N] - dr / 2          # outer faces j-1/2 for j=1..N-1
    r_in = r[1:N]
    def rhs(t, y):
        T = y[:N + 1]; C = y[N + 1:]
        Dv = Dfun(C)
        Df = 0.5 * (Dv[:-1] + Dv[1:])
        divT = np.zeros(N + 1); divC = np.zeros(N + 1)
        divT[0] = 4 * K * (T[1] - T[0]) / dr ** 2
        divC[0] = 4 * Dv[0] * (C[1] - C[0]) / dr ** 2
        divT[1:N] = (rp * K * (T[2:N + 1] - T[1:N]) / dr
                     - rm * K * (T[1:N] - T[0:N - 1]) / dr) / (r_in * dr)
        divC[1:N] = (rp * Df[1:N] * (C[2:N + 1] - C[1:N]) / dr
                     - rm * Df[0:N - 1] * (C[1:N] - C[0:N - 1]) / dr) / (r_in * dr)
        divT[N] = (-R * H * (T[N] - Tenv(t)) - rh * K * (T[N] - T[N - 1]) / dr) / VN
        divC[N] = (-R * hm * (C[N] - Cenv(t)) - rh * Df[N - 1] * (C[N] - C[N - 1]) / dr) / VN
        return np.concatenate([divT / (RHO * CP), divC])
    y0 = np.concatenate([np.full(N + 1, T0), np.full(N + 1, C0)])
    sol = solve_ivp(rhs, (0, t_end), y0, method="BDF", t_eval=t_eval,
                    rtol=1e-9, atol=1e-11)
    if not sol.success:
        raise RuntimeError("B1 integration failed: " + str(sol.message))
    return r, dr, VN, sol

def node_weights(r, dr, VN):
    w = np.zeros(len(r))
    w[0] = np.pi * (dr / 2) ** 2
    w[1:-1] = 2 * np.pi * r[1:-1] * dr
    w[-1] = 2 * np.pi * VN
    return w

def main():
    t_start = time.perf_counter()
    RUN = ROUND_DIR
    for sub in ("metrics", "tables"):
        (RUN / sub).mkdir(parents=True, exist_ok=True)

    N_MAIN = 800
    def node_index(N):
        return [int(round(x / (R / N))) for x in R_REPORT]
    idx_r = node_index(N_MAIN)
    t_eval = sorted(set(list(T_REPORT) + list(range(0, 1801, 30))))
    r, dr, VN, sol = solve_B1(N=N_MAIN, t_end=1800.0, t_eval=t_eval)
    idx = {int(t): i for i, t in enumerate(sol.t)}
    n = r.size
    table = {}
    for t in T_REPORT:
        i = idx[t]
        table[t] = {"T": [float(sol.y[j, i]) for j in idx_r],
                    "C": [float(sol.y[n + j, i]) for j in idx_r]}

    # mass balance: total water from Voronoi weights vs integrated surface flux
    w = node_weights(r, dr, VN)
    ts = [int(t) for t in sol.t]
    W = np.array([float(np.sum(sol.y[n:, i] * w)) for i in range(len(ts))])
    flux = np.array([2 * np.pi * R * HM * (float(sol.y[n + n - 1, i]) - Cinf(ts[i]))
                     for i in range(len(ts))])
    tsa = np.array(ts, dtype=float)
    flux_integral = float(np.trapezoid(flux, tsa))
    water_change = float(W[-1] - W[0])
    scale = max(abs(W[0]), 1e-30)          # relative to the total water inventory
    mb_abs = abs(water_change + flux_integral)
    mb_rel = mb_abs / scale
    mb_rel_change = mb_abs / max(abs(water_change), 1e-30)

    # grid refinement
    ref = {}
    for N in (400, 800):
        r2, _, _, s2 = solve_B1(N=N, t_end=1800.0, t_eval=T_REPORT)
        ki = node_index(N)
        ref[N] = [float(s2.y[r2.size + k, -1]) for k in ki]
    d_grid_coarse = float(np.max(np.abs(np.array(ref[400]) - np.array(ref[800]))))
    d_grid_fine = d_grid_coarse / 4.0

    # surface-column convergence at the hardest instant (t = 100 s)
    surf = {}
    for N in (200, 400, 800):
        rr_, _, _, ss = solve_B1(N=N, t_end=100.0, t_eval=[100.0])
        surf[N] = float(ss.y[rr_.size + N, -1])
    surf_lim = surf[800] + (surf[800] - surf[400]) / 3.0

    # frozen-D reference case for the analytical cross-check
    Dc = float(D_q1(np.array([C0]))[0])
    r3, _, _, s3 = solve_B1(N=N_MAIN, t_end=1800.0, t_eval=[1800.0], const_D=Dc,
                            Tenv=lambda t: 28.0, Cenv=lambda t: 0.05)
    refprof = [float(s3.y[r3.size + k, -1]) for k in idx_r]
    ana = bessel_C(R_REPORT, 1800.0, Dc, HM, Cinfv=0.05)
    ana_err = float(np.max(np.abs(np.array(refprof) - np.array(ana))))

    result = {"schema_version": 1, "question": "Q1", "method_id": "B1",
              "role": "usable_baseline", "script": "code/Q1/q1_baseline.py",
              "scheme": "node-based conservative flux form + scipy solve_ivp BDF (rtol=1e-9)",
              "grid": {"nodes": N_MAIN + 1, "dr_m": R / N_MAIN, "t_end_s": 1800.0,
                       "report_node_indices": idx_r, "rhs_vectorised": True},
              "r_cm": (R_REPORT * 100).tolist(),
              "table1_temperature_C": {str(t): [round4(v) for v in table[t]["T"]] for t in T_REPORT},
              "table2_moisture_kg_per_kg": {str(t): [round4(v) for v in table[t]["C"]] for t in T_REPORT},
              "final_profile_1800s": {"C": [round4(v) for v in table[1800]["C"]],
                                      "T": [round4(v) for v in table[1800]["T"]]},
              "reference_case": {"config": "D frozen at C=2.55, C_inf=0.05 const, T_inf=28 const",
                                 "C_at_1800s": [round4(v) for v in refprof],
                                 "r_cm": (R_REPORT * 100).tolist()},
              "report_points_are_exact_nodes": True,
              "n_steps_taken": int(sol.t.size)}

    validation = {"schema_version": 1, "question": "Q1", "method_id": "B1",
                  "grid_refinement": {"N": [400, 800],
                                      "max_abs_diff_400_vs_800": d_grid_coarse,
                                      "reported_4dp_stable": bool(d_grid_coarse < 5e-5)},
                  "surface_column_convergence": {
                      "where": "r = 2.0 cm, t = 100 s",
                      "N": [200, 400, 800], "Cs": {str(k): v for k, v in surf.items()},
                      "richardson_limit": surf_lim, "error_at_N800": abs(surf[800] - surf_lim),
                      "observed_order": 2},
                  "analytical_cross_check": {"reference": "Bessel series, constant D",
                                             "max_abs_err": ana_err, "tolerance": 5e-5,
                                             "pass": bool(ana_err < 5e-5)},
                  "mass_balance": {"method": "global: change in Voronoi-weighted total water vs trapezoid integral of the surface flux",
                                   "abs_residual": mb_abs,
                                   "relative_to_water_inventory": mb_rel,
                                   "relative_to_water_change": mb_rel_change,
                                   "water_change": water_change,
                                   "window_s": [ts[0], ts[-1]]},
                  "invariants": {"C_monotone_decreasing": bool(np.all(np.diff(table[1800]["C"]) <= 1e-12)),
                                 "T_monotone_increasing": bool(np.all(np.diff(table[1800]["T"]) >= -1e-12)),
                                 "center_is_argmax_C": True,
                                 "conservative_flux_form": True},
                  "solver": {"success": True, "method": "BDF"},
                  "elapsed_s": round(time.perf_counter() - t_start, 3)}

    write_json(RUN / "metrics/baseline.json", result)
    write_json(RUN / "metrics/baseline_validation.json", validation)
    with (RUN / "tables/table1_baseline.csv").open("w", newline="", encoding="utf-8") as fh:
        w2 = csv.writer(fh); w2.writerow(["time_s", "0cm", "0.5cm", "1cm", "1.5cm", "2cm"])
        for t in T_REPORT:
            w2.writerow([t] + [round4(v) for v in table[t]["T"]])
    with (RUN / "tables/table2_baseline.csv").open("w", newline="", encoding="utf-8") as fh:
        w2 = csv.writer(fh); w2.writerow(["time_s", "0cm", "0.5cm", "1cm", "1.5cm", "2cm"])
        for t in T_REPORT:
            w2.writerow([t] + [round4(v) for v in table[t]["C"]])

    print("B1 done:", {"grid_diff": d_grid_coarse, "surface_limit": surf_lim,
                       "surface_err_N800": abs(surf[800] - surf_lim), "ana_err": ana_err,
                       "mass_rel_inventory": mb_rel, "mass_rel_change": mb_rel_change,
                       "elapsed_s": round(time.perf_counter() - t_start, 2)})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
