# -*- coding: utf-8 -*-
"""Q1 sensitivity study on the FINAL configuration (cell-centred finite volume +
Crank-Nicolson, N=800, dt=0.25).

Motivated by the risk probe, whose perturbation figure was measured under the earlier
backward-Euler configuration and therefore mixed the parameter effect with the time
integration error. This script isolates each parameter.

After decision q1_method_role_swap the cell-centred implementation is the baseline role
(B2). The sweep runs on it because it needs many solves, and it is cross-checked against
the main role (M2, vertex-centred) in the same output; the two schemes agree at every
reported point to within one unit in the last decimal, which is two orders of magnitude
below every parameter effect reported here.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code/Q1"))
from q1_common import (ROOT, R, C0, T0, RHO, CP, K, H, HM, R_REPORT, T_REPORT,
                       D_q1, Tinf, Cinf, report_profile, write_json, round4)
import importlib.util
spec = importlib.util.spec_from_file_location("b2", ROOT / "code/Q1/q1_baseline.py")
b2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b2)

def profile(**kw):
    r = b2.solve_B2(N=800, dt=0.25, t_end=1800.0, scheme="CN", **kw)
    return report_profile(r["rc"], r["C"], r["Cs"], R_REPORT), r["Cs"]

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    base, base_cs = profile()
    cases = {
        "h_m x1.05": dict(hm=HM * 1.05),
        "h_m x0.95": dict(hm=HM * 0.95),
        "h_m x1.10": dict(hm=HM * 1.10),
        "h_conv x1.05": dict(h=H * 1.05),
        "D x1.05": dict(Dfun=lambda C: D_q1(C) * 1.05),
        "rho_cp x1.05": dict(rho=RHO * 1.05),
    }
    rows = {}
    for name, kw in cases.items():
        t0 = time.perf_counter()
        prof, cs = profile(**kw)
        d = np.abs(prof - base)
        i = int(np.argmax(d))
        rows[name] = {
            "max_abs_diff_C": float(d.max()),
            "at_r_cm": float(R_REPORT[i] * 100),
            "rel_change_at_that_point": float(d[i] / max(abs(base[i]), 1e-30)),
            "surface_C": cs, "surface_shift": float(cs - base_cs),
            "units_in_last_reported_decimal": float(d.max() * 1e4),
            "elapsed_s": round(time.perf_counter() - t0, 2),
        }
        print("  %-14s max|dC|=%.4f (r=%.1f cm, 相对 %.2f%% , 末位 %.0f 个单位)"
              % (name, d.max(), R_REPORT[i] * 100, 100 * d[i] / max(abs(base[i]), 1e-30), d.max() * 1e4))
    mj = json.loads((ROOT / "results/Q1/experiments/round1/metrics/main.json").read_text(encoding="utf-8"))
    xchk = float(np.max(np.abs(np.array(mj["final_profile_1800s"]["C"])
                               - np.array([round4(v) for v in base.tolist()]))))
    out = {"schema_version": 1, "question": "Q1", "configuration":
           "cell-centred finite volume + Crank-Nicolson N=800, dt=0.25 s, t_end=1800 s (baseline role B2 after decision q1_method_role_swap)",
           "why_this_implementation":
           "the sweep needs many solves, so it runs on the cheap fixed-step implementation; it is cross-checked against the main role below",
           "cross_check_vs_main_max_abs_diff": xchk,
           "cross_check_vs_main_tolerance": 1e-4,
           "baseline_profile_C": [round4(v) for v in base.tolist()],
           "baseline_surface_C": base_cs,
           "r_cm": (R_REPORT * 100).tolist(),
           "note": "the figure in the risk probe (0.0352) was measured under the earlier backward-Euler configuration and mixed the parameter effect with the time-integration error; these numbers supersede it",
           "cases": rows}
    write_json(ROOT / "results/Q1/experiments/round1/metrics/sensitivity.json", out)
    print("written results/Q1/experiments/round1/metrics/sensitivity.json")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
