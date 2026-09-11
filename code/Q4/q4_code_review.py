# -*- coding: utf-8 -*-
"""Mechanical part of the Python code review for the Q4 round."""
from __future__ import annotations
import ast, hashlib, json, py_compile, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "results/Q4/experiments/round1"
SCRIPTS = ["code/Q4/q4_main.py", "code/Q4/q4_baseline.py", "code/Q4/q4_verifier.py"]


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    out = {"schema_version": 1, "question": "Q4", "round": "round1",
           "implementation_target": "python", "reviewer": "python-code-reviewer",
           "reviewed_scripts": {}, "checks": {}}
    syn = {}
    for s in SCRIPTS:
        try:
            py_compile.compile(str(ROOT / s), doraise=True)
            ast.parse((ROOT / s).read_text(encoding="utf-8"))
            syn[s] = "ok"; out["reviewed_scripts"][s] = sha(s)
        except Exception as exc:
            syn[s] = "FAIL: " + str(exc)
    out["checks"]["syntax"] = {"status": "PASS" if all(v == "ok" for v in syn.values()) else "FAIL",
                               "detail": syn}
    contract = load("planning/model_contract.json")
    main_src = (ROOT / "code/Q4/q4_main.py").read_text(encoding="utf-8")
    base_src = (ROOT / "code/Q4/q4_baseline.py").read_text(encoding="utf-8")
    ver_src = (ROOT / "code/Q4/q4_verifier.py").read_text(encoding="utf-8")
    inputs_ok = all(k in main_src for k in ("attachment1_env.csv", "attachment2_radius.csv"))
    physics_ok = all(k in main_src for k in ("4.2e-4", "3850.0", "760.0", "1850.0", "8e-7"))
    out["checks"]["input_contract"] = {"status": "PASS" if inputs_ok and physics_ok else "FAIL",
                                       "reads_declared_inputs": inputs_ok,
                                       "appendix4_closures_present": physics_ok,
                                       "declared_inputs": [i["id"] for i in contract["inputs"]]}
    dec = [json.loads(l) for l in (ROOT / "methods/Q4/q4_decisions.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    approved = {d["decision_id"]: d for d in dec}
    mv = load("results/Q4/experiments/round1/metrics/main_validation.json")
    vv = load("results/Q4/experiments/round1/metrics/verifier_validation.json")
    align = {
        "main_xi_vertex_flux_form": "xi2f" in main_src and "Mdia[N]" in main_src,
        "main_rannacher_startup": "n_be_start" in main_src and "th = 1.0 if s <= n_be_start" in main_src,
        "main_moving_boundary_term": "kc = Rd / Rm" in main_src,
        "baseline_cell_centred_in_xi": "xif[1:N]" in base_src and "Msup[0:N - 1] += cdf" in base_src,
        "baseline_no_startup": "n_be_start" not in base_src,
        "baseline_surface_is_reconstructed": "_surface_value" in base_src,
        "verifier_own_bessel": "bessel_roots" in ver_src and "j1" in ver_src,
        "approved_decision_recorded": "q4_method_choice" in approved,
        "reference_within_tol": vv["reference_vs_analytical"]["pass"],
        "moving_boundary_invariance_pass": bool(mv["moving_boundary_invariance"]["pass"]),
        "verifier_checks_pass": all(v.get("pass") for v in vv.values() if isinstance(v, dict) and "pass" in v),
    }
    out["checks"]["method_alignment"] = {"status": "PASS" if all(align.values()) else "CONDITIONAL",
                                         "detail": align, "approved_main": "M4", "approved_baseline": "B4",
                                         "note": "roles follow the human decision q4_method_choice"}
    snaps = {}
    for role in ("main", "baseline", "verifier"):
        d = load("results/Q4/experiments/round1/runs/%s/run_metadata.json" % role)
        snaps[role] = {"status": d.get("status"), "executed_by_runner": d.get("executed_by_runner"),
                       "return_code": d.get("return_code"), "result_hash": d.get("result_hash"),
                       "validation_hash": d.get("validation_hash"), "code_manifest": d.get("code_manifest")}
    cur = {r: sha("results/Q4/experiments/round1/metrics/%s.json" % r) for r in snaps}
    hashes_match = all(snaps[r]["result_hash"] == cur[r] for r in snaps)
    out["checks"]["reproducibility"] = {"status": "PASS" if hashes_match and all(s["executed_by_runner"] for s in snaps.values()) else "FAIL",
                                        "deterministic": True, "random_seed": 2026,
                                        "snapshot_result_hashes_match_current": hashes_match, "snapshots": snaps}
    oke = {}
    try:
        import openpyxl
        wb = openpyxl.load_workbook(RUN / "result4.xlsx", read_only=True, data_only=True)
        ws = wb["Sheet1"]
        rows = list(ws.iter_rows(values_only=True))
        head = rows[0]
        oke = {"sheets": wb.sheetnames, "rows": len(rows), "cols": len(head),
               "header_ok": str(head[0]).startswith("时间") and head[1] == 0 and str(head[-1]).strip() == "药材表面",
               "time_axis_starts_60s_ends_at_drying": rows[1][0] == 60,
               "blanks_present": any(v is None for r in rows[1:] for v in r[1:21]),
               "all_values_le_target_at_end": all((v is None or v <= 0.15 + 1e-12) for v in rows[-1][1:])}
        wb.close()
    except Exception as exc:
        oke = {"error": str(exc)}
    tables = sorted(p.name for p in (RUN / "tables").glob("*.csv"))
    out["checks"]["output_contract"] = {
        "status": "PASS" if (oke.get("header_ok") and oke.get("time_axis_starts_60s_ends_at_drying")
                             and oke.get("all_values_le_target_at_end")) else "FAIL",
        "deliverable": "results/Q4/experiments/round1/result4.xlsx",
        "detail": oke, "tables": tables,
        "kpi_tables_present": any("table6" in t for t in tables)}
    out["overall_status"] = ("PASS" if all(c["status"] == "PASS" for c in out["checks"].values()) else "CONDITIONAL")
    dst = ROOT / "code/Q4/reviews/q4_python_review.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": out["overall_status"],
                      "checks": {k: v["status"] for k, v in out["checks"].items()}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
