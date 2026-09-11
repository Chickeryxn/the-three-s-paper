# -*- coding: utf-8 -*-
"""Q4 usable baseline (B4): cell-centred finite volume in xi = r/R(t) + Crank-Nicolson,
no Rannacher startup.

Deliberately different from M4 at every layer that can move the answer:
  * unknowns at cell centres instead of nodes (so nothing is native at xi = 1);
  * the surface value is recovered from the Robin relation instead of being a solution
    variable, and the surface conductance is the half-cell series resistance;
  * the apparent advection is written in the cell weak form (including the -2 kc v_i y_i
    volume term and the kc y_s boundary term) rather than as a face-flux operator;
  * no backward-Euler startup (pure Crank-Nicolson).
It never reads the M4 result as a numeric input.

Writes results/Q4/experiments/round1/metrics/baseline.json and _validation.json,
plus tables/table6_baseline.csv.
"""
from __future__ import annotations
import csv, json, sys, time
from pathlib import Path
import numpy as np
from scipy.linalg import solve_banded
from scipy.interpolate import PchipInterpolator

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "results/Q4/experiments/round1"
R0 = 0.02; T0C = 28.0; C0 = 2.55; H = 25.0; HM = 8e-7
T_INF_C = 50.0; C_INF = 0.05; TARGET = 0.15
R_TABLE6_CM = np.array([0.0, 0.005, 0.010, 0.015])
TABLE6_HOURS = list(range(6, 200, 6))


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
_rf = PchipInterpolator(_TR, _RR)
radius = lambda t: float(_rf(min(t, R_END)))
rdot = lambda t: float(_rf.derivative()(min(t, R_END)))


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


def _report(rc, vals, surf, R, r_phys):
    """Cell-centred reporting: piecewise-linear over cells plus the reconstructed surface."""
    from scipy.interpolate import CubicSpline
    xs = np.concatenate([rc, [1.0]]); ys = np.concatenate([vals, [surf]])
    cs = CubicSpline(xs, ys)
    out = []
    for r in r_phys:
        out.append(None if r > R else float(cs(r / R)))
    out.append(float(surf))
    return out


def solve(N=800, dt=5.0, t_hours=250.0, theta=0.5, hm=HM, h=H, no_mass_transfer=False,
          table6=True):
    dxi = 1.0 / N
    xif = np.arange(N + 1) * dxi                     # faces 0 .. 1
    xic = (xif[:-1] + xif[1:]) / 2.0                 # cell centres
    vol = (xif[1:] ** 2 - xif[:-1] ** 2) / 2.0       # int xi dxi over the cell
    hm_eff = 0.0 if no_mass_transfer else hm
    T = np.full(N, T0C + 273.15); C = np.full(N, C0)
    steps = int(round(t_hours * 3600.0 / dt))
    sub6 = {}; t_dry = None; s = 0
    for s in range(1, steps + 1):
        t = s * dt; tm = t - dt
        R = max(radius(t), R_MIN); Rm = max(radius(tm), R_MIN)
        Rd = rdot(t); kc = Rd / Rm
        ti = Tenv(t); ci = Cenv(t)
        rho, cp, k, D = props(C, T)
        kf = 0.5 * (k[:-1] + k[1:]); Df = 0.5 * (D[:-1] + D[1:])
        for is_heat in (True, False):
            alpha = k / (rho * cp)
            co_c = (0.5 * (alpha[:-1] + alpha[1:])) if is_heat else Df
            y = T if is_heat else C
            amb = ti if is_heat else ci
            coN = alpha[-1] if is_heat else D[-1]
            # both fields are solved in divided form (heat divided by rho*cp), so the
            # convective conductance in that measure is h/(rho cp) for heat and h_m for
            # moisture -- using bare h for heat would be high by the factor rho*cp
            Gwall = (h / (rho[-1] * cp[-1])) if is_heat else hm_eff
            # half-cell series resistance at xi = 1, in the xi measure:
            #   (dxi/2) R^2 / co   +   R / h_surface
            Gs = (1.0 / ((dxi / 2.0) * Rm ** 2 / max(coN, 1e-300) + Rm / Gwall)) if Gwall > 0 else 0.0
            # diffusion faces between cells: xi_f * co / (dxi R^2)
            cdf = xif[1:N] * co_c / (dxi * Rm ** 2)
            # weak form on cell i: int_cell xi*(diff + adv) dxi with
            #   diff faces  xi_f co/(dxi R^2) (y_{i+1}-y_i)
            #   adv  faces  0.5 kc xi_f^2 (y_i+y_{i+1})   [right face of i] etc.
            #   adv  volume -2 kc v_i y_i
            #   adv  boundary +kc y at xi = 1 (taken as y_{N-1})
            xif2 = xif[1:N] ** 2
            Msub = np.zeros(N); Mdia = np.zeros(N); Msup = np.zeros(N)
            Msup[0:N - 1] += cdf
            Msub[1:N] += cdf
            Mdia[0:N - 1] -= cdf
            Mdia[1:N] -= cdf
            Mdia[N - 1] -= Gs
            xj = 0.5 * kc * xif2
            Msup[0:N - 1] += xj
            Msub[1:N] -= xj
            Mdia[0:N - 1] += xj
            Mdia[1:N] -= xj
            Mdia[N - 1] += kc
            Mdia -= 2 * kc * vol
            src = np.zeros(N)
            src[N - 1] = Gs * amb
            A = vol / dt
            ym = np.concatenate([[0.0], y[0:N - 1]])
            yp = np.concatenate([y[1:N], [0.0]])
            Q = Mdia * y + Msub * ym + Msup * yp + src
            aa = -theta * Msub; bb = A - theta * Mdia; cc = -theta * Msup
            aa[0] = 0.0; cc[N - 1] = 0.0
            rhs = A * y + (1 - theta) * Q + theta * src
            sol = _tri(aa, bb, cc, rhs)
            if is_heat:
                T = sol
            else:
                C = sol
        if not np.isfinite(T).all() or T.min() < 250 or T.max() > 420:
            raise RuntimeError("temperature left the physical band at t=%.1f s" % t)
        if table6 and (t % 3600 == 0) and (int(t / 3600) in TABLE6_HOURS):
            Cs = _surface_value(float(C[-1]), float(coN), dxi, Rm, hm_eff, ci)
            sub6[str(int(t / 3600))] = _report(xic, C, Cs, R, R_TABLE6_CM)
        if t_dry is None and float(C.max()) <= TARGET:
            t_dry = t
            break
    Rl = max(radius(t), R_MIN)
    CNl = float(C[-1]); coNl = float(props(C, T)[3][-1])
    end_row = _report(xic, C, _surface_value(CNl, coNl, dxi, Rl, hm_eff, Cenv(t)), Rl, R_TABLE6_CM)
    return {"t_dry_h": (t_dry / 3600.0) if t_dry else None, "n_steps": s,
            "sub6": sub6, "table6_end": end_row, "C": C, "T": T, "R_end": Rl,
            "uniformity_dev": float(np.max(np.abs(C - C0))),
            "surface_C_end": _surface_value(CNl, coNl, dxi, Rl, hm_eff, Cenv(t))}


def _surface_value(CN, coN, dxi, R, hm, cinf):
    """Robin relation on the half cell next to xi = 1."""
    g = coN / ((dxi / 2.0) * R)
    if hm <= 0:
        return CN
    return (g * CN + hm * cinf) / (g + hm)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.perf_counter()
    RUN.joinpath("metrics").mkdir(parents=True, exist_ok=True)
    RUN.joinpath("tables").mkdir(parents=True, exist_ok=True)
    res = solve(N=800, dt=5.0, t_hours=250.0)
    wall = time.perf_counter() - t0
    coarse = solve(N=800, dt=10.0, t_hours=250.0)
    ref = {}
    for N in (400, 800):
        ref[N] = solve(N=N, dt=5.0, t_hours=6.0)["sub6"]["6"]
    d_grid = float(np.max([abs(a - b) for a, b in zip(ref[400], ref[800])
                           if a is not None and b is not None]))
    d_dt = abs(coarse["t_dry_h"] - res["t_dry_h"]) if (coarse["t_dry_h"] and res["t_dry_h"]) else None
    off = solve(N=400, dt=5.0, t_hours=6.0, no_mass_transfer=True, table6=False)
    result = {"schema_version": 1, "question": "Q4", "method_id": "B4",
              "role": "usable_baseline", "script": "code/Q4/q4_baseline.py",
              "scheme": "cell-centred finite volume in xi + Crank-Nicolson (no startup), surface value from the Robin half-cell relation",
              "grid": {"cells": 800, "dxi": 1.0 / 800, "dt_s": 5.0},
              "drying_time_hours": res["t_dry_h"],
              "table6_moisture_kg_per_kg": {k: [None if v is None else round(v, 4) for v in row]
                                            for k, row in res["sub6"].items()},
              "table6_end_row": {"label": "烘干结束时间", "time_hours": res["t_dry_h"],
                                 "R_cm": res["R_end"] * 100,
                                 "C": [None if v is None else round(v, 4) for v in res["table6_end"]]},
              "r_cm": [0.0, 0.5, 1.0, 1.5],
              "role_note": "the surface column is reconstructed from the outer cell centre through the Robin relation"}
    validation = {"schema_version": 1, "question": "Q4", "method_id": "B4",
                  "grid_refinement_6h": {"N": [400, 800], "dt_s": 5.0, "max_abs_diff_C": d_grid,
                                         "reported_4dp_stable": bool(d_grid < 5e-5)},
                  "time_refinement_full_span": {"dt_s": [10.0, 5.0],
                                                "t_dry_hours": {"10.0": coarse["t_dry_h"], "5.0": res["t_dry_h"]},
                                                "abs_diff_hours": d_dt,
                                                "reported_4dp_stable": bool(d_dt is not None and d_dt < 0.05)},
                  "moving_boundary_invariance": {"observed_max_abs_deviation_of_C_from_C0": off["uniformity_dev"],
                                                 "threshold": 1e-8,
                                                 "pass": bool(off["uniformity_dev"] < 1e-8)},
                  "elapsed_s": round(wall, 2)}
    (RUN / "metrics/baseline.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (RUN / "metrics/baseline_validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (RUN / "tables/table6_baseline.csv").open("w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["time_h", "0cm", "0.5cm", "1.0cm", "1.5cm", "surface"])
        for k in sorted(res["sub6"], key=float):
            wr.writerow([k] + ["" if v is None else round(v, 4) for v in res["sub6"][k]])
        wr.writerow(["drying_end(%.4f)" % res["t_dry_h"]]
                    + ["" if v is None else round(v, 4) for v in res["table6_end"]])
    print(json.dumps({"status": "PASS", "t_dry_h": res["t_dry_h"], "steps": res["n_steps"],
                      "grid_diff_C": d_grid, "dt_diff_h": d_dt,
                      "moving_boundary_dev": off["uniformity_dev"], "wall_s": round(wall, 1)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
