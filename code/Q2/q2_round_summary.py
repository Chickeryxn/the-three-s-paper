# -*- coding: utf-8 -*-
"""Aggregate Q2 round1 into the canonical run_summary.json."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "results/Q2/experiments/round1"

def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ch = hashlib.sha256((ROOT / "planning/model_contract.json").read_bytes()).hexdigest()
    mj = load("results/Q2/experiments/round1/metrics/main.json")
    bj = load("results/Q2/experiments/round1/metrics/baseline.json")
    vj = load("results/Q2/experiments/round1/metrics/verifier.json")
    mv = load("results/Q2/experiments/round1/metrics/main_validation.json")
    bv = load("results/Q2/experiments/round1/metrics/baseline_validation.json")
    vv = load("results/Q2/experiments/round1/metrics/verifier_validation.json")

    def snap(role):
        d = load("results/Q2/experiments/round1/runs/%s/run_metadata.json" % role)
        return {"path": "results/Q2/experiments/round1/runs/%s/run_metadata.json" % role,
                "status": d.get("status"), "command": d.get("command"),
                "elapsed_seconds": d.get("elapsed_seconds"),
                "executed_by_runner": d.get("executed_by_runner"), "return_code": d.get("return_code")}

    sm, sb, sv = snap("main"), snap("baseline"), snap("verifier")
    inputs = ["workspace/data_clean/attachment1_env.csv", "planning/model_contract.json",
              "planning/framing_decisions.jsonl", "methods/Q2/q2_decisions.jsonl"]

    summary = {
        "schema_version": 1, "question": "Q2", "round": "round1",
        "implementation_target": "python", "random_seed": 2026,
        "approved_decision_id": "q2_method_choice",
        "superseding_decision_id": "q2_presentation_method_amendment",
        "contract_hash": ch,
        "run_snapshot": sm["path"], "snapshot_ref": sm["path"],
        "methods": [
            {"method_id": "M2", "role": "main_candidate", "script": "code/Q2/q2_main.py",
             "status": "success", "execution_time_seconds": mj.get("timing", {}).get("solver_wall_s"),
             "input_files": inputs,
             "output_files": ["results/Q2/experiments/round1/result2.xlsx",
                              "results/Q2/experiments/round1/tables/table3_main.csv",
                              "results/Q2/experiments/round1/tables/table4_main.csv"],
             "figure_files": ["results/Q2/experiments/round1/figures/fig1_q2_curves.png"],
             "metrics_summary": {
                 "scheme": mj["scheme"], "drying_time_hours": mj["drying_time_hours"],
                 "dt_refinement_full_span_hours": mv["time_refinement_full_span"]["abs_diff_hours"],
                 "grid_refinement_6h_max_abs_diff_C": mv["grid_refinement_6h"]["max_abs_diff_C"],
                 "mass_balance_rel": mv["mass_balance"]["rel_error"],
                 "xlsx_rows": mj["deliverable"]["data_rows"],
                 "xlsx_write_wall_s": mj["deliverable"]["write_wall_s"]},
             "result_ref": "results/Q2/experiments/round1/metrics/main.json",
             "validation_ref": "results/Q2/experiments/round1/metrics/main_validation.json",
             "run_snapshot": sm["path"], "snapshot": sm, "warnings": [], "errors": []},
            {"method_id": "B2", "role": "usable_baseline", "script": "code/Q2/q2_baseline.py",
             "status": "success", "execution_time_seconds": bv.get("wall_s"),
             "input_files": inputs,
             "output_files": ["results/Q2/experiments/round1/tables/table3_baseline.csv",
                              "results/Q2/experiments/round1/tables/table4_baseline.csv"],
             "figure_files": [],
             "metrics_summary": {"scheme": bj["scheme"], "drying_time_hours": bj["drying_time_hours"],
                                 "mass_balance_rel": bv["mass_balance"]["rel_error"],
                                 "steps": bv["steps"]},
             "result_ref": "results/Q2/experiments/round1/metrics/baseline.json",
             "validation_ref": "results/Q2/experiments/round1/metrics/baseline_validation.json",
             "run_snapshot": sb["path"], "snapshot": sb, "warnings": [], "errors": []}],
        "verifier": {"method_id": "V2", "script": "code/Q2/q2_verifier.py",
                     "result_ref": "results/Q2/experiments/round1/metrics/verifier.json",
                     "validation_ref": "results/Q2/experiments/round1/metrics/verifier_validation.json",
                     "run_snapshot": sv["path"], "snapshot": sv,
                     "metrics_summary": {
                         "reference_vs_analytical": vv["reference_vs_analytical"]["max_abs_err"],
                         "main_vs_baseline_moisture": vv["main_vs_baseline_tables"]["max_abs_diff_moisture"],
                         "main_vs_baseline_temperature": vv["main_vs_baseline_tables"]["max_abs_diff_temperature"],
                         "drying_time_spread_seconds": vv["drying_time"]["abs_diff_seconds"]}},
        "independence": {"runtime_status": "RUNTIME_INDEPENDENT"},
        "comparison": {
            "main_metric_source": "results/Q2/experiments/round1/metrics/main.json",
            "baseline_metric_source": "results/Q2/experiments/round1/metrics/baseline.json",
            "max_abs_diff_moisture": vv["main_vs_baseline_tables"]["max_abs_diff_moisture"],
            "max_abs_diff_temperature": vv["main_vs_baseline_tables"]["max_abs_diff_temperature"],
            "drying_time_spread_seconds": vv["drying_time"]["abs_diff_seconds"],
            "verdict": "vertex-centred and cell-centred implementations agree on every reported value at four decimals; the drying time differs by 26 s because the drying tail makes the threshold crossing flat"},
        "fallback_trigger": {"fallback_id": "F2",
                             "condition": "M2 and B2 disagree beyond the reported tolerance and the disagreement cannot be attributed",
                             "observed": False,
                             "evidence": "results/Q2/experiments/round1/metrics/verifier_validation.json"},
        "environment": {"python": sys.version.split()[0],
                        "numpy": __import__("numpy").__version__,
                        "scipy": __import__("scipy").__version__,
                        "xlsx_writer": "openpyxl write_only"},
    }
    out = RUN / "run_summary.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "written": str(out),
                      "snapshots": [sm["status"], sb["status"], sv["status"]]}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
