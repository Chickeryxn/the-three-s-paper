# -*- coding: utf-8 -*-
"""Evidence for the Q1 role swap: what exactly changes in the deliverable result1.xlsx
and in the reported tables when the vertex-centred (node) scheme becomes the main method.

Reads the CURRENT result1.xlsx (produced by the cell-centred M1) and the CURRENT
metrics/baseline.json (produced by the vertex B1), and reports the exact deltas the
swap would introduce. Writes results/Q1/experiments/round1/metrics/role_swap_impact.json.
"""
from __future__ import annotations
import sys, time
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicSpline

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q1_common import ROOT, R, ROUND_DIR, R_GRID, R_REPORT, T_REPORT, write_json, round4
from q1_baseline import solve_B1


def node_report(r, vals, targets):
    cs = CubicSpline(r, vals)
    return np.array([float(cs(x)) for x in targets])


def read_xlsx(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = {}
    for name in ("温度", "水分浓度"):
        ws = wb[name]
        rows = []
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                continue
            rows.append(list(row))
        out[name] = rows
    wb.close()
    return out


def main():
    t0 = time.perf_counter()
    targets = R_GRID / 100.0
    times = list(range(1, 1801))
    N = 800
    r, dr, VN, sol = solve_B1(N=N, t_end=1800.0, t_eval=[float(t) for t in times])
    n = r.size
    Tn = sol.y[:n, :]
    Cn = sol.y[n:, :]
    Cg = np.empty((len(times), targets.size))
    Tg = np.empty((len(times), targets.size))
    for i in range(len(times)):
        Cg[i] = node_report(r, Cn[:, i], targets)
        Tg[i] = node_report(r, Tn[:, i], targets)

    old = read_xlsx(ROUND_DIR / "result1.xlsx")
    oldC = np.array([[float(v) for v in row[1:]] for row in old["水分浓度"]])
    oldT = np.array([[float(v) for v in row[1:]] for row in old["温度"]])
    assert oldC.shape == Cg.shape, (oldC.shape, Cg.shape)
    newC = np.round(Cg, 4); newT = np.round(Tg, 4)

    dC = np.abs(newC - oldC); dT = np.abs(newT - oldT)
    nzC = np.argwhere(dC > 0); nzT = np.argwhere(dT > 0)
    worstC = float(dC.max()); worstT = float(dT.max())
    iC = np.unravel_index(int(np.argmax(dC)), dC.shape) if nzC.size else None
    iT = np.unravel_index(int(np.argmax(dT)), dT.shape) if nzT.size else None

    row1800_C = float(np.abs(newC[1799] - oldC[1799]).max())
    row1800_T = float(np.abs(newT[1799] - oldT[1799]).max())

    # safeguard check: does the NEW main reproduce the archived vertex numbers exactly?
    import json
    b = json.loads((ROUND_DIR / "metrics/baseline.json").read_text(encoding="utf-8"))
    idx = [int(round(x / (R / N))) for x in R_REPORT]
    rep = {}
    exactC = True; exactT = True
    for t in T_REPORT:
        i = times.index(t)
        gotC = [round4(Cn[j, i]) for j in idx]
        gotT = [round4(Tn[j, i]) for j in idx]
        expC = b["table2_moisture_kg_per_kg"][str(t)]
        expT = b["table1_temperature_C"][str(t)]
        exactC = exactC and (gotC == expC)
        exactT = exactT and (gotT == expT)
        rep[str(t)] = {"C_match": gotC == expC, "T_match": gotT == expT}

    out = {
        "schema_version": 1, "question": "Q1", "kind": "role_swap_impact",
        "question_answered": "if the vertex-centred node scheme becomes main and regenerates result1.xlsx, which reported cells move?",
        "grid": {"N": N, "dr_m": dr, "times": [1, 1800], "radii_cm": R_GRID.tolist()},
        "deliverable_delta": {
            "moisture": {"cells_changed_at_4dp": int(nzC.shape[0]), "cells_total": int(dC.size),
                         "max_abs_diff": worstC,
                         "worst_cell": ({"t_s": int(times[iC[0]]), "r_cm": float(R_GRID[iC[1]])} if iC else None),
                         "fraction_changed": float(nzC.shape[0]) / float(dC.size)},
            "temperature": {"cells_changed_at_4dp": int(nzT.shape[0]), "cells_total": int(dT.size),
                            "max_abs_diff": worstT,
                            "worst_cell": ({"t_s": int(times[iT[0]]), "r_cm": float(R_GRID[iT[1]])} if iT else None),
                            "fraction_changed": float(nzT.shape[0]) / float(dT.size)}},
        "row_1800s_delta": {"moisture_max_abs_diff": row1800_C, "temperature_max_abs_diff": row1800_T},
        "safeguard_reproduces_archived_vertex_numbers": {"moisture_exact": bool(exactC),
                                                         "temperature_exact": bool(exactT),
                                                         "per_time": rep},
        "elapsed_s": round(time.perf_counter() - t0, 2),
    }
    write_json(ROUND_DIR / "metrics/role_swap_impact.json", out)
    print(json.dumps({k: out[k] for k in ("deliverable_delta", "row_1800s_delta")}, ensure_ascii=False, indent=2))
    print("safeguard exact:", exactC, exactT, "elapsed", out["elapsed_s"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
