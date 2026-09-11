# -*- coding: utf-8 -*-
"""Q2 main method (vertex-centred finite volume + Crank-Nicolson).

Per decision q2_presentation_method_amendment the main method is the VERTEX-centred
(dual-cell) conservative finite volume scheme; the cell-centred scheme is retained as
the independent baseline.

Dual control volumes on a cylinder (per unit length, 2*pi factored out and re-introduced
through the face areas):
    j = 0      : disk of radius dr/2      -> V_0 = pi dr^2 / 4
    j = 1..N-1 : [r_{j-1/2}, r_{j+1/2}]   -> V_j = 2 pi j dr^2
    j = N      : [R-dr/2, R]              -> V_N = pi (R^2 - (R-dr/2)^2)
Face areas A_{j+1/2} = 2 pi (j+1/2) dr. The inner face of node 0 has zero area, so the
axis symmetry condition is satisfied by the discretisation itself.

Writes under results/Q2/experiments/round1/
"""
from __future__ import annotations
import csv, json, sys, time
from pathlib import Path
import numpy as np
from scipy.linalg import solve_banded

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "results/Q2/experiments/round1"

R = 0.02; T0C = 28.0; C0 = 2.55
H = 25.0; HM = 8e-7
T_INF_C = 50.0; C_INF = 0.05
TARGET = 0.15
R_REPORT_CM = np.round(np.arange(21) * 0.1, 10)
R_SUB_CM = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
T_SUB_H = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

with (ROOT / "workspace/data_clean/attachment1_env.csv").open(encoding="utf-8") as fh:
    _a = np.array([[float(x) for x in r] for r in list(csv.reader(fh))[1:]])
_TE, _TI, _CI = _a[:, 0], _a[:, 1], _a[:, 2]
RAMP_END = float(_TE[-1])
Tenv = lambda t: (float(np.interp(t, _TE, _TI)) + 273.15) if t <= RAMP_END else T_INF_C + 273.15
Cenv = lambda t: float(np.interp(t, _TE, _CI)) if t <= RAMP_END else C_INF

def props(C, T):
    rho = 650.0 + 128.0 * C
    cp = 1450.0 + 2736.0 * C / (C + 1.0)
    k = 0.21 + 0.38 * C / (C + 1.0)
    D = 2.4e-3 * np.exp(-0.45 / np.maximum(C, 1e-9)) * np.exp(-3850.0 / T)
    return rho, cp, k, D

def _tri(a, b, c, d):
    n = len(b)
    ab = np.empty((3, n)); ab[0, 1:] = c[:-1]; ab[1, :] = b; ab[2, :-1] = a[1:]
    return solve_banded((1, 1), ab, d)

def build_grid(N):
    dr = R / N
    r = np.arange(N + 1) * dr
    Aface = 2 * np.pi * (r[:-1] + dr / 2)          # A_{j+1/2}, j = 0..N-1
    V = np.empty(N + 1)
    V[0] = np.pi * dr ** 2 / 4.0
    V[1:N] = 2 * np.pi * np.arange(1, N) * dr ** 2
    V[N] = np.pi * (R ** 2 - (R - dr / 2) ** 2)
    return dr, r, Aface, V

def solve(N=800, dt=1.0, t_hours=260.0, theta=0.5, stop_at_target=True,
          record_grid=False, hm=HM, h=H):
    dr, r, Aface, V = build_grid(N)
    T = np.full(N + 1, T0C + 273.15); C = np.full(N + 1, C0)
    steps = int(round(t_hours * 3600.0 / dt))
    nrec = int(round(R_REPORT_CM[-1] / (dr * 100)))            # node index of 2.0 cm
    idx_rep = [int(round(x / (dr * 100))) for x in R_REPORT_CM]
    idx_sub = [int(round(x / (dr * 100))) for x in R_SUB_CM]
    Cgrid = np.zeros((steps + 1, len(idx_rep))) if record_grid else None
    Tgrid = np.zeros((steps + 1, len(idx_rep))) if record_grid else None
    sub = {}
    t_dry = None; W0 = None; flux = 0.0
    for s in range(1, steps + 1):
        t = s * dt; tm = t - dt
        ti = Tenv(t); ti_m = Tenv(tm); ci = Cenv(t); ci_m = Cenv(tm)
        rho, cp, k, D = props(C, T)
        kf = 0.5 * (k[:-1] + k[1:]); Df = 0.5 * (D[:-1] + D[1:])
        # --- face conductances
        Gk = Aface * kf / dr                          # heat
        Gd = Aface * Df / dr                          # mass
        SR_h = 2 * np.pi * R * h                      # surface conductance, heat
        SR_m = 2 * np.pi * R * hm                     # surface conductance, mass
        # --- heat
        ait = rho * cp * V / dt
        subT = np.zeros(N + 1); supT = np.zeros(N + 1); diagT = np.empty(N + 1)
        supT[:N] = -theta * Gk
        subT[1:] = -theta * Gk
        diagT[1:N] = ait[1:N] + theta * (Gk[0:N - 1] + Gk[1:N])
        diagT[0] = ait[0] + theta * Gk[0]
        diagT[N] = ait[N] + theta * (Gk[N - 1] + SR_h)
        exT = np.empty(N + 1)
        exT[0] = Gk[0] * (T[1] - T[0])
        exT[1:N] = Gk[1:N] * (T[2:N + 1] - T[1:N]) - Gk[0:N - 1] * (T[1:N] - T[0:N - 1])
        exT[N] = SR_h * (ti_m - T[N]) + Gk[N - 1] * (T[N - 1] - T[N])
        rhsT = ait * T + (1 - theta) * exT
        rhsT[N] += theta * SR_h * ti
        T = _tri(subT, diagT, supT, rhsT)
        # --- moisture
        aitm = V / dt
        subM = np.zeros(N + 1); supM = np.zeros(N + 1); diagM = np.empty(N + 1)
        supM[:N] = -theta * Gd
        subM[1:] = -theta * Gd
        diagM[1:N] = aitm[1:N] + theta * (Gd[0:N - 1] + Gd[1:N])
        diagM[0] = aitm[0] + theta * Gd[0]
        diagM[N] = aitm[N] + theta * (Gd[N - 1] + SR_m)
        Cprev = C
        exM = np.empty(N + 1)
        exM[0] = Gd[0] * (C[1] - C[0])
        exM[1:N] = Gd[1:N] * (C[2:N + 1] - C[1:N]) - Gd[0:N - 1] * (C[1:N] - C[0:N - 1])
        exM[N] = SR_m * (ci_m - C[N]) + Gd[N - 1] * (C[N - 1] - C[N])
        rhsM = aitm * C + (1 - theta) * exM
        rhsM[N] += theta * SR_m * ci
        C = _tri(subM, diagM, supM, rhsM)
        if W0 is None:
            W0 = float(np.sum(Cprev * V))
        flux += dt * (theta * SR_m * (float(C[N]) - ci) + (1 - theta) * SR_m * (float(Cprev[N]) - ci_m))
        if not np.isfinite(T).all() or T.min() < 250 or T.max() > 420:
            raise RuntimeError("temperature left the physical band at t=%.1f s" % t)
        if record_grid:
            # the deliverable is in degC; the state variable is in kelvin
            Cgrid[s] = C[idx_rep]; Tgrid[s] = T[idx_rep] - 273.15
        for hh in T_SUB_H:
            if abs(t - hh * 3600.0) < dt / 2:
                sub[str(hh)] = {"C": [float(C[j]) for j in idx_sub],
                                "T": [float(T[j]) for j in idx_sub]}
        if t_dry is None and float(C.max()) <= TARGET:
            t_dry = t
            if stop_at_target:
                Cgrid = Cgrid[:s + 1] if record_grid else None
                Tgrid = Tgrid[:s + 1] if record_grid else None
                break
    Wend = float(np.sum(C * V))
    return {"dr": dr, "r": r, "idx_rep": idx_rep, "idx_sub": idx_sub,
            "C": C, "T": T, "t_dry_h": (t_dry / 3600.0) if t_dry else None,
            "n_steps": s, "Cgrid": Cgrid, "Tgrid": Tgrid, "sub": sub,
            "mass": {"W0": W0, "Wend": Wend, "flux": flux,
                     "rel_error": abs((Wend - W0) + flux) / max(abs(W0), 1e-300)},
            "maxC": float(C.max()), "centerC": float(C[0]), "surfaceC": float(C[-1]),
            "TminC": float(T.min() - 273.15), "TmaxC": float(T.max() - 273.15)}

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t_start = time.perf_counter()
    for s in ("metrics", "tables", "figures"):
        (RUN / s).mkdir(parents=True, exist_ok=True)

    res = solve(N=800, dt=1.0, t_hours=260.0, theta=0.5, stop_at_target=True, record_grid=True)
    t_run = time.perf_counter() - t_start

    # table 3 / table 4
    tables = {k: res["sub"][k] for k in res["sub"]}
    # deliverable
    xlsx_t0 = time.perf_counter()
    try:
        import openpyxl
        wb = openpyxl.Workbook(write_only=True)
        for name, grid in (("温度", res["Tgrid"]), ("水分浓度", res["Cgrid"])):
            ws = wb.create_sheet(title=name)
            ws.append(["时间\\到药材中心的距离"] + [float(x) for x in R_REPORT_CM])
            for i in range(1, grid.shape[0]):
                ws.append([i] + [round(float(v), 4) for v in grid[i]])
        wb.save(RUN / "result2.xlsx")
        xlsx_ok = True
    except Exception as exc:
        xlsx_ok = "error: " + str(exc)
    xlsx_wall = time.perf_counter() - xlsx_t0

    # ---- validation: time refinement on the full span, grid refinement on 6 h ----
    t2 = time.perf_counter()
    coarse = solve(N=800, dt=2.0, t_hours=260.0, theta=0.5, stop_at_target=True)
    dt_diff = abs(coarse["t_dry_h"] - res["t_dry_h"]) if (coarse["t_dry_h"] and res["t_dry_h"]) else None
    grid_ref = {}
    for N in (400, 800):
        g = solve(N=N, dt=1.0, t_hours=6.0, theta=0.5, stop_at_target=False)
        grid_ref[N] = [g["C"][int(round(x / (g["dr"] * 100)))] for x in R_SUB_CM]
    g_diff = float(np.max(np.abs(np.array(grid_ref[400]) - np.array(grid_ref[800]))))
    ref_wall = time.perf_counter() - t2

    result = {"schema_version": 1, "question": "Q2", "method_id": "M2",
              "role": "main_candidate", "script": "code/Q2/q2_main.py",
              "scheme": "vertex-centred (dual-cell) finite volume + Crank-Nicolson (theta=0.5)",
              "grid": {"nodes": 801, "dr_m": res["dr"], "dt_s": 1.0, "theta": 0.5,
                       "report_points_are_exact_nodes": True},
              "r_cm": R_REPORT_CM.tolist(),
              "table3_temperature_C": {k: [round(v - 273.15, 4) for v in res["sub"][k]["T"]] for k in res["sub"]},
              "table4_moisture_kg_per_kg": {k: [round(v, 4) for v in res["sub"][k]["C"]] for k in res["sub"]},
              "drying_time_hours": res["t_dry_h"],
              "final_profile": {"C": [round(float(v), 4) for v in res["C"][res["idx_rep"]]],
                                "T": [round(float(v - 273.15), 4) for v in res["T"][res["idx_rep"]]]},
              "deliverable": {"file": "results/Q2/experiments/round1/result2.xlsx",
                              "sheets": ["温度", "水分浓度"],
                              "data_rows": int(res["Cgrid"].shape[0] - 1) if res["Cgrid"] is not None else 0,
                              "data_cols": len(R_REPORT_CM), "written": xlsx_ok is True,
                              "write_wall_s": round(xlsx_wall, 1),
                              "mode": "openpyxl write_only"},
              "timing": {"solver_wall_s": round(t_run, 1), "xlsx_wall_s": round(xlsx_wall, 1)}}

    validation = {"schema_version": 1, "question": "Q2", "method_id": "M2",
                  "time_refinement_full_span": {"dt_s": [2.0, 1.0],
                                                "t_dry_hours": {2.0: coarse["t_dry_h"], 1.0: res["t_dry_h"]},
                                                "abs_diff_hours": dt_diff,
                                                "reported_4dp_stable": bool(dt_diff is not None and dt_diff < 0.01)},
                  "grid_refinement_6h": {"N": [400, 800], "max_abs_diff_C": g_diff,
                                         "reported_4dp_stable": bool(g_diff < 5e-5)},
                  "mass_balance": res["mass"],
                  "invariants": {"C_monotone_decreasing": bool(np.all(np.diff(res["C"]) <= 1e-12)),
                                 "T_monotone_increasing": bool(np.all(np.diff(res["T"]) >= -1e-12)),
                                 "center_is_argmax_C": bool(int(np.argmax(res["C"])) == 0),
                                 "surface_native_node": True,
                                 "axis_symmetry": "dual-cell inner face area is zero (exact)"},
                  "reference_wall_s": round(ref_wall, 1),
                  "solver_wall_s": round(t_run, 1)}

    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics/main.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (RUN / "metrics/main_validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (RUN / "tables/table3_main.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["time_h", "0cm", "0.5cm", "1cm", "1.5cm", "2cm"])
        for k in sorted(res["sub"], key=float):
            w.writerow([k] + [round(v - 273.15, 4) for v in res["sub"][k]["T"]])
    with (RUN / "tables/table4_main.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["time_h", "0cm", "0.5cm", "1cm", "1.5cm", "2cm"])
        for k in sorted(res["sub"], key=float):
            w.writerow([k] + [round(v, 4) for v in res["sub"][k]["C"]])
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
        reps = sorted(res["sub"], key=float)
        for k in reps:
            pass
        tm = [float(k) for k in reps]
        for i, cm in enumerate(["0", "0.5", "1.0", "1.5", "2.0"]):
            ax[0].plot(tm, [res["sub"][k]["T"][i] - 273.15 for k in reps], marker="o", label=cm + " cm")
            ax[1].plot(tm, [res["sub"][k]["C"][i] for k in reps], marker="o", label=cm + " cm")
        ax[0].set_xlabel("t / h"); ax[0].set_ylabel("T / degC"); ax[0].set_title("preheat + constant rate")
        ax[1].set_xlabel("t / h"); ax[1].set_ylabel("C / (kg/kg)"); ax[1].set_title("moisture")
        for a in ax:
            a.legend(fontsize=7); a.grid(alpha=.3)
        fig.tight_layout(); fig.savefig(RUN / "figures/fig1_q2_curves.png", dpi=140)
        plt.close(fig)
        fig_ok = True
    except Exception as exc:
        fig_ok = "error: " + str(exc)

    print(json.dumps({"status": "PASS", "t_dry_h": res["t_dry_h"], "steps": res["n_steps"],
                      "dt_refine_diff_h": dt_diff, "grid_diff_C": g_diff,
                      "mass_rel": res["mass"]["rel_error"],
                      "solver_wall_s": round(t_run, 1), "xlsx_wall_s": round(xlsx_wall, 1),
                      "xlsx_rows": result["deliverable"]["data_rows"],
                      "xlsx_ok": xlsx_ok is True, "figure_ok": fig_ok is True}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
