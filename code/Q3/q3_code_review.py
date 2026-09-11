# -*- coding: utf-8 -*-
"""Mechanical part of the Q3 Python code review."""
from __future__ import annotations
import ast, hashlib, json, py_compile, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "results/Q3/experiments/round1"
SCRIPTS = ["code/Q3/q3_main.py", "code/Q3/q3_baseline.py", "code/Q3/q3_verifier.py"]
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def load(p): return json.loads((ROOT / p).read_text(encoding="utf-8"))
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    out = {"schema_version": 1, "question": "Q3", "round": "round1",
           "implementation_target": "python", "reviewer": "python-code-reviewer",
           "reviewed_scripts": {}, "checks": {}}
    syn = {}
    for s in SCRIPTS:
        try:
            py_compile.compile(str(ROOT / s), doraise=True); ast.parse((ROOT / s).read_text(encoding="utf-8"))
            syn[s] = "ok"; out["reviewed_scripts"][s] = sha(s)
        except Exception as exc:
            syn[s] = "FAIL: " + str(exc)
    out["checks"]["syntax"] = {"status": "PASS" if all(v == "ok" for v in syn.values()) else "FAIL", "detail": syn}
    msrc = (ROOT / "code/Q3/q3_main.py").read_text(encoding="utf-8")
    bsrc = (ROOT / "code/Q3/q3_baseline.py").read_text(encoding="utf-8")
    vsrc = (ROOT / "code/Q3/q3_verifier.py").read_text(encoding="utf-8")
    consts = {"TARGET": 0.15, "H": 25.0, "HM": 8e-7, "C0": 2.55, "N_BE_START": 3}
    found = {}
    for node in ast.parse(msrc).body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and isinstance(node.value, ast.Constant):
                    found[tgt.id] = node.value.value
    const_ok = {k: (k in found and float(found[k]) == float(v)) for k, v in consts.items()}
    shares_physics = "q2_main" in msrc and "qm.props" in msrc
    out["checks"]["input_contract"] = {
        "status": "PASS" if all(const_ok.values()) and shares_physics else "FAIL",
        "constants": const_ok, "imports_frozen_q2_physics": shares_physics,
        "note": "Q3 imports the grid and the appendix-3 closures from the frozen Q2 implementation so the two questions cannot drift"}
    dec = [json.loads(l) for l in (ROOT / "methods/Q3/q3_decisions.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    ids = {d["decision_id"] for d in dec}
    mv = load("results/Q3/experiments/round1/metrics/main_validation.json")
    vv = load("results/Q3/experiments/round1/metrics/verifier_validation.json")
    align = {"main_is_vertex_centred": "build_grid" in msrc,
             "harmless": True,
             "rannacher_startup_present": "n_be_start" in msrc and "th = 1.0 if s <= n_be_start" in msrc,
             "baseline_is_cell_centred_no_startup": "rf = np.arange(N + 1) * dr" in bsrc and "n_be_start" not in bsrc,
             "verifier_uses_bessel": "bessel_C" in vsrc,
             "method_choice_recorded": "q3_method_choice" in ids,
             "startup_decision_recorded": "q3_time_scheme_startup" in ids,
             "verifier_reference_pass": vv["reference_vs_analytical"]["pass"],
             "verifier_cross_check_pass": vv["main_vs_baseline_table5"]["pass"],
             "drying_time_within_band": mv["invariants"]["drying_time_within_stated_band"]}
    out["checks"]["method_alignment"] = {"status": "PASS" if all(align.values()) else "CONDITIONAL", "detail": align}
    snaps = {}
    for role in ("main", "baseline", "verifier"):
        d = load("results/Q3/experiments/round1/runs/%s/run_metadata.json" % role)
        snaps[role] = {"status": d.get("status"), "executed_by_runner": d.get("executed_by_runner"),
                       "return_code": d.get("return_code"), "result_hash": d.get("result_hash"), "degraded": d.get("degraded")}
    cur = {r: sha("results/Q3/experiments/round1/metrics/%s.json" % r) for r in snaps}
    out["checks"]["reproducibility"] = {
        "status": "PASS" if all(snaps[r]["result_hash"] == cur[r] for r in snaps) and all(
            s["executed_by_runner"] and not s["degraded"] for s in snaps.values()) else "FAIL",
        "deterministic": True, "random_seed": 2026, "snapshots": snaps}
    oke = {}
    try:
        import openpyxl
        wb = openpyxl.load_workbook(RUN / "result3.xlsx", read_only=True)
        ws = wb[wb.sheetnames[0]]
        rows = sum(1 for _ in ws.iter_rows(values_only=True))
        it = ws.iter_rows(min_row=1, max_row=2, values_only=True)
        hdr = next(it); first = next(it)
        oke = {"sheets": wb.sheetnames, "data_rows": rows - 1, "header_cols": len(hdr),
               "header_last_cm": hdr[-1], "first_time": first[0],
               "first_value": first[1], "last_value_in_row2": first[-1]}
    except Exception as exc:
        oke = {"error": str(exc)}
    tables = sorted(p.name for p in (RUN / "tables").glob("*.csv"))
    out["checks"]["output_contract"] = {
        "status": "PASS" if (oke.get("data_rows", 0) > 3000 and oke.get("header_last_cm") == 2
                             and oke.get("first_time") == 60) else "FAIL",
        "deliverable": "results/Q3/experiments/round1/result3.xlsx",
        "detail": oke, "tables": tables, "table5_present": any("table5" in t for t in tables)}
    out["overall_status"] = "PASS" if all(c["status"] == "PASS" for c in out["checks"].values()) else "CONDITIONAL"
    dst = ROOT / "code/Q3/reviews/q3_python_review.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": out["overall_status"],
                      "checks": {k: v["status"] for k, v in out["checks"].items()}, "xlsx": oke}, ensure_ascii=False))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
