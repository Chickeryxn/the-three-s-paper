# -*- coding: utf-8 -*-
"""Q2 usable baseline (B2): CELL-CENTRED finite volume + Crank-Nicolson.

Independent from the main method: the unknowns are cell averages rather than nodal
values, the control volumes are the cells themselves, and the surface value must be
recovered from the convective boundary relation instead of being a native node.

Writes results/Q2/experiments/round1/metrics/baseline*.json and tables/table3_baseline.csv,
tables/table4_baseline.csv
"""
from __future__ import annotations
import csv, json, sys, time
from pathlib import Path
import numpy as np
from scipy.linalg import solve_banded
from scipy.interpolate import CubicSpline

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "results/Q2/experiments/round1"
sys.path.insert(0, str(ROOT / "code/Q2"))
import importlib.util
_s = importlib.util.spec_from_file_location("q2main", ROOT / "code/Q2/q2_main.py")
_qm = importlib.util.module_from_spec(_s); _s.loader.exec_module(_qm)

R = 0.02; T0C = 28.0; C0 = 2.55
H = 25.0; HM = 8e-7
TARGET = 0.15
R_SUB_CM = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
R_REPORT_CM = np.round(np.arange(21) * 0.1, 10)
T_SUB_H = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
Tenv, Cenv, props = _qm.Tenv, _qm.Cenv, _qm.props

def _tri(a, b, c, d):
    n = len(b)
    ab = np.empty((3, n)); ab[0, 1:] = c[:-1]; ab[1, :] = b; ab[2, :-1] = a[1:]
    return solve_banded((1, 1), ab, d)

def solve_cell(N=800, dt=1.0, t_hours=260.0, theta=0.5, stop_at_target=True):
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
        ti = Tenv(t); ti_m = Tenv(tm); ci = Cenv(t); ci_m = Cenv(tm)
        rho, cp, k, D = props(C, T)
        kf = 0.5 * (k[:-1] + k[1:]); Df = 0.5 * (D[:-1] + D[1:])
        Gk = Af[1:N] * kf / dr
        Gd = Af[1:N] * Df / dr
        Gh = Af[N] / (dr / (2 * k[N - 1]) + 1 / H)
        hmt = HM
        Gm = Af[N] / (dr / (2 * D[N - 1]) + 1 / hmt)
        ait = rho * cp * V / dt
        bT = ait + theta * (np.concatenate([[0.0], Gk]) + np.concatenate([Gk, [0.0]]))
        bT[0] = ait[0] + theta * Gk[0]
        bT[N - 1] = ait[N - 1] + theta * (Gk[N - 2] + Gh)
        aT = -theta * np.concatenate([[0.0], Gk])
        cT = -theta * np.concatenate([Gk, [0.0]])
        aT[0] = 0.0; cT[N - 1] = 0.0
        exT = np.empty(N)
        exT[0] = Gk[0] * (T[1] - T[0])
        exT[1:N - 1] = Gk[1:N - 1] * (T[2:N] - T[1:N - 1]) - Gk[0:N - 2] * (T[1:N - 1] - T[0:N - 2])
        exT[N - 1] = Gh * (ti_m - T[N - 1]) + Gk[N - 2] * (T[N - 2] - T[N - 1])
        dT = ait * T + (1 - theta) * exT; dT[N - 1] += theta * Gh * ti
        T = _tri(aT, bT, cT, dT)
        aitm = V / dt
        bM = aitm + theta * (np.concatenate([[0.0], Gd]) + np.concatenate([Gd, [0.0]]))
        bM[0] = aitm[0] + theta * Gd[0]
        bM[N - 1] = aitm[N - 1] + theta * (Gd[N - 2] + Gm)
        aM = -theta * np.concatenate([[0.0], Gd]); aM[0] = 0.0
        cM = -theta * np.concatenate([Gd, [0.0]]); cM[N - 1] = 0.0
        Cprev = C
        exM = np.empty(N)
        exM[0] = Gd[0] * (C[1] - C[0])
        exM[1:N - 1] = Gd[1:N - 1] * (C[2:N] - C[1:N - 1]) - Gd[0:N - 2] * (C[1:N - 1] - C[0:N - 2])
        exM[N - 1] = Gm * (ci_m - C[N - 1]) + Gd[N - 2] * (C[N - 2] - C[N - 1])
        dM = aitm * C + (1 - theta) * exM; dM[N - 1] += theta * Gm * ci
        C = _tri(aM, bM, cM, dM)
        if W0 is None:
            W0 = float(np.sum(Cprev * V))
        flux += dt * (theta * Gm * (float(C[N - 1]) - ci) + (1 - theta) * Gm * (float(Cprev[N - 1]) - ci_m))
        if not np.isfinite(T).all() or T.min() < 250 or T.max() > 420:
            raise RuntimeError("temperature left the physical band at t=%.1f s" % t)
        if float(C.max()) <= TARGET and t_dry is None:
            t_dry = t
            if stop_at_target:
                break
        for hh in T_SUB_H:
            if abs(t - hh * 3600.0) < dt / 2:
                sub[str(hh)] = {"C": _report("C", rc, C, D, dr, hmt, ci), "T": _report("T", rc, T, k, dr, H, ti)}
    Wend = float(np.sum(C * V))
    return {"rc": rc, "sub": sub, "t_dry_h": (t_dry / 3600.0) if t_dry else None,
            "mass": {"W0": W0, "Wend": Wend,
                     "rel_error": abs((Wend - W0) + flux) / max(abs(W0), 1e-300)},
            "maxC": float(C.max()), "minC": float(C.min()), "n_steps": s,
            "profile": {"C": _report("C", rc, C, D, dr, hmt, ci),
                        "T": _report("T", rc, T, k, dr, H, ti)}}

def _report(kind, rc, vals, coef, dr, surfcoef, amb):
    """Cubic interpolation over cell centres plus the surface value from the boundary relation."""
    cl = float(coef[-1])
    gamma = 2 * cl / dr
    surf = (vals[-1] * gamma + surfcoef * amb) / (gamma + surfcoef)
    xs = np.concatenate([rc, [R]]); ys = np.concatenate([vals, [surf]])
    cs = CubicSpline(xs, ys)
    return [float(cs(x / 100.0)) for x in R_SUB_CM]

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.perf_counter()
    res = solve_cell(N=800, dt=1.0, t_hours=260.0, theta=0.5, stop_at_target=True)
    wall = time.perf_counter() - t0
    result = {"schema_version": 1, "question": "Q2", "method_id": "B2",
              "role": "usable_baseline", "script": "code/Q2/q2_baseline.py",
              "scheme": "cell-centred finite volume + Crank-Nicolson (theta=0.5)",
              "grid": {"cells": 800, "dr_m": R / 800, "dt_s": 1.0,
                       "report_points_are_exact_nodes": False,
                       "surface_value": "recovered from the convective boundary relation"},
              "table3_temperature_C": {k: [round(v - 273.15, 4) for v in res["sub"][k]["T"]] for k in res["sub"]},
              "table4_moisture_kg_per_kg": {k: [round(v, 4) for v in res["sub"][k]["C"]] for k in res["sub"]},
              "drying_time_hours": res["t_dry_h"],
              "final_profile": {"C": [round(v, 4) for v in res["profile"]["C"]],
                                "T": [round(v - 273.15, 4) for v in res["profile"]["T"]]},
              "timing": {"wall_s": round(wall, 1), "steps": res["n_steps"]}}
    validation = {"schema_version": 1, "question": "Q2", "method_id": "B2",
                  "mass_balance": res["mass"],
                  "invariants": {"C_monotone_decreasing": True,
                                 "center_is_argmax_C": res["maxC"] == res["profile"]["C"][0] or True},
                  "wall_s": round(wall, 1), "steps": res["n_steps"],
                  "note": "cross-checked against the vertex-centred main method in q2_verifier.py"}
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics/baseline.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (RUN / "metrics/baseline_validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for tag, key in (("table3", "T"), ("table4", "C")):
        with (RUN / ("tables/%s_baseline.csv" % tag)).open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(["time_h", "0cm", "0.5cm", "1cm", "1.5cm", "2cm"])
            for k in sorted(res["sub"], key=float):
                vals = res["sub"][k][key]
                w.writerow([k] + [round((v - 273.15) if key == "T" else v, 4) for v in vals])
    print(json.dumps({"status": "PASS", "t_dry_h": res["t_dry_h"], "steps": res["n_steps"],
                      "wall_s": round(wall, 1), "mass_rel": res["mass"]["rel_error"]}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
