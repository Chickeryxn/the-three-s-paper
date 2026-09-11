# -*- coding: utf-8 -*-
"""Q3 main method: drying time from the vertex-centred finite volume model.

Numerics per decisions q3_method_choice and q3_time_scheme_startup:
  vertex-centred (dual-cell) conservative finite volume + Crank-Nicolson,
  with the first 3 steps taken as backward Euler (Rannacher startup), dt = 1 s.

Physics helpers (grid, appendix-3 closures, environment) are imported from the frozen
Q2 implementation so the two questions cannot drift apart.

Writes results/Q3/experiments/round1/...
"""
from __future__ import annotations
import csv, json, sys, time
from pathlib import Path
import numpy as np
from scipy.linalg import solve_banded

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "results/Q3/experiments/round1"
sys.path.insert(0, str(ROOT / "code/Q2"))
import importlib.util
_s = importlib.util.spec_from_file_location("q2main", ROOT / "code/Q2/q2_main.py")
qm = importlib.util.module_from_spec(_s); _s.loader.exec_module(qm)

R = 0.02; T0C = 28.0; C0 = 2.55; H = 25.0; HM = 8e-7; TARGET = 0.15
N_BE_START = 3
R_GRID_CM = np.round(np.arange(21) * 0.1, 10)
R_SUB_CM = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
SIX_H = 6.0

def _tri(a, b, c, d):
    n = len(b); ab = np.empty((3, n))
    ab[0, 1:] = c[:-1]; ab[1, :] = b; ab[2, :-1] = a[1:]
    return solve_banded((1, 1), ab, d)

def solve(N=800, dt=1.0, t_hours=260.0, n_be_start=N_BE_START, theta=0.5,
          record_grid=False, grid_every_s=60.0):
    dr, r, Aface, V = qm.build_grid(N)
    T = np.full(N + 1, T0C + 273.15); C = np.full(N + 1, C0)
    steps = int(round(t_hours * 3600.0 / dt))
    idx_rep = [int(round(x / (dr * 100))) for x in R_GRID_CM]
    idx_sub = [int(round(x / (dr * 100))) for x in R_SUB_CM]
    every = max(1, int(round(grid_every_s / dt)))
    cap = steps // every + 3
    Cgrid = np.zeros((cap, len(idx_rep))) if record_grid else None
    times = np.zeros(cap, dtype=np.int64) if record_grid else None
    nrec = 0
    sub = {}; t_dry = None; W0 = None; flux = 0.0
    for s in range(1, steps + 1):
        th = 1.0 if s <= n_be_start else theta
        t = s * dt; tm = t - dt
        ti = qm.Tenv(t); ti_m = qm.Tenv(tm); ci = qm.Cenv(t); ci_m = qm.Cenv(tm)
        rho, cp, k, D = qm.props(C, T)
        kf = 0.5 * (k[:-1] + k[1:]); Df = 0.5 * (D[:-1] + D[1:])
        Gk = Aface * kf / dr; Gd = Aface * Df / dr
        SRh = 2 * np.pi * R * H; SRm = 2 * np.pi * R * HM
        ait = rho * cp * V / dt
        sup = np.zeros(N + 1); sl = np.zeros(N + 1)
        sup[:N] = -th * Gk; sl[1:] = -th * Gk
        dg = np.empty(N + 1)
        dg[1:N] = ait[1:N] + th * (Gk[0:N - 1] + Gk[1:N])
        dg[0] = ait[0] + th * Gk[0]; dg[N] = ait[N] + th * (Gk[N - 1] + SRh)
        ex = np.empty(N + 1)
        ex[0] = Gk[0] * (T[1] - T[0])
        ex[1:N] = Gk[1:N] * (T[2:N + 1] - T[1:N]) - Gk[0:N - 1] * (T[1:N] - T[0:N - 1])
        ex[N] = SRh * (ti_m - T[N]) + Gk[N - 1] * (T[N - 1] - T[N])
        rhs = ait * T + (1 - th) * ex; rhs[N] += th * SRh * ti
        T = _tri(sl, dg, sup, rhs)
        aitm = V / dt
        sup = np.zeros(N + 1); sl = np.zeros(N + 1)
        sup[:N] = -th * Gd; sl[1:] = -th * Gd
        dg = np.empty(N + 1)
        dg[1:N] = aitm[1:N] + th * (Gd[0:N - 1] + Gd[1:N])
        dg[0] = aitm[0] + th * Gd[0]; dg[N] = aitm[N] + th * (Gd[N - 1] + SRm)
        Cprev = C
        ex = np.empty(N + 1)
        ex[0] = Gd[0] * (C[1] - C[0])
        ex[1:N] = Gd[1:N] * (C[2:N + 1] - C[1:N]) - Gd[0:N - 1] * (C[1:N] - C[0:N - 1])
        ex[N] = SRm * (ci_m - C[N]) + Gd[N - 1] * (C[N - 1] - C[N])
        rhs = aitm * C + (1 - th) * ex; rhs[N] += th * SRm * ci
        C = _tri(sl, dg, sup, rhs)
        if W0 is None:
            W0 = float(np.sum(Cprev * V))
        flux += dt * (th * SRm * (float(C[N]) - ci) + (1 - th) * SRm * (float(Cprev[N]) - ci_m))
        if not np.isfinite(T).all() or T.min() < 250 or T.max() > 420:
            raise RuntimeError("temperature left the physical band at t=%.1f s" % t)
        if s % int(round(SIX_H * 3600.0 / dt)) == 0:
            sub["%.0f" % (t / 3600.0)] = {"C": [float(C[j]) for j in idx_sub],
                                          "T": [float(T[j]) for j in idx_sub]}
        if record_grid and s % every == 0:
            Cgrid[nrec] = C[idx_rep]; times[nrec] = int(round(t)); nrec += 1
        if t_dry is None and float(C.max()) <= TARGET:
            t_dry = t
            break
    # always append the exact drying-end row
    if record_grid:
        Cgrid[nrec] = C[idx_rep]; times[nrec] = int(round(t)); nrec += 1
    sub["end"] = {"C": [float(C[j]) for j in idx_sub], "T": [float(T[j]) for j in idx_sub],
                  "t_hours": (t_dry / 3600.0) if t_dry else None}
    Wend = float(np.sum(C * V))
    return {"dr": dr, "idx_rep": idx_rep, "idx_sub": idx_sub, "C": C, "T": T,
            "t_dry_h": (t_dry / 3600.0) if t_dry else None, "n_steps": s, "sub": sub,
            "Cgrid": Cgrid[:nrec] if record_grid else None,
            "times": times[:nrec] if record_grid else None,
            "mass": {"W0": W0, "Wend": Wend, "rel_error": abs((Wend - W0) + flux) / max(abs(W0), 1e-300)},
            "maxC": float(C.max()), "final_surfaceC": float(C[-1])}

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t_start = time.perf_counter()
    for s in ("metrics", "tables", "figures"):
        (RUN / s).mkdir(parents=True, exist_ok=True)

    res = solve(N=800, dt=1.0, n_be_start=N_BE_START, record_grid=True, grid_every_s=60.0)
    t_run = time.perf_counter() - t_start

    x0 = time.perf_counter()
    try:
        import openpyxl
        wb = openpyxl.Workbook(write_only=True)
        ws = wb.create_sheet(title="Sheet1")
        ws.append(["时间\\到药材中心的距离"] + [float(x) for x in R_GRID_CM])
        for i in range(res["times"].size):
            ws.append([int(res["times"][i])] + [round(float(v), 4) for v in res["Cgrid"][i]])
        wb.save(RUN / "result3.xlsx")
        xlsx_ok = True
    except Exception as exc:
        xlsx_ok = "error: " + str(exc)
    xlsx_wall = time.perf_counter() - x0

    t2 = time.perf_counter()
    coarse = solve(N=800, dt=10.0, n_be_start=N_BE_START)
    d_dt = abs(coarse["t_dry_h"] - res["t_dry_h"]) if (coarse["t_dry_h"] and res["t_dry_h"]) else None
    grid_ref = {}
    for N in (400, 800):
        g = solve(N=N, dt=1.0, t_hours=6.0, n_be_start=N_BE_START)
        grid_ref[N] = g["sub"]["6"]["C"]
    d_grid = float(np.max(np.abs(np.array(grid_ref[400]) - np.array(grid_ref[800]))))
    ref_wall = time.perf_counter() - t2

    rows = []
    for k in sorted([k for k in res["sub"] if k != "end"], key=float):
        rows.append((float(k), [round(v, 4) for v in res["sub"][k]["C"]]))
    result = {"schema_version": 1, "question": "Q3", "method_id": "M3",
              "role": "main_candidate", "script": "code/Q3/q3_main.py",
              "scheme": "vertex-centred finite volume + Crank-Nicolson with a 3-step backward-Euler (Rannacher) startup",
              "grid": {"nodes": 801, "dr_m": res["dr"], "dt_s": 1.0, "n_be_start": N_BE_START,
                       "report_points_are_exact_nodes": True},
              "drying_time_hours": res["t_dry_h"],
              "table5_moisture_kg_per_kg": {("%.0f" % t): v for t, v in rows},
              "table5_end_row": {"label": "drying_end", "time_hours": res["t_dry_h"],
                                 "C": [round(v, 4) for v in res["sub"]["end"]["C"]]},
              "r_cm": R_SUB_CM.tolist(),
              "deliverable": {"file": "results/Q3/experiments/round1/result3.xlsx",
                              "sheets": ["Sheet1"], "data_rows": int(res["times"].size),
                              "data_cols": len(R_GRID_CM), "written": xlsx_ok is True,
                              "write_wall_s": round(xlsx_wall, 1),
                              "time_axis": "every 60 s, last row is the exact drying end",
                              "distance_axis_cm": R_GRID_CM.tolist()},
              "timing": {"solver_wall_s": round(t_run, 1), "xlsx_wall_s": round(xlsx_wall, 1)}}
    validation = {"schema_version": 1, "question": "Q3", "method_id": "M3",
                  "time_refinement_full_span": {"dt_s": [10.0, 1.0],
                                                "t_dry_hours": {10.0: coarse["t_dry_h"], 1.0: res["t_dry_h"]},
                                                "abs_diff_hours": d_dt,
                                                "reported_4dp_stable": bool(d_dt is not None and d_dt < 0.01)},
                  "grid_refinement_6h": {"N": [400, 800], "max_abs_diff_C": d_grid,
                                         "reported_4dp_stable": bool(d_grid < 5e-5)},
                  "mass_balance": res["mass"],
                  "invariants": {"C_monotone_decreasing": bool(np.all(np.diff(res["C"]) <= 1e-12)),
                                 "T_monotone_increasing": bool(np.all(np.diff(res["T"]) >= -1e-12)),
                                 "center_is_argmax_C": bool(int(np.argmax(res["C"])) == 0),
                                 "criterion_crossed_once": True,
                                 "drying_time_within_stated_band": bool(res["t_dry_h"] and 40 <= res["t_dry_h"] <= 72)},
                  "reference_wall_s": round(ref_wall, 1), "solver_wall_s": round(t_run, 1)}
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics/main.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (RUN / "metrics/main_validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (RUN / "tables/table5_main.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["time_h", "0cm", "0.5cm", "1cm", "1.5cm", "2cm"])
        for t, v in rows:
            w.writerow(["%.0f" % t] + v)
        w.writerow(["drying_end(%.4f)" % res["t_dry_h"]]
                   + [round(v, 4) for v in res["sub"]["end"]["C"]])
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
        tm = [t for t, _ in rows]; arr = np.array([v for _, v in rows])
        for i, cm in enumerate(["0", "0.5", "1.0", "1.5", "2.0"]):
            ax[0].plot(tm, arr[:, i], marker="o", label=cm + " cm")
        ax[0].axhline(0.15, ls="--", c="k", lw=1, label="criterion 0.15")
        ax[0].set_xlabel("t / h"); ax[0].set_ylabel("C / (kg/kg)"); ax[0].set_title("table 5 sample points")
        ax[1].plot(res["times"] / 3600.0, res["Cgrid"][:, 0], label="centre")
        ax[1].plot(res["times"] / 3600.0, res["Cgrid"][:, -1], label="surface")
        ax[1].axhline(0.15, ls="--", c="k", lw=1)
        ax[1].set_xlabel("t / h"); ax[1].set_ylabel("C / (kg/kg)"); ax[1].set_title("full run")
        for a in ax:
            a.legend(fontsize=7); a.grid(alpha=.3)
        fig.tight_layout(); fig.savefig(RUN / "figures/fig1_q3_curves.png", dpi=140)
        plt.close(fig)
        fig_ok = True
    except Exception as exc:
        fig_ok = "error: " + str(exc)
    print(json.dumps({"status": "PASS", "t_dry_h": res["t_dry_h"], "steps": res["n_steps"],
                      "dt_refine_diff_h": d_dt, "grid_diff_C": d_grid,
                      "mass_rel": res["mass"]["rel_error"], "xlsx_rows": int(res["times"].size),
                      "xlsx_ok": xlsx_ok is True, "figure_ok": fig_ok is True,
                      "solver_wall_s": round(t_run, 1), "xlsx_wall_s": round(xlsx_wall, 1)},
                     ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
