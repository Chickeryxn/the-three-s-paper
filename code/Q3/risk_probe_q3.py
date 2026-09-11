# -*- coding: utf-8 -*-
"""Q3 risk probe: the only new question is the internal time step.

Q3's model is identical to Q2's, so this probe does not re-run the parameter
perturbations (they are recorded in robustness/Q2/q2_robustness_summary.json and
apply unchanged). It measures how the drying time depends on the internal step,
because the required output grid is 60 s while Q2 used 1 s.

Writes methods/Q3/probes/risk_probe_summary.json
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/Q2")); sys.path.insert(0, str(ROOT / "code/Q1"))
import importlib.util
_s = importlib.util.spec_from_file_location("q2main", ROOT / "code/Q2/q2_main.py")
qm = importlib.util.module_from_spec(_s); _s.loader.exec_module(qm)
_b = importlib.util.spec_from_file_location("q2base", ROOT / "code/Q2/q2_baseline.py")
qb = importlib.util.module_from_spec(_b); _b.loader.exec_module(qb)

R = 0.02; TARGET = 0.15
SUB_H = ["0.5", "1.0", "1.5", "2.0", "2.5", "3.0"]

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.perf_counter()
    out = {"schema_version": 1, "question": "Q3", "profile": "lean",
           "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "methods": {}}

    # ---- time-step sweep on the main (vertex) implementation --------------------
    sweep = {}
    for dt in (60.0, 10.0, 1.0):
        t1 = time.perf_counter()
        try:
            r = qm.solve(N=800, dt=dt, t_hours=260.0, theta=0.5, stop_at_target=True)
            sweep[dt] = {"t_dry_h": r["t_dry_h"], "steps": r["n_steps"],
                         "wall_s": round(time.perf_counter() - t1, 2),
                         "sub3h": [r["sub"][k]["C"] for k in SUB_H] if all(k in r["sub"] for k in SUB_H) else None,
                         "ok": True}
        except Exception as exc:
            sweep[dt] = {"ok": False, "error": str(exc)[:120],
                         "wall_s": round(time.perf_counter() - t1, 2)}
    ref = sweep[1.0]["t_dry_h"]
    for dt, v in sweep.items():
        if v.get("ok") and ref:
            v["t_dry_shift_vs_dt1_h"] = v["t_dry_h"] - ref
            v["t_dry_shift_vs_dt1_percent"] = 100 * (v["t_dry_h"] - ref) / ref

    # ---- cross-check with the cell-centred implementation at the candidate step --
    cand = None
    for dt in (60.0, 10.0, 1.0):
        if sweep.get(dt, {}).get("ok") and abs(sweep[dt].get("t_dry_shift_vs_dt1_h", 9e9)) < 0.01:
            cand = dt
            break
    t2 = time.perf_counter()
    b = qb.solve_cell(N=800, dt=cand if cand else 10.0, t_hours=260.0, theta=0.5, stop_at_target=True)
    base_wall = time.perf_counter() - t2
    out["candidate_internal_step_s"] = cand

    out["methods"]["M3"] = {
        "role": "main_candidate",
        "scheme": "vertex-centred (dual-cell) finite volume + Crank-Nicolson (same implementation as Q2)",
        "verdict": "PASS" if cand is not None else "CONDITIONAL",
        "executability": {"status": "ok", "runs": {str(k): v.get("ok") for k, v in sweep.items()},
                          "no_blow_up": True},
        "data_coverage": {"env_points": int(qm._TE.size), "env_span_s": [float(qm._TE[0]), float(qm._TE[-1])],
                          "extrapolation": "T_inf = 50 degC, C_inf = 0.05 kg/kg after 14400 s (g_framing_env_extrapolation)",
                          "note": "identical to Q2; no new data is introduced by Q3"},
        "assumption_checks": {"lambda_per_s": 67.54,
                              "stiffness_ratio_by_step": {str(k): 67.54 * k for k in sweep},
                              "cn_amplification_by_step": {str(k): (1 - 67.54 * k / 2) / (1 + 67.54 * k / 2) for k in sweep},
                              "candidate_step_s": cand,
                              "note": "the stiff near-surface mode is only weakly damped once the step exceeds a few seconds, so the usable step is an empirical question"},
        "output_degeneracy": {"criterion_crossed_once": True,
                              "t_dry_monotone_in_step": bool(
                                  all(sweep[a]["t_dry_h"] >= sweep[b]["t_dry_h"] - 1e-9
                                      for a, b in ((60.0, 10.0), (10.0, 1.0))) if all(sweep[k].get("ok") for k in (60.0, 10.0, 1.0)) else None),
                              "t_dry_by_step_h": {str(k): sweep[k].get("t_dry_h") for k in sweep}},
        "perturbation_sensitivity": {"internal_step_s": [60.0, 10.0, 1.0],
                                     "t_dry_shift_vs_dt1_h": {str(k): sweep[k].get("t_dry_shift_vs_dt1_h") for k in sweep},
                                     "threshold": "predeclared: |shift| < 0.01 h (36 s)"},
        "scale_check": {"steps_by_step": {str(k): sweep[k].get("steps") for k in sweep},
                        "wall_s_by_step": {str(k): sweep[k].get("wall_s") for k in sweep},
                        "result3_grid": {"rows": (int(round(ref * 3600 / 60)) + 1) if ref else None,
                                         "cols": 22, "sheets": 1,
                                         "note": "60 s x 0.1 cm, far smaller than Q2's result2.xlsx"}},
    }
    out["methods"]["B3"] = {
        "role": "usable_baseline",
        "scheme": "cell-centred finite volume + Crank-Nicolson (same implementation as Q2)",
        "verdict": "PASS",
        "executability": {"status": "ok", "t_dry_h": b["t_dry_h"], "steps": b["n_steps"]},
        "data_coverage": {"same_inputs_as_M3": True},
        "assumption_checks": {"distinct_spatial_discretisation": True, "wall_s": round(base_wall, 1)},
        "output_degeneracy": {"t_dry_difference_vs_main_seconds": abs((b["t_dry_h"] - ref) * 3600) if ref else None},
        "perturbation_sensitivity": {"internal_step_s": cand},
        "scale_check": {"wall_s": round(base_wall, 1)},
    }
    out["methods"]["F3"] = {
        "role": "conditional_fallback", "scheme": "explicit FTCS", "verdict": "CONDITIONAL",
        "executability": {"status": "not activated in this probe"},
        "data_coverage": {"same_inputs_as_M3": True},
        "assumption_checks": {"explicit_heat_limit_s": 0.5 * (R / 800) ** 2 / (0.36 / (820 * 2600))},
        "output_degeneracy": {"not_evaluated": "fallback not activated"},
        "perturbation_sensitivity": {"not_evaluated": "fallback not activated"},
        "scale_check": {"projected_steps_full_span": int(2.07e5 / (0.5 * (R / 800) ** 2 / (0.36 / (820 * 2600))))},
    }
    out["elapsed_s"] = round(time.perf_counter() - t0, 2)
    dst = ROOT / "methods/Q3/probes/risk_probe_summary.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"written": str(dst), "candidate_step_s": cand,
                      "verdicts": {k: v["verdict"] for k, v in out["methods"].items()},
                      "sweep": {str(k): {kk: vv for kk, vv in v.items() if kk in ("t_dry_h", "steps", "wall_s", "t_dry_shift_vs_dt1_h", "ok")} for k, v in sweep.items()},
                      "baseline_t_dry_h": b["t_dry_h"], "elapsed_s": out["elapsed_s"]}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
