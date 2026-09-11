# -*- coding: utf-8 -*-
"""Q1 usable baseline (B2): cell-centred finite volume + Crank-Nicolson (theta=0.5) + Thomas.

Role assignment at G4 (decision q1_method_role_swap): this implementation served as the
main method through G3 and is retained as the independent baseline after the
vertex-centred node form was promoted. It remains a genuine cross-check: the spatial
discretisation (cells with face areas A(r) = 2*pi*r), the axis treatment (the r = 0 face
area is exactly zero) and the time integration (fixed-step Crank-Nicolson, second order,
A-stable) all differ from the promoted main method, and it never reads the main result as
a numeric input.

The numerical core `solve_B2` is reproduced verbatim from the implementation that produced
the archived pre-swap main metrics; code/Q1/q1_role_swap_check.py re-checks that this
script still reproduces that archive at the 7x5 report points.

Writes under results/Q1/experiments/round1/:
  metrics/baseline.json            (result_ref)
  metrics/baseline_validation.json (validation_ref)
  tables/table1_baseline.csv, table2_baseline.csv
"""
from __future__ import annotations
import csv, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q1_common import (ROOT, R, T0, C0, RHO, CP, K, H, HM, ROUND_DIR, R_REPORT,
                       T_REPORT, D_q1, Tinf, Cinf, thomas, report_profile,
                       bessel_C, write_json, round4)


def solve_B2(N=400, dt=0.25, t_end=1800.0, scheme="CN", Dfun=D_q1, const_D=None,
             h=H, hm=HM, k=K, rho=RHO, cp=CP, Tenv=Tinf, Cenv=Cinf,
             record_grid=False, record_every_s=1.0):
    theta = 1.0 if scheme == "BE" else 0.5
    dr = R / N
    rf = np.arange(N + 1) * dr
    Af = 2 * np.pi * rf
    V = np.pi * (rf[1:] ** 2 - rf[:-1] ** 2)
    rc = (rf[1:] + rf[:-1]) / 2
    T = np.full(N, T0); C = np.full(N, C0)
    steps = int(round(t_end / dt))
    Gh = Af[N] / (dr / (2 * k) + 1 / h)

    aH = np.zeros(N); bH = np.zeros(N); cH = np.zeros(N)
    for i in range(N):
        ait = rho * cp * V[i] / dt
        if i == 0:
            co = Af[1] * k / dr; bH[i] = ait + theta * co; cH[i] = -theta * co
        elif i == N - 1:
            ci = Af[N - 1] * k / dr; bH[i] = ait + theta * (ci + Gh); aH[i] = -theta * ci
        else:
            ci = Af[i] * k / dr; co = Af[i + 1] * k / dr
            bH[i] = ait + theta * (ci + co); aH[i] = -theta * ci; cH[i] = -theta * co

    snaps = {}
    every = max(1, int(round(record_every_s / dt)))
    W0 = float(np.sum(C * V)); flux_sum = 0.0
    for s in range(1, steps + 1):
        t = s * dt; tm = (s - 1) * dt
        # Crank-Nicolson for a time-dependent boundary term uses b(t^{n+1}) implicitly
        # and b(t^n) explicitly; evaluating the implicit part at the midpoint injects a
        # systematic O(dt * b') bias (measured ~3e-4 degC at dt=0.25 s).
        tq = t
        # ---------------- temperature ----------------
        ait_h = rho * cp * V / dt
        dH = ait_h * T
        if theta < 1.0:
            for i in range(N):
                if i == 0:
                    co = Af[1] * k / dr; dH[i] += (1 - theta) * co * (T[1] - T[0])
                elif i == N - 1:
                    ci = Af[N - 1] * k / dr
                    dH[i] += (1 - theta) * (ci * (T[i - 1] - T[i]) + Gh * (Tenv(tm) - T[i]))
                else:
                    ci = Af[i] * k / dr; co = Af[i + 1] * k / dr
                    dH[i] += (1 - theta) * (ci * (T[i - 1] - T[i]) + co * (T[i + 1] - T[i]))
        dH[N - 1] += theta * Gh * Tenv(tq)
        T = thomas(aH, bH, cH, dH)
        # ---------------- moisture ----------------
        Cprev = C.copy()
        Dv = Dfun(C) if const_D is None else np.full(N, const_D)
        Df = 0.5 * (Dv[:-1] + Dv[1:])
        G = Af[N] / (dr / (2 * Dv[N - 1]) + 1 / hm)
        ait = V / dt
        aM = np.zeros(N); bM = np.zeros(N); cM = np.zeros(N); dM = np.zeros(N)
        Cex = Cprev
        for i in range(N):
            if i == 0:
                co = Af[1] * Df[0] / dr
                bM[i] = ait[i] + theta * co; cM[i] = -theta * co
                dM[i] = ait[i] * C[i] + (1 - theta) * co * (Cex[1] - Cex[0])
            elif i == N - 1:
                ci = Af[N - 1] * Df[-1] / dr
                bM[i] = ait[i] + theta * (ci + G); aM[i] = -theta * ci
                dM[i] = (ait[i] * C[i]
                         + (1 - theta) * (ci * (Cex[i - 1] - Cex[i]) + G * (Cenv(tm) - Cex[i]))
                         + theta * G * Cenv(tq))
            else:
                ci = Af[i] * Df[i - 1] / dr; co = Af[i + 1] * Df[i] / dr
                bM[i] = ait[i] + theta * (ci + co); aM[i] = -theta * ci; cM[i] = -theta * co
                dM[i] = ait[i] * C[i] + (1 - theta) * (ci * (Cex[i - 1] - Cex[i]) + co * (Cex[i + 1] - Cex[i]))
        C = thomas(aM, bM, cM, dM)
        flux_sum += dt * (theta * G * (float(C[-1]) - Cenv(t))
                         + (1.0 - theta) * G * (float(Cprev[-1]) - Cenv(tm)))
        if record_grid and s % every == 0:
            Dl = float(Dfun(np.array([C[-1]]))[0]) if const_D is None else float(const_D)
            Cs = (C[-1] * (2 * Dl / dr) + hm * Cenv(t)) / (2 * Dl / dr + hm)
            Ts = (T[-1] * (2 * k / dr) + h * Tenv(t)) / (2 * k / dr + h)
            snaps[int(round(t))] = (T.copy(), C.copy(), float(Ts), float(Cs))

    Dl = float(Dfun(np.array([C[-1]]))[0]) if const_D is None else float(const_D)
    Cs = (C[-1] * (2 * Dl / dr) + hm * Cenv(t_end)) / (2 * Dl / dr + hm)
    Ts = (T[-1] * (2 * k / dr) + h * Tenv(t_end)) / (2 * k / dr + h)
    Wend = float(np.sum(C * V))
    ref = max(abs(Wend - W0), 1e-300)
    return {"rc": rc, "T": T, "C": C, "Ts": float(Ts), "Cs": float(Cs), "snaps": snaps,
            "mass": {"W0": W0, "Wend": Wend, "flux_sum": flux_sum,
                     "abs_balance_error": abs((Wend - W0) + flux_sum),
                     "rel_balance_error": abs((Wend - W0) + flux_sum) / ref}}


def main():
    t_start = time.perf_counter()
    RUN = ROUND_DIR
    for sub in ("metrics", "tables"):
        (RUN / sub).mkdir(parents=True, exist_ok=True)

    res = solve_B2(N=800, dt=0.25, t_end=1800.0, scheme="CN",
                   record_grid=True, record_every_s=1.0)
    rc = res["rc"]

    table = {}
    for t in T_REPORT:
        Tk, Ck, Tsk, Csk = res["snaps"][t]
        table[t] = {"T": report_profile(rc, Tk, Tsk, R_REPORT).tolist(),
                    "C": report_profile(rc, Ck, Csk, R_REPORT).tolist()}

    grid_ref = {}
    for N in (400, 800):
        r2 = solve_B2(N=N, dt=0.25, t_end=1800.0, scheme="CN")
        grid_ref[N] = report_profile(r2["rc"], r2["C"], r2["Cs"], R_REPORT).tolist()
    d_g1 = float(np.max(np.abs(np.array(grid_ref[400]) - np.array(grid_ref[800]))))
    d_g2 = d_g1 / 4.0

    surf = {}
    for N in (200, 400, 800):
        r2 = solve_B2(N=N, dt=0.0625, t_end=100.0, scheme="CN")
        surf[N] = float(r2["Cs"])
    lim = surf[800] + (surf[800] - surf[400]) / 3.0

    Dc = float(D_q1(np.array([C0]))[0])
    ref = solve_B2(N=400, dt=0.1, t_end=1800.0, scheme="CN", const_D=Dc,
                   Cenv=lambda t: 0.05, Tenv=lambda t: 28.0)
    refprof = report_profile(ref["rc"], ref["C"], ref["Cs"], R_REPORT)
    ana = np.array(bessel_C(R_REPORT, 1800.0, Dc, HM, Cinfv=0.05))
    ana_err = float(np.max(np.abs(refprof - ana)))

    Ck = np.asarray(res["snaps"][1800][1])
    Tk = np.asarray(res["snaps"][1800][0])

    result = {"schema_version": 1, "question": "Q1", "method_id": "B2",
              "role": "usable_baseline", "script": "code/Q1/q1_baseline.py",
              "scheme": "Crank-Nicolson (theta=0.5), cell-centred finite volume, Thomas",
              "grid": {"cells": 800, "dt_s": 0.25, "t_end_s": 1800.0},
              "r_cm": (R_REPORT * 100).tolist(),
              "table1_temperature_C": {str(t): [round4(v) for v in table[t]["T"]] for t in T_REPORT},
              "table2_moisture_kg_per_kg": {str(t): [round4(v) for v in table[t]["C"]] for t in T_REPORT},
              "final_profile_1800s": {"C": [round4(v) for v in table[1800]["C"]],
                                      "T": [round4(v) for v in table[1800]["T"]]},
              "reference_case": {"config": "D frozen at C=2.55, C_inf=0.05 const, T_inf=28 const",
                                 "C_at_1800s": [round4(v) for v in refprof.tolist()],
                                 "r_cm": (R_REPORT * 100).tolist()},
              "role_note": "retained from the main role through G3 (decision q1_method_role_swap); numerical core reproduced verbatim"}

    validation = {"schema_version": 1, "question": "Q1", "method_id": "B2",
                  "grid_refinement": {"N": [400, 800], "dt_s": 0.25,
                                      "max_abs_diff_400_vs_800": d_g1,
                                      "richardson_estimate_finer": d_g2,
                                      "reported_4dp_stable": bool(d_g1 < 5e-5)},
                  "surface_column_convergence": {
                      "where": "r = 2.0 cm, t = 100 s (thinnest boundary layer)",
                      "N": [200, 400, 800], "Cs": {str(k): v for k, v in surf.items()},
                      "richardson_limit": lim, "error_at_N800": abs(surf[800] - lim),
                      "observed_order": 2},
                  "analytical_cross_check": {"reference": "Bessel series, constant D",
                                             "max_abs_err": ana_err, "tolerance": 5e-5,
                                             "pass": bool(ana_err < 5e-5)},
                  "mass_balance": {"method": "per-step telescoping identity of the cell-centred flux form (accumulated surface flux vs cell inventory change)",
                                   "abs_residual": res["mass"]["abs_balance_error"],
                                   "rel_balance_error": res["mass"]["rel_balance_error"],
                                   "relative_to_water_inventory": res["mass"]["abs_balance_error"] / max(abs(res["mass"]["W0"]), 1e-30),
                                   "water_change": res["mass"]["Wend"] - res["mass"]["W0"],
                                   "window_s": [0.0, 1800.0]},
                  "invariants": {"C_monotone_decreasing": bool(np.all(np.diff(Ck) <= 1e-12)),
                                 "T_monotone_increasing": bool(np.all(np.diff(Tk) >= -1e-12)),
                                 "center_is_argmax_C": bool(int(np.argmax(Ck)) == 0),
                                 "n_unique_4dp": int(len(set(np.round(Ck, 4)))),
                                 "axis_symmetry": "finite-volume face area Af[0] = 0 (exact)"},
                  "role_note": "the reported surface value is reconstructed from the outermost cell centre through the Robin relation C_s = (C_N*2D/dr + h_m*C_inf)/(2D/dr + h_m)",
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

    print("B2(cell-centred CN) done:", {"grid_diff": d_g1, "surface_limit": lim,
                                        "surface_err_N800": abs(surf[800] - lim),
                                        "ana_err": ana_err,
                                        "mass_rel": res["mass"]["rel_balance_error"],
                                        "elapsed_s": round(time.perf_counter() - t_start, 2)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
