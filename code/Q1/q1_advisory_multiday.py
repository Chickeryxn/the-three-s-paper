# -*- coding: utf-8 -*-
"""ADVISORY ONLY: multi-day drying-time sensitivity to h_m, on the Q2/Q3 parameter set.

This is exploratory evidence for the Q1 stability verdict, not a canonical Q3 result.
Q2/Q3 have not passed their own G2/G2.5 gates; their own robustness check will replace
this annex. Configuration follows the human decisions already on record:
  g_framing_env_extrapolation -> T_inf = 50 degC, C_inf = 0.05 kg/kg for the constant-rate stage
  g_framing_convective_coefficients -> h = 25 W/(m2 K), h_m = 8e-7 m/s
  g_assumption_mass_equation_form -> Fick form given by the problem

Writes robustness/Q1/q1_robustness_advisory_multiday.json
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
from scipy.linalg import solve_banded

ROOT = Path(__file__).resolve().parents[2]
R = 0.02; T0 = 28.0; C0 = 2.55
H = 25.0; HM = 8e-7
T_INF = 50.0; C_INF = 0.05
TARGET = 0.15

def _tri(a, b, c, d):
    n = len(b)
    ab = np.empty((3, n))
    ab[0, 1:] = c[:-1]; ab[1, :] = b; ab[2, :-1] = a[1:]
    return solve_banded((1, 1), ab, d)

def props(C, T):
    rho = 650.0 + 128.0 * C
    cp = 1450.0 + 2736.0 * C / (C + 1.0)
    k = 0.21 + 0.38 * C / (C + 1.0)
    D = 2.4e-3 * np.exp(-0.45 / np.maximum(C, 1e-9)) * np.exp(-3850.0 / T)
    return rho, cp, k, D

import csv
with (ROOT / "workspace/data_clean/attachment1_env.csv").open(encoding="utf-8") as fh:
    _a = np.array([[float(x) for x in r] for r in list(csv.reader(fh))[1:]])
_TE, _TI, _CI = _a[:, 0], _a[:, 1], _a[:, 2]
RAMP_END = float(_TE[-1])

def Tenv_of(t):
    """Preheat stage from attachment 1, then the human-decided constant-rate stage.

    Attachment 1 is in degC while the state variable T is in kelvin, so the
    conversion is applied here (mixing the two silently cools the surface).
    """
    return float(np.interp(t, _TE, _TI)) + 273.15 if t <= RAMP_END else T_INF + 273.15

def Cenv_of(t):
    return float(np.interp(t, _TE, _CI)) if t <= RAMP_END else C_INF

def run(N=200, dt=2.0, t_hours=200.0, hm=HM, theta=1.0):
    """theta = 1.0 (backward Euler, L-stable) is used here: over a multi-day horizon the
    stiff near-surface modes are strongly excited by the 28 -> 50 degC ramp, and Crank-Nicolson
    (only A-stable) rings. The first-order time error largely cancels in the h_m ratio that
    this advisory reports; the absolute drying time is indicative only."""
    dr = R / N
    rf = np.arange(N + 1) * dr
    Af = 2 * np.pi * rf
    V = np.pi * (rf[1:] ** 2 - rf[:-1] ** 2)
    rc = (rf[1:] + rf[:-1]) / 2
    Aface = Af[1:N]
    T = np.full(N, T0 + 273.15); C = np.full(N, C0)
    steps = int(round(t_hours * 3600.0 / dt))
    t_dry = None
    t_center = {}
    for s in range(1, steps + 1):
        t = s * dt
        rho, cp, k, D = props(C, T)
        ti = Tenv_of(t); ci_inf = Cenv_of(t); tm = t - dt
        ti_m = Tenv_of(tm); ci_m = Cenv_of(tm)
        # heat
        kh = 0.5 * (k[:-1] + k[1:])
        Kh = Aface * kh / dr
        ciK = np.zeros(N); ciK[1:] = Kh
        coK = np.zeros(N); coK[:N - 1] = Kh
        Gh = Af[N] / (dr / (2 * k[N - 1]) + 1 / H)
        ait_h = rho * cp * V / dt
        Cm = np.empty(N); Cp = np.empty(N)
        Cm[0] = 0.0; Cm[1:] = T[:-1]; Cp[:N - 1] = T[1:]; Cp[N - 1] = 0.0
        exH = ciK * (Cm - T) + coK * (Cp - T)
        exH[0] = coK[0] * (T[1] - T[0])
        exH[N - 1] = ciK[N - 1] * (T[N - 2] - T[N - 1]) + Gh * (ti_m - T[N - 1])
        dH = ait_h * T + (1 - theta) * exH; dH[N - 1] += theta * Gh * ti
        bH = ait_h + theta * (ciK + coK); bH[0] = ait_h[0] + theta * coK[0]
        bH[N - 1] = ait_h[N - 1] + theta * (ciK[N - 1] + Gh)
        aH = -theta * ciK; cH = -theta * coK; aH[0] = 0.0; cH[N - 1] = 0.0
        T = _tri(aH, bH, cH, dH)
        # moisture
        Df = 0.5 * (D[:-1] + D[1:])
        Kd = Aface * Df / dr
        ci = np.zeros(N); ci[1:] = Kd
        co = np.zeros(N); co[:N - 1] = Kd
        G = Af[N] / (dr / (2 * D[N - 1]) + 1 / hm)
        ait = V / dt
        Cm[0] = 0.0; Cm[1:] = C[:-1]; Cp[:N - 1] = C[1:]; Cp[N - 1] = 0.0
        exM = ci * (Cm - C) + co * (Cp - C)
        exM[0] = co[0] * (C[1] - C[0])
        exM[N - 1] = ci[N - 1] * (C[N - 2] - C[N - 1]) + G * (ci_m - C[N - 1])
        dM = ait * C + (1 - theta) * exM; dM[N - 1] += theta * G * ci_inf
        bM = ait + theta * (ci + co); bM[0] = ait[0] + theta * co[0]
        bM[N - 1] = ait[N - 1] + theta * (ci[N - 1] + G)
        aM = -theta * ci; cM = -theta * co; aM[0] = 0.0; cM[N - 1] = 0.0
        C = _tri(aM, bM, cM, dM)
        if t_dry is None and float(C.max()) <= TARGET:
            t_dry = t
        for mark in (6, 12, 24, 48, 72):
            if abs(t - mark * 3600.0) < dt / 2:
                t_center[str(mark)] = {"max_C": float(C.max()), "center_C": float(C[0]),
                                       "center_T_C": float(T[0] - 273.15)}
        if not np.isfinite(T).all() or T.min() < 250.0 or T.max() > 400.0:
            raise RuntimeError("temperature left the physical band at t=%.1f s: T in [%.1f, %.1f]"
                               % (t, float(T.min()), float(T.max())))
        if t_dry is not None:
            break
    return {"t_dry_h": (t_dry / 3600.0) if t_dry else None, "reached": t_dry is not None,
            "marks": t_center, "final_max_C": float(C.max()), "final_center_C": float(C[0])}

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.perf_counter()
    base = run(N=200, dt=2.0, t_hours=200.0, hm=HM)
    plus = run(N=200, dt=2.0, t_hours=200.0, hm=HM * 1.05)
    fine = run(N=200, dt=1.0, t_hours=200.0, hm=HM)
    out = {"schema_version": 1, "status": "ADVISORY_NOT_CANONICAL",
           "purpose": "estimate how strongly the multi-day drying time depends on h_m, for the Q1 stability verdict",
           "configuration": {"properties": "appendix 3", "T_inf_C": T_INF, "C_inf": C_INF,
                             "h_m": HM, "h": H, "target_max_C": TARGET,
                             "N": 200, "dt_s": 2.0, "horizon_h": 200.0,
                             "time_scheme": "backward Euler (L-stable)",
                             "T_inf_ramp": "attachment 1 for t <= 14400 s, then held at 50 degC",
                             "C_inf_ramp": "attachment 1 for t <= 14400 s, then held at 0.05 kg/kg"},
           "h_m_base": base, "h_m_plus5pct": plus, "timestep_check_N200_dt2_5": fine,
           "note": "Q2/Q3 have not passed G2/G2.5; this annex is exploratory and will be replaced by the canonical Q3 robustness check"}
    if base["t_dry_h"] and plus["t_dry_h"]:
        out["sensitivity"] = {"t_dry_h_base": base["t_dry_h"], "t_dry_h_plus5pct": plus["t_dry_h"],
                              "shift_h": plus["t_dry_h"] - base["t_dry_h"],
                              "shift_pct": 100.0 * (plus["t_dry_h"] - base["t_dry_h"]) / base["t_dry_h"]}
    out["elapsed_s"] = round(time.perf_counter() - t0, 2)
    dst = ROOT / "robustness/Q1/q1_robustness_advisory_multiday.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": out["status"], "base": base["t_dry_h"],
                      "plus5pct": plus["t_dry_h"], "fine_grid": fine["t_dry_h"],
                      "base_reached": base["reached"], "mark72": base["marks"].get("72"),
                      "elapsed_s": out["elapsed_s"]}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
