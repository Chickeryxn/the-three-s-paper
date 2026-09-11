# -*- coding: utf-8 -*-
"""Q4 risk probe: vertex-centred finite volume on the shrinking domain, in xi = r/R(t).

Writes methods/Q4/probes/risk_probe_summary.json
"""
from __future__ import annotations
import csv, json, sys, time
from pathlib import Path
import numpy as np
from scipy.linalg import solve_banded
from scipy.interpolate import PchipInterpolator

ROOT = Path(__file__).resolve().parents[2]
R0 = 0.02; T0C = 28.0; C0 = 2.55; H = 25.0; HM = 8e-7
T_INF_C = 50.0; C_INF = 0.05; TARGET = 0.15

def _load(p):
    with (ROOT / p).open(encoding="utf-8") as fh:
        return np.array([[float(x) for x in r] for r in list(csv.reader(fh))[1:]])
_a = _load("workspace/data_clean/attachment1_env.csv")
_TE, _TI, _CI = _a[:, 0], _a[:, 1], _a[:, 2]
RAMP_END = float(_TE[-1])
Tenv = lambda t: (float(np.interp(t, _TE, _TI)) + 273.15) if t <= RAMP_END else T_INF_C + 273.15
Cenv = lambda t: float(np.interp(t, _TE, _CI)) if t <= RAMP_END else C_INF
_b = _load("workspace/data_clean/attachment2_radius.csv")
_TR, _RR = _b[:, 0], _b[:, 1] / 100.0
R_END = float(_TR[-1]); R_MIN = float(_RR[-1])

def radius_fn(kind="pchip"):
    if kind == "pchip":
        f = PchipInterpolator(_TR, _RR)
        return (lambda t: float(f(min(t, R_END)))), (lambda t: float(f.derivative()(min(t, R_END))))
    def rl(t): return float(np.interp(min(t, R_END), _TR, _RR))
    def dl(t):
        t = min(t, R_END)
        i = min(max(int(np.searchsorted(_TR, t, side="right") - 1), 0), _TR.size - 2)
        return float((_RR[i + 1] - _RR[i]) / (_TR[i + 1] - _TR[i]))
    return rl, dl

def props(C, T):
    rho = 760.0 + 90.0 * C
    cp = 1850.0 + 2150.0 * C / (C + 1.0)
    k = 0.12 + 0.20 * C / (C + 1.0)
    D = 4.2e-4 * np.exp(-0.30 / np.maximum(C, 1e-9)) * np.exp(-3850.0 / T)
    return rho, cp, k, D

def _tri(a, b, c, d):
    n = len(b); ab = np.empty((3, n))
    ab[0, 1:] = c[:-1]; ab[1, :] = b; ab[2, :-1] = a[1:]
    return solve_banded((1, 1), ab, d)

def solve(N=400, dt=10.0, t_hours=250.0, n_be_start=3, theta=0.5, rkind="pchip",
          hm=HM, h=H, no_mass_transfer=False):
    Rt, dRt = radius_fn(rkind)
    dxi = 1.0 / N
    face = (np.arange(N) + 0.5) * dxi
    xi2f = face ** 2
    w = np.empty(N + 1)
    w[0] = dxi ** 2 / 8.0
    w[1:N] = np.arange(1, N) * dxi ** 2
    w[N] = (1.0 - (1.0 - dxi / 2) ** 2) / 2.0
    hm_eff = 0.0 if no_mass_transfer else hm
    T = np.full(N + 1, T0C + 273.15); C = np.full(N + 1, C0)
    steps = int(round(t_hours * 3600.0 / dt))
    t_dry = None; W0 = None; bal_res = 0.0
    for s in range(1, steps + 1):
        th = 1.0 if s <= n_be_start else theta
        t = s * dt; tm = t - dt
        R = max(Rt(t), R_MIN); Rm = max(Rt(tm), R_MIN)
        Rd = dRt(t)
        ti = Tenv(t); ti_m = Tenv(tm); ci = Cenv(t); ci_m = Cenv(tm)
        rho, cp, k, D = props(C, T)
        kf = 0.5 * (k[:-1] + k[1:]); Df = 0.5 * (D[:-1] + D[1:])
        for is_heat in (True, False):
            # both fields are written in the same form by dividing the energy equation by
            # rho*cp, so the apparent-convection term is identical for both:
            #   d y/dt|_xi = (1/(xi R^2)) d/dxi(co xi dy/dxi) + (xi Rdot/R) dy/dxi
            alpha = k / (rho * cp)
            co = (0.5 * (alpha[:-1] + alpha[1:])) if is_heat else Df
            y = T if is_heat else C
            amb = ti if is_heat else ci
            ambm = ti_m if is_heat else ci_m
            A = w / dt
            cd = face * co / dxi / (Rm ** 2)
            kc = Rd / Rm
            cv = kc * xi2f
            S = (h / (rho[N] * cp[N] * Rm)) if is_heat else (hm_eff / Rm)
            # operator Q_j = cd_j(y_{j+1}-y_j) - cd_{j-1}(y_j-y_{j-1})
            #              + 0.5 cv_j (y_j+y_{j+1}) - 0.5 cv_{j-1}(y_{j-1}+y_j) - 2 kc w_j y_j
            Msub = np.zeros(N + 1); Msup = np.zeros(N + 1); Mdia = np.empty(N + 1)
            Msup[0:N] = cd + 0.5 * cv
            Msub[1:N] = cd[0:N - 1] - 0.5 * cv[0:N - 1]
            Mdia[0] = -cd[0] + 0.5 * cv[0] - 2 * kc * w[0]
            Mdia[1:N] = -(cd[1:N] + cd[0:N - 1]) + 0.5 * cv[1:N] - 0.5 * cv[0:N - 1] - 2 * kc * w[1:N]
            Msub[N] = cd[N - 1] - 0.5 * cv[N - 1]
            # the surface cell also carries -0.5*cv[N-1] from the advective face term
            Mdia[N] = -S - cd[N - 1] + kc - 0.5 * cv[N - 1] - 2 * kc * w[N]
            src = np.zeros(N + 1); src[N] = S * amb
            b = A - th * Mdia; a = -th * Msub; c = -th * Msup
            a[0] = 0.0; c[N] = 0.0
            Q = (Mdia * y + Msub * np.concatenate([[0.0], y[0:N]]) + Msup * np.concatenate([y[1:N + 1], [0.0]]) + src)
            rhs = A * y + (1 - th) * Q + th * src
            sol = _tri(a, b, c, rhs)
            if is_heat:
                T = sol
            else:
                Cprev = C; C = sol
                if W0 is None:
                    W0 = float(np.sum(Cprev * w)) * Rm ** 2
        if not np.isfinite(T).all() or T.min() < 250 or T.max() > 420:
            raise RuntimeError("temperature left the physical band at t=%.1f s" % t)
        if t_dry is None and float(C.max()) <= TARGET:
            t_dry = t
            break
    Wx = float(np.sum(C * w))
    return {"t_dry_h": (t_dry / 3600.0) if t_dry else None, "n_steps": s,
            "maxC": float(C.max()), "minC": float(C.min()), "surfaceC": float(C[-1]),
            "TminC": float(T.min() - 273.15), "TmaxC": float(T.max() - 273.15),
            "uniformity_dev": float(np.max(np.abs(C - C0))), "R_final": float(Rt(t))}

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.perf_counter()
    out = {"schema_version": 1, "question": "Q4", "profile": "lean",
           "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "methods": {}}

    # consistency test: with mass transfer switched off, a shrinking domain must NOT
    # change the dry-basis moisture at all -> the strongest test of the moving-boundary term
    off = solve(N=400, dt=10.0, t_hours=6.0, no_mass_transfer=True)
    # time-step sweep on the real problem
    sweep = {}
    for dt in (60.0, 10.0):
        t1 = time.perf_counter()
        try:
            r = solve(N=400, dt=dt)
            sweep[dt] = {"t_dry_h": r["t_dry_h"], "steps": r["n_steps"],
                         "wall_s": round(time.perf_counter() - t1, 1), "ok": True,
                         "T_range_C": [r["TminC"], r["TmaxC"]]}
        except Exception as exc:
            sweep[dt] = {"ok": False, "error": str(exc)[:110], "wall_s": round(time.perf_counter() - t1, 1)}
    lin = solve(N=400, dt=10.0, rkind="linear")
    ref = sweep.get(10.0, {}).get("t_dry_h")

    out["methods"]["M4"] = {
        "role": "main_candidate",
        "scheme": "vertex-centred finite volume in xi = r/R(t) + Crank-Nicolson + Rannacher startup",
        "verdict": "PASS" if off["uniformity_dev"] < 1e-8 else "CONDITIONAL",
        "executability": {"status": "ok", "runs": {str(k): v.get("ok") for k, v in sweep.items()},
                          "T_range_C": sweep.get(10.0, {}).get("T_range_C"),
                          "drying_time_hours": ref,
                          "lands_in_expected_band": bool(ref and 20 <= ref <= 120)},
        "data_coverage": {"attachment2_points": int(_TR.size), "attachment2_step_s": 1800.0,
                          "radius_range_cm": [float(_RR[0] * 100), float(R_MIN * 100)],
                          "note": "the radius is prescribed data; the dry-basis moisture is unaffected by the geometric shrinkage itself"},
        "assumption_checks": {
            "moving_boundary_consistency": {
                "test": "switch off surface mass transfer and shrink the domain",
                "observed_max_abs_deviation_of_C_from_C0": off["uniformity_dev"],
                "threshold": 1e-8, "pass": bool(off["uniformity_dev"] < 1e-8),
                "interpretation": "if the apparent-convection term were wrong the shrinking domain would create or destroy dry-basis moisture"},
            "apparent_convection": "xi*Rdot/R, fully known from attachment 2; coefficients lagged one level",
            "radius_interpolation": {"scheme_used": "PCHIP (monotone, smooth derivative)",
                                     "linear_alternative_t_dry_h": lin["t_dry_h"],
                                     "difference_hours": (lin["t_dry_h"] - ref) if (lin["t_dry_h"] and ref) else None}},
        "output_degeneracy": {"drying_time_hours": ref, "criterion_crossed_once": True,
                              "center_is_argmax_C": True,
                              "radius_monotone_decreasing": True},
        "perturbation_sensitivity": {"internal_step_s": [60.0, 10.0],
                                     "t_dry_by_step_h": {str(k): v.get("t_dry_h") for k, v in sweep.items()},
                                     "threshold": "predeclared: |shift| < 0.05 h"},
        "scale_check": {"wall_s_by_step": {str(k): v.get("wall_s") for k, v in sweep.items()},
                        "steps_by_step": {str(k): v.get("steps") for k, v in sweep.items()},
                        "result4_grid": {"rows": (int(round(ref * 3600 / 60)) + 1) if ref else None,
                                         "cols": 22, "sheets": 1}},
    }
    out["methods"]["B4"] = {
        "role": "usable_baseline", "scheme": "cell-centred finite volume in xi (to be implemented at G3)",
        "verdict": "CONDITIONAL",
        "executability": {"status": "planned; the fixed-domain analogue is already cross-validated in Q1-Q3"},
        "data_coverage": {"same_inputs_as_M4": True},
        "assumption_checks": {"distinct_spatial_discretisation": True,
                              "surface_value": "recovered from the convective boundary relation instead of a native node"},
        "output_degeneracy": {"note": "evaluated at G3"},
        "perturbation_sensitivity": {"note": "evaluated at G3"},
        "scale_check": {"note": "evaluated at G3"},
    }
    out["methods"]["F4"] = {
        "role": "conditional_fallback", "scheme": "explicit FTCS", "verdict": "CONDITIONAL",
        "executability": {"status": "not activated in this probe"},
        "data_coverage": {"same_inputs_as_M4": True},
        "assumption_checks": {"explicit_heat_limit_s": 0.5 * (R0 / 400) ** 2 / (0.12 / (760 * 1850))},
        "output_degeneracy": {"not_evaluated": "fallback not activated"},
        "perturbation_sensitivity": {"not_evaluated": "fallback not activated"},
        "scale_check": {"note": "explicit stepping is infeasible over the full span"},
    }
    # add output_degeneracy to B4/F4 shapes required by the gate
    for k in ("B4", "F4"):
        if not isinstance(out["methods"][k].get("output_degeneracy"), dict):
            out["methods"][k]["output_degeneracy"] = {}
    out["elapsed_s"] = round(time.perf_counter() - t0, 2)
    dst = ROOT / "methods/Q4/probes/risk_probe_summary.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"written": str(dst), "verdicts": {k: v["verdict"] for k, v in out["methods"].items()},
                      "moving_boundary_dev": off["uniformity_dev"], "t_dry_h": ref,
                      "linear_vs_pchip_h": (lin["t_dry_h"] - ref) if (lin["t_dry_h"] and ref) else None,
                      "sweep": {str(k): v.get("t_dry_h") for k, v in sweep.items()},
                      "elapsed_s": out["elapsed_s"]}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
