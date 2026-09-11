# -*- coding: utf-8 -*-
"""Guard for the Q1 role swap (decision q1_method_role_swap).

Re-checks, from the regenerated artifacts, the two safeguards the modeler attached to the
swap:
  (1) the promoted vertex-centred main reproduces the archived pre-swap baseline numbers
      exactly at every reported point and in every shared validation metric;
  (2) the demoted cell-centred baseline reproduces the archived pre-swap main numbers
      exactly, and its numerical core is unchanged at source level.
Also re-measures the deliverable delta against the archived result1.xlsx.

Writes methods/Q1/probes/role_swap_evidence/role_swap_check.json.
"""
from __future__ import annotations
import ast, difflib, json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / "methods/Q1/probes/role_swap_evidence"
RUN = ROOT / "results/Q1/experiments/round1"
R_GRID = np.round(np.arange(21) * 0.1, 10)


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def func_body(path, name):
    src = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            seg = ast.get_source_segment(src, node)
            lines = seg.splitlines()
            i = 0
            while not lines[i].rstrip().endswith(":"):
                i += 1
            return lines[i + 1:]
    raise KeyError(name + " not found in " + str(path))


def line_diff(a, b):
    out = []
    for l in difflib.unified_diff(a, b, lineterm="", n=0):
        if l[:3] in ("+++", "---"):
            continue
        if l[:1] in "+-":
            out.append(l)
    return out


# shared numeric core of the validation objects; role-specific prose keys and
# additional role-specific metrics are excluded on purpose
VAL_CORE = {
    "grid_refinement": ("N", "max_abs_diff_400_vs_800", "reported_4dp_stable"),
    "surface_column_convergence": ("N", "Cs", "richardson_limit", "error_at_N800", "observed_order"),
    "analytical_cross_check": ("max_abs_err", "tolerance", "pass"),
}


def val_core(obj):
    return {k: {kk: (obj.get(k) or {}).get(kk) for kk in keys} for k, keys in VAL_CORE.items()}


def read_xlsx(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = {}
    for name in ("温度", "水分浓度"):
        rows = list(wb[name].iter_rows(values_only=True))[1:]
        out[name] = np.array([[float(v) for v in r[1:]] for r in rows])
    wb.close()
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    checks = []

    def add(name, ok, detail):
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})

    new_main = load(RUN / "metrics/main.json")
    new_mval = load(RUN / "metrics/main_validation.json")
    new_base = load(RUN / "metrics/baseline.json")
    new_bval = load(RUN / "metrics/baseline_validation.json")
    old_base = load(EV / "baseline_pre_swap.json")
    old_bval = load(EV / "baseline_validation_pre_swap.json")
    old_main = load(EV / "main_pre_swap.json")
    old_mval = load(EV / "main_validation_pre_swap.json")

    keys = ("table1_temperature_C", "table2_moisture_kg_per_kg", "final_profile_1800s",
            "reference_case", "r_cm")
    d1 = {k: (new_main.get(k) == old_base.get(k)) for k in keys}
    add("main_reproduces_archived_baseline_reported_values", all(d1.values()), d1)

    d2 = {k: (a == b) for k, a, b in zip(VAL_CORE,
                                       val_core(new_mval).values(),
                                       val_core(old_bval).values())}
    add("main_reproduces_archived_baseline_validation_core", all(d2.values()), d2)

    d3 = {k: (new_base.get(k) == old_main.get(k)) for k in keys}
    add("baseline_reproduces_archived_main_reported_values", all(d3.values()), d3)

    d4 = {k: (a == b) for k, a, b in zip(VAL_CORE,
                                       val_core(new_bval).values(),
                                       val_core(old_mval).values())}
    add("baseline_reproduces_archived_main_validation_core", all(d4.values()), d4)

    body_main = func_body(ROOT / "code/Q1/q1_main.py", "solve_M2")
    body_ref = func_body(EV / "q1_baseline_pre_swap.py", "solve_B1")
    diff_m = line_diff(body_ref, body_main)
    allowed = sum(1 for l in diff_m
                  if "rtol" in l or "atol" in l or "integration failed" in l)
    add("solve_M2_body_matches_archived_solve_B1", allowed == len(diff_m),
        {"differing_lines": diff_m, "n_differing": len(diff_m),
         "note": "differences must be confined to the solver-tolerance arguments and the error-message label"})

    body_base = func_body(ROOT / "code/Q1/q1_baseline.py", "solve_B2")
    body_ref2 = func_body(EV / "q1_main_pre_swap.py", "solve_M1")
    diff_b = line_diff(body_ref2, body_base)
    add("solve_B2_body_identical_to_archived_solve_M1", len(diff_b) == 0,
        {"differing_lines": diff_b, "n_differing": len(diff_b)})

    new_x = read_xlsx(RUN / "result1.xlsx")
    old_x = read_xlsx(EV / "result1_pre_swap.xlsx")
    row = -1.0
    delta = {}
    for name, key in (("moisture", "水分浓度"), ("temperature", "温度")):
        d = np.abs(new_x[key] - old_x[key])
        nz = int((d > 0).sum())
        ij = np.unravel_index(int(np.argmax(d)), d.shape)
        delta[name] = {"cells_changed_at_4dp": nz, "cells_total": int(d.size),
                       "max_abs_diff": float(d.max()),
                       "worst_cell": {"t_s": int(ij[0] + 1), "r_cm": float(R_GRID[ij[1]])}}
        row = max(row, float(d[1799].max()))
    add("deliverable_t1800_row_unchanged", row == 0.0, {"max_abs_diff": row})
    add("deliverable_delta_bounded_to_one_ulp",
        all(v["max_abs_diff"] <= 5.0001e-4 for v in delta.values()), delta)

    ver = load(RUN / "metrics/verifier_validation.json")
    cmp_ = ver["main_vs_baseline_real_problem"]
    lim = ver["convergence_limit_comparison"]
    add("independent_implementations_still_agree",
        bool(cmp_["pass"] and lim["pass"]),
        {"max_abs_diff_moisture": cmp_["max_abs_diff_moisture"],
         "max_abs_diff_temperature": cmp_["max_abs_diff_temperature"],
         "convergence_limits_diff": lim["abs_diff"]})

    status = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
    out = {"schema_version": 1, "question": "Q1", "kind": "role_swap_check",
           "decision_id": "q1_method_role_swap", "status": status, "checks": checks}
    (EV / "role_swap_check.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
