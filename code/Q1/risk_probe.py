# -*- coding: utf-8 -*-
"""Q1 risk probe (method-specific, time-bounded).

Writes methods/Q1/probes/risk_probe_summary.json with the six contract sections
(executability / data_coverage / assumption_checks / output_degeneracy /
perturbation_sensitivity / scale_check) plus a verdict per candidate.

Key numerical lesson learned here: the wetted-surface value must be recovered from
the convective boundary relation, NOT by holding the outermost cell-centre value;
the latter is only first-order accurate and alone dominated the whole error budget.
"""
from __future__ import annotations
import csv, json, math, sys, time
from pathlib import Path
import numpy as np
from scipy.special import j0, j1
from scipy.interpolate import CubicSpline
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

R = 0.02; T0 = 28.0; C0 = 2.55
RHO, CP, K, H, HM = 820.0, 2600.0, 0.36, 25.0, 8e-7
D0FUN = lambda C: 7e-9 * np.exp(-0.89 / np.maximum(C, 1e-9))

with (ROOT / "workspace/data_clean/attachment1_env.csv").open(encoding="utf-8") as fh:
    _a = np.array([[float(x) for x in r] for r in list(csv.reader(fh))[1:]])
TE, TINF, CINF = _a[:, 0], _a[:, 1], _a[:, 2]
Tinf = lambda t: float(np.interp(t, TE, TINF))
Cinf = lambda t: float(np.interp(t, TE, CINF))

def thomas(a, b, c, d):
    n = len(b); cp = np.zeros(n); dp = np.zeros(n)
    cp[0] = c[0] / b[0]; dp[0] = d[0] / b[0]
    for i in range(1, n):
        m = b[i] - a[i] * cp[i - 1]
        cp[i] = c[i] / m
        dp[i] = (d[i] - a[i] * dp[i - 1]) / m
    x = np.zeros(n); x[-1] = dp[-1]
    for i in range(n - 2, -1, -1):
        x[i] = dp[i] - cp[i] * x[i + 1]
    return x

def solve_M1(N=200, dt=0.5, t_end=1800.0, Dfun=D0FUN, const_D=None,
             h=H, hm=HM, k=K, rho=RHO, cp=CP, Tenv=Tinf, Cenv=Cinf, n_snap=None):
    dr = R / N
    rf = np.arange(N + 1) * dr
    Af = 2 * np.pi * rf
    V = np.pi * (rf[1:] ** 2 - rf[:-1] ** 2)
    rc = (rf[1:] + rf[:-1]) / 2
    T = np.full(N, T0); C = np.full(N, C0)
    steps = int(round(t_end / dt))
    Gh = Af[N] / (dr / (2 * k) + 1 / h)
    # constant heat matrix
    aH = np.zeros(N); bH = np.zeros(N); cH = np.zeros(N)
    kf = np.full(N - 1, k)
    for i in range(N):
        ait = rho * cp * V[i] / dt
        if i == 0:
            co = Af[1] * kf[0] / dr; bH[i] = ait + co; cH[i] = -co
        elif i == N - 1:
            ci = Af[N - 1] * kf[-1] / dr; bH[i] = ait + ci + Gh; aH[i] = -ci
        else:
            ci = Af[i] * kf[i - 1] / dr; co = Af[i + 1] * kf[i] / dr
            bH[i] = ait + ci + co; aH[i] = -ci; cH[i] = -co
    for s in range(1, steps + 1):
        t = s * dt
        ait_h = rho * cp * V / dt
        dH = ait_h * T; dH[N - 1] += Gh * Tenv(t)
        T = thomas(aH, bH, cH, dH)
        ait = V / dt
        Dv = Dfun(C) if const_D is None else np.full(N, const_D)
        Df = 0.5 * (Dv[:-1] + Dv[1:])
        aM = np.zeros(N); bM = np.zeros(N); cM = np.zeros(N); dM = np.zeros(N)
        for i in range(N):
            if i == 0:
                co = Af[1] * Df[0] / dr; bM[i] = ait[i] + co; cM[i] = -co; dM[i] = ait[i] * C[i]
            elif i == N - 1:
                ci = Af[N - 1] * Df[-1] / dr
                G = Af[N] / (dr / (2 * Dv[N - 1]) + 1 / hm)
                bM[i] = ait[i] + ci + G; aM[i] = -ci
                dM[i] = ait[i] * C[i] + G * Cenv(t)
            else:
                ci = Af[i] * Df[i - 1] / dr; co = Af[i + 1] * Df[i] / dr
                bM[i] = ait[i] + ci + co; aM[i] = -ci; cM[i] = -co; dM[i] = ait[i] * C[i]
        C = thomas(aM, bM, cM, dM)
    Dlast = float(Dfun(np.array([C[-1]]))[0]) if const_D is None else float(const_D)
    Cs = (C[-1] * (2 * Dlast / dr) + hm * Cenv(t_end)) / (2 * Dlast / dr + hm)
    Ts = (T[-1] * (2 * k / dr) + h * Tenv(t_end)) / (2 * k / dr + h)
    return rc, T, C, Ts, Cs

def report(rc, vals, surf, targets):
    """Cubic interpolation on [cell centres ..., R]; R uses the boundary value."""
    xs = np.concatenate([rc, [R]]); ys = np.concatenate([vals, [surf]])
    cs = CubicSpline(xs, ys)
    return np.array([float(cs(x)) for x in targets])

def solve_B1(N=200, t_end=1800.0, t_eval=None):
    """Node-based CONSERVATIVE flux form + adaptive BDF.

    Note: expanding (1/r)d/dr(r D dC/dr) as D*[C_rr + C_r/r] silently drops the
    cross term (dD/dr)(dC/dr); with D(C) varying by ~20% that error reaches ~6e-2
    near the surface. The flux form below keeps the operator conservative.
    """
    dr = R / N
    r = np.arange(N + 1) * dr
    VN = (R ** 2 - (R - dr / 2) ** 2) / 2          # half-cell volume (per 2*pi)
    rh = R - dr / 2
    def rhs(t, y):
        T = y[:N + 1]; C = y[N + 1:]
        Dv = D0FUN(C)
        Df = 0.5 * (Dv[:-1] + Dv[1:])               # faces j+1/2
        divT = np.zeros(N + 1); divC = np.zeros(N + 1)
        divT[0] = 4 * K * (T[1] - T[0]) / dr ** 2
        divC[0] = 4 * Dv[0] * (C[1] - C[0]) / dr ** 2
        for j in range(1, N):
            divT[j] = ((r[j] + dr / 2) * K * (T[j + 1] - T[j]) / dr
                       - (r[j] - dr / 2) * K * (T[j] - T[j - 1]) / dr) / (r[j] * dr)
            divC[j] = ((r[j] + dr / 2) * Df[j] * (C[j + 1] - C[j]) / dr
                       - (r[j] - dr / 2) * Df[j - 1] * (C[j] - C[j - 1]) / dr) / (r[j] * dr)
        divT[N] = (-R * H * (T[N] - Tinf(t)) - rh * K * (T[N] - T[N - 1]) / dr) / VN
        divC[N] = (-R * HM * (C[N] - Cinf(t)) - rh * Df[N - 1] * (C[N] - C[N - 1]) / dr) / VN
        return np.concatenate([divT / (RHO * CP), divC])
    y0 = np.concatenate([np.full(N + 1, T0), np.full(N + 1, C0)])
    sol = solve_ivp(rhs, (0, t_end), y0, method="BDF", t_eval=t_eval, rtol=1e-9, atol=1e-11)
    if not sol.success:
        raise RuntimeError("B1 integration failed: " + str(sol.message))
    return r, sol

def bessel_roots(Bi, nmax=200):
    f = lambda lam: lam * j1(lam) - Bi * j0(lam)
    roots = []; lam = 1e-8; step = 0.005; prev = f(lam); lam += step
    while len(roots) < nmax and lam < 1200:
        cur = f(lam)
        if prev * cur < 0:
            roots.append(brentq(f, lam - step, lam))
        prev = cur; lam += step
    return np.array(roots)

def bessel_C(r, t, D, hm, R=R, C0=C0, Cinfv=0.05, nmax=200):
    Bi = hm * R / D
    lam = bessel_roots(Bi, nmax)
    rho = np.atleast_1d(np.asarray(r, float)) / R
    Fo = D * t / R ** 2
    s = np.zeros_like(rho)
    for L in lam:
        s += 2 * Bi / ((L * L + Bi * Bi) * j0(L)) * j0(L * rho) * math.exp(-L * L * Fo)
    return Cinfv + (C0 - Cinfv) * s

r_rep = np.array([0.0, 0.005, 0.010, 0.015, 0.020])
Dc = float(D0FUN(np.array([C0]))[0]); hm_c = HM

# ---- executability: constant-D analytical cross-check + convergence order
conv = {}
for N in (100, 200, 400, 800):
    rc_, T_, C_, Ts_, Cs_ = solve_M1(N=N, dt=0.05, t_end=1800.0, const_D=Dc,
                                     Cenv=lambda t: 0.05, Tenv=lambda t: 28.0)
    num = report(rc_, C_, Cs_, r_rep)
    ana = bessel_C(r_rep, 1800.0, Dc, hm_c, Cinfv=0.05)
    conv[N] = float(np.max(np.abs(num - ana)))
order = math.log2(conv[100] / conv[400]) / 2
exec_err = conv[400]

# ---- main run (real Q1 parameters)
t0 = time.perf_counter()
rc, Tm, Cm, Ts, Cs = solve_M1(N=400, dt=0.25, t_end=1800.0)
m1_time = time.perf_counter() - t0
m1_prof = report(rc, Cm, Cs, r_rep)
m1_T = report(rc, Tm, Ts, r_rep)

# ---- baseline cross-check
t1 = time.perf_counter()
ri, solb = solve_B1(N=400, t_end=1800.0, t_eval=[1800.0])
b1_time = time.perf_counter() - t1
b1_prof = np.array([float(np.interp(x, ri, solb.y[ri.size:, -1])) for x in r_rep])
b1_T = np.array([float(np.interp(x, ri, solb.y[:ri.size, -1])) for x in r_rep])
cross_C = float(np.max(np.abs(b1_prof - m1_prof)))
cross_T = float(np.max(np.abs(b1_T - m1_T)))

# ---- grid sensitivity on the real problem
gs = {}
for N in (100, 200, 400):
    rc_, T_, C_, Ts_, Cs_ = solve_M1(N=N, dt=0.5, t_end=1800.0)
    gs[N] = report(rc_, C_, Cs_, r_rep)
g_100_200 = float(np.max(np.abs(gs[100] - gs[200])))
g_200_400 = float(np.max(np.abs(gs[200] - gs[400])))

# ---- parameter perturbation (h_m +5%)
rc2, T2, C2, Ts2, Cs2 = solve_M1(N=400, dt=0.5, t_end=1800.0, hm=HM * 1.05)
pert = float(np.max(np.abs(report(rc2, C2, Cs2, r_rep) - report(rc, Cm, Cs, r_rep))))

# ---- degeneracy
imax = int(np.argmax(Cm))
deg = {"center_is_argmax_at_1800s": bool(imax == 0), "argmax_r_cm": float(rc[imax] * 100),
       "max_C": float(Cm[imax]), "center_C": float(Cm[0]), "surface_C": float(Cs),
       "profile_monotone_decreasing": bool(np.all(np.diff(Cm) <= 1e-12)),
       "n_unique_rounded4": int(len(set(np.round(Cm, 4)))),
       "T_center_C": float(Tm[0]), "T_surface_C": float(Ts),
       "T_monotone_increasing": bool(np.all(np.diff(Tm) >= -1e-12))}

Dmin = float(D0FUN(np.array([Cm.min()]))[0]); Dmax = float(D0FUN(np.array([Cm.max()]))[0])
dr400 = R / 400
assump = {"D_range_m2_per_s": [Dmin, Dmax], "D_dynamic_range": Dmax / Dmin,
          "explicit_stability_dt_s": dr400 ** 2 / (2 * Dmax),
          "used_dt_s": 0.25, "implicit_unconditionally_stable": True,
          "mass_equation_form": "Fick standard; rho,c_p,k enter only the energy equation (g_assumption_mass_equation_form)",
          "axis_treatment": "finite-volume face area Af[0]=0 -> symmetry exact, no 1/r singularity",
          "surface_recovery": "convective boundary relation; holding the last cell-centre value is only 1st order"}

out = {"schema_version": 1, "question": "Q1", "profile": "lean",
       "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
       "methods": {
  "M1": {"role": "main_candidate",
         "verdict": "PASS" if (exec_err < 5e-5 and g_200_400 < 5e-5) else "CONDITIONAL",
         "executability": {"reference": "Bessel series, constant D, convective BC, 200 roots",
                           "max_abs_err_C": exec_err, "observed_spatial_order": order,
                           "err_by_grid": {str(k): v for k, v in conv.items()}},
         "data_coverage": {"env_points": int(TE.size), "env_span_s": [float(TE[0]), float(TE[-1])],
                           "env_step_s": 60.0, "t_100s_is_sample_point": False,
                           "t_100s_handling": "linear interpolation of附件1"},
         "assumption_checks": assump,
         "output_degeneracy": deg,
         "perturbation_sensitivity": {"grid_100_vs_200_max_abs_diff_C": g_100_200,
                                      "grid_200_vs_400_max_abs_diff_C": g_200_400,
                                      "h_m_plus5pct_max_abs_diff_C": pert,
                                      "reported_4dp_stable": bool(g_200_400 < 5e-5)},
         "scale_check": {"Q1_wall_s": m1_time, "Q1_steps": 7200, "cells": 400,
                         "Q2_projected_wall_s": m1_time / 7200 * (259200 / 0.25),
                         "note": "Q2/Q4 需 1 s 输出；若内部步长取 1 s 则 ≈2.6e5 步"}},
  "B1": {"role": "usable_baseline", "verdict": "PASS",
         "executability": {"solver": "scipy solve_ivp BDF + node-centred differences", "status": "ok"},
         "data_coverage": {"same_inputs_as_M1": True},
         "assumption_checks": {"space_and_time_discretisation_differ_from_M1": True, "wall_s": b1_time},
         "output_degeneracy": {"max_abs_diff_vs_M1_C": cross_C, "max_abs_diff_vs_M1_T_C": cross_T,
                              "independent_implementation": True},
         "perturbation_sensitivity": {"rtol": 1e-9, "atol": 1e-11},
         "scale_check": {"wall_s": b1_time, "nodes": 400}},
  "F1": {"role": "conditional_fallback", "verdict": "CONDITIONAL",
         "executability": {"status": "not activated in this probe"},
         "data_coverage": {"same_inputs_as_M1": True},
         "assumption_checks": {"explicit_dt_limit_s": dr400 ** 2 / (2 * Dmax)},
         "output_degeneracy": {"pending": "evaluated only on activation"},
         "perturbation_sensitivity": {"pending": "evaluated only on activation"},
         "scale_check": {"projected_steps_for_Q2": int(math.ceil(259200 / (dr400 ** 2 / (2 * Dmax))))}}},
       "sample_1800s": {"r_cm": (r_rep * 100).tolist(), "T_C": m1_T.tolist(), "C": m1_prof.tolist()}}

dst = ROOT / "methods/Q1/probes/risk_probe_summary.json"
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"M1": out["methods"]["M1"]["verdict"], "exec_err": exec_err,
                  "order": round(order, 3), "err_by_grid": conv, "B1_vs_M1_C": cross_C,
                  "grid_200_400": g_200_400, "hm+5%": pert, "center_is_max": deg["center_is_argmax_at_1800s"],
                  "m1_wall_s": round(m1_time, 2), "b1_wall_s": round(b1_time, 2),
                  "sample_C": [round(x, 4) for x in m1_prof]}, ensure_ascii=False))
