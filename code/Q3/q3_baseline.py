# -*- coding: utf-8 -*-
"""Q3 usable baseline: cell-centred finite volume + Crank-Nicolson, NO Rannacher startup.

Deliberately differs from the main method in two ways: a different spatial discretisation
(cell-centred vs vertex-centred) and no startup smoothing. It therefore also serves as a
check that the Rannacher startup does not move the answer.

Writes results/Q3/experiments/round1/metrics/baseline*.json and tables/table5_baseline.csv
"""
from __future__ import annotations
import csv, json, sys, time
from pathlib import Path
import numpy as np
from scipy.linalg import solve_banded
from scipy.interpolate import CubicSpline

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "results/Q3/experiments/round1"
sys.path.insert(0, str(ROOT / "code/Q2"))
import importlib.util
_s = importlib.util.spec_from_file_location("q2main", ROOT / "code/Q2/q2_main.py")
qm = importlib.util.module_from_spec(_s); _s.loader.exec_module(qm)

R = 0.02; T0C = 28.0; C0 = 2.55; H = 25.0; HM = 8e-7; TARGET = 0.15
R_SUB_CM = np.array([0.0, 0.5, 1.0, 1.5, 2.0]); SIX_H = 6.0

def _tri(a, b, c, d):
    n = len(b); ab = np.empty((3, n))
    ab[0, 1:] = c[:-1]; ab[1, :] = b; ab[2, :-1] = a[1:]
    return solve_banded((1, 1), ab, d)

def _rep(vals, coef, dr, surfcoef, amb):
    g = 2 * float(coef[-1]) / dr
    surf = (vals[-1] * g + surfcoef * amb) / (g + surfcoef)
    cs = CubicSpline(np.concatenate([np.linspace(dr / 2, R - dr / 2, vals.size), [R]]),
                     np.concatenate([vals, [surf]]))
    return [float(cs(x / 100.0)) for x in R_SUB_CM]

def solve(N=800, dt=1.0, t_hours=260.0, theta=0.5):
    dr = R / N
    rf = np.arange(N + 1) * dr
    Af = 2 * np.pi * rf
    V = np.pi * (rf[1:] ** 2 - rf[:-1] ** 2)
    rc = (rf[1:] + rf[:-1]) / 2
    T = np.full(N, T0C + 273.15); C = np.full(N, C0)
    steps = int(round(t_hours * 3600.0 / dt))
    sub = {}; t_dry = None; W0 = None; flux = 0.0
    for s in range(1, steps + 1):
        t = s * dt; tm = t - dt
        ti = qm.Tenv(t); ti_m = qm.Tenv(tm); ci = qm.Cenv(t); ci_m = qm.Cenv(tm)
        rho, cp, k, D = qm.props(C, T)
        kf = 0.5 * (k[:-1] + k[1:]); Df = 0.5 * (D[:-1] + D[1:])
        Gk = Af[1:N] * kf / dr; Gd = Af[1:N] * Df / dr
        Gh = Af[N] / (dr / (2 * k[N - 1]) + 1 / H)
        Gm = Af[N] / (dr / (2 * D[N - 1]) + 1 / HM)
        for is_heat in (True, False):
            coef = kf if is_heat else Df
            G = Gk if is_heat else Gd
            Gs = Gh if is_heat else Gm
            amb = ti if is_heat else ci
            ambm = ti_m if is_heat else ci_m
            y = T if is_heat else C
            ait = (rho * cp * V / dt) if is_heat else (V / dt)
            b = ait + theta * (np.concatenate([[0.0], G]) + np.concatenate([G, [0.0]]))
            b[0] = ait[0] + theta * G[0]
            b[N - 1] = ait[N - 1] + theta * (G[N - 2] + Gs)
            a = -theta * np.concatenate([[0.0], G]); a[0] = 0.0
            c = -theta * np.concatenate([G, [0.0]]); c[N - 1] = 0.0
            ex = np.empty(N)
            ex[0] = G[0] * (y[1] - y[0])
            ex[1:N - 1] = G[1:N - 1] * (y[2:N] - y[1:N - 1]) - G[0:N - 2] * (y[1:N - 1] - y[0:N - 2])
            ex[N - 1] = Gs * (ambm - y[N - 1]) + G[N - 2] * (y[N - 2] - y[N - 1])
            d = ait * y + (1 - theta) * ex; d[N - 1] += theta * Gs * amb
            sol = _tri(a, b, c, d)
            if is_heat:
                T = sol
            else:
                Cprev = C
                C = sol
                if W0 is None:
                    W0 = float(np.sum(Cprev * V))
                flux += dt * (theta * Gm * (float(C[N - 1]) - ci)
                              + (1 - theta) * Gm * (float(Cprev[N - 1]) - ci_m))
        if not np.isfinite(T).all() or T.min() < 250 or T.max() > 420:
            raise RuntimeError("temperature left the physical band at t=%.1f s" % t)
        if s % int(round(SIX_H * 3600.0 / dt)) == 0:
            sub["%.0f" % (t / 3600.0)] = {"C": _rep(C, D, dr, HM, ci), "T": _rep(T, k, dr, H, ti)}
        if t_dry is None and float(C.max()) <= TARGET:
            t_dry = t; break
    sub["end"] = {"C": _rep(C, D, dr, HM, ci), "T": _rep(T, k, dr, H, ti),
                  "t_hours": (t_dry / 3600.0) if t_dry else None}
    Wend = float(np.sum(C * V))
    return {"sub": sub, "t_dry_h": (t_dry / 3600.0) if t_dry else None, "n_steps": s,
            "mass": {"W0": W0, "Wend": Wend, "rel_error": abs((Wend - W0) + flux) / max(abs(W0), 1e-300)}}

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.perf_counter()
    res = solve(N=800, dt=1.0, t_hours=260.0)
    wall = time.perf_counter() - t0
    rows = sorted([k for k in res["sub"] if k != "end"], key=float)
    result = {"schema_version": 1, "question": "Q3", "method_id": "B3",
              "role": "usable_baseline", "script": "code/Q3/q3_baseline.py",
              "scheme": "cell-centred finite volume + Crank-Nicolson, no Rannacher startup",
              "grid": {"cells": 800, "dr_m": R / 800, "dt_s": 1.0,
                       "report_points_are_exact_nodes": False},
              "drying_time_hours": res["t_dry_h"],
              "table5_moisture_kg_per_kg": {k: [round(v, 4) for v in res["sub"][k]["C"]] for k in rows},
              "table5_end_row": {"time_hours": res["t_dry_h"],
                                 "C": [round(v, 4) for v in res["sub"]["end"]["C"]]},
              "timing": {"wall_s": round(wall, 1), "steps": res["n_steps"]}}
    validation = {"schema_version": 1, "question": "Q3", "method_id": "B3",
                  "mass_balance": res["mass"], "wall_s": round(wall, 1), "steps": res["n_steps"],
                  "note": "cross-checked against the vertex-centred main method in q3_verifier.py"}
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics/baseline.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (RUN / "metrics/baseline_validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (RUN / "tables/table5_baseline.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["time_h", "0cm", "0.5cm", "1cm", "1.5cm", "2cm"])
        for k in rows:
            w.writerow([k] + [round(v, 4) for v in res["sub"][k]["C"]])
        w.writerow(["drying_end(%.4f)" % res["t_dry_h"]]
                   + [round(v, 4) for v in res["sub"]["end"]["C"]])
    print(json.dumps({"status": "PASS", "t_dry_h": res["t_dry_h"], "steps": res["n_steps"],
                      "wall_s": round(wall, 1), "mass_rel": res["mass"]["rel_error"]}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
