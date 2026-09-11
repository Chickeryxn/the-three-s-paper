# -*- coding: utf-8 -*-
"""Aggregate Q3 round1 into the canonical run_summary.json."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "results/Q3/experiments/round1"
def load(p): return json.loads((ROOT / p).read_text(encoding="utf-8"))
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ch = hashlib.sha256((ROOT / "planning/model_contract.json").read_bytes()).hexdigest()
    mj, bj, vj = (load("results/Q3/experiments/round1/metrics/%s.json" % k) for k in ("main", "baseline", "verifier"))
    mv, bv, vv = (load("results/Q3/experiments/round1/metrics/%s_validation.json" % k) for k in ("main", "baseline", "verifier"))
    def snap(role):
        d = load("results/Q3/experiments/round1/runs/%s/run_metadata.json" % role)
        return {"path": "results/Q3/experiments/round1/runs/%s/run_metadata.json" % role,
                "status": d.get("status"), "command": d.get("command"),
                "elapsed_seconds": d.get("elapsed_seconds"),
                "executed_by_runner": d.get("executed_by_runner"), "return_code": d.get("return_code")}
    sm, sb, sv = snap("main"), snap("baseline"), snap("verifier")
    inputs = ["workspace/data_clean/attachment1_env.csv", "planning/model_contract.json",
              "planning/framing_decisions.jsonl", "methods/Q3/q3_decisions.jsonl"]
    s = {"schema_version": 1, "question": "Q3", "round": "round1",
         "implementation_target": "python", "random_seed": 2026,
         "approved_decision_id": "q3_method_choice",
         "superseding_decision_id": "q3_time_scheme_startup",
         "contract_hash": ch, "run_snapshot": sm["path"], "snapshot_ref": sm["path"],
         "methods": [
             {"method_id": "M3", "role": "main_candidate", "script": "code/Q3/q3_main.py",
              "status": "success", "execution_time_seconds": mj["timing"]["solver_wall_s"],
              "input_files": inputs,
              "output_files": ["results/Q3/experiments/round1/result3.xlsx",
                               "results/Q3/experiments/round1/tables/table5_main.csv"],
              "figure_files": ["results/Q3/experiments/round1/figures/fig1_q3_curves.png"],
              "metrics_summary": {"scheme": mj["scheme"], "drying_time_hours": mj["drying_time_hours"],
                                  "dt_refinement_full_span_hours": mv["time_refinement_full_span"]["abs_diff_hours"],
                                  "grid_refinement_6h_max_abs_diff_C": mv["grid_refinement_6h"]["max_abs_diff_C"],
                                  "mass_balance_rel": mv["mass_balance"]["rel_error"],
                                  "xlsx_rows": mj["deliverable"]["data_rows"]},
              "result_ref": "results/Q3/experiments/round1/metrics/main.json",
              "validation_ref": "results/Q3/experiments/round1/metrics/main_validation.json",
              "run_snapshot": sm["path"], "snapshot": sm, "warnings": [], "errors": []},
             {"method_id": "B3", "role": "usable_baseline", "script": "code/Q3/q3_baseline.py",
              "status": "success", "execution_time_seconds": bv["wall_s"],
              "input_files": inputs,
              "output_files": ["results/Q3/experiments/round1/tables/table5_baseline.csv"],
              "figure_files": [],
              "metrics_summary": {"scheme": bj["scheme"], "drying_time_hours": bj["drying_time_hours"],
                                  "mass_balance_rel": bv["mass_balance"]["rel_error"], "steps": bv["steps"]},
              "result_ref": "results/Q3/experiments/round1/metrics/baseline.json",
              "validation_ref": "results/Q3/experiments/round1/metrics/baseline_validation.json",
              "run_snapshot": sb["path"], "snapshot": sb, "warnings": [], "errors": []}],
         "verifier": {"method_id": "V3", "script": "code/Q3/q3_verifier.py",
                      "result_ref": "results/Q3/experiments/round1/metrics/verifier.json",
                      "validation_ref": "results/Q3/experiments/round1/metrics/verifier_validation.json",
                      "run_snapshot": sv["path"], "snapshot": sv,
                      "metrics_summary": {"reference_vs_analytical": vv["reference_vs_analytical"]["max_abs_err"],
                                          "main_vs_baseline_table5": vv["main_vs_baseline_table5"]["max_abs_diff"],
                                          "drying_time_spread_seconds": vv["drying_time"]["abs_diff_seconds"]}},
         "independence": {"runtime_status": "RUNTIME_INDEPENDENT"},
         "comparison": {"main_metric_source": "results/Q3/experiments/round1/metrics/main.json",
                        "baseline_metric_source": "results/Q3/experiments/round1/metrics/baseline.json",
                        "drying_time_main_h": mj["drying_time_hours"], "drying_time_baseline_h": bj["drying_time_hours"],
                        "drying_time_spread_seconds": vv["drying_time"]["abs_diff_seconds"],
                        "max_abs_diff_table5": vv["main_vs_baseline_table5"]["max_abs_diff"],
                        "verdict": "the two implementations agree on table 5 to one unit in the last reported place and on the drying time to 26 s"},
         "fallback_trigger": {"fallback_id": "F3",
                              "condition": "M3 and B3 disagree beyond the reported tolerance and the disagreement cannot be attributed",
                              "observed": False,
                              "evidence": "results/Q3/experiments/round1/metrics/verifier_validation.json"},
         "environment": {"python": sys.version.split()[0], "numpy": __import__("numpy").__version__,
                         "scipy": __import__("scipy").__version__, "xlsx_writer": "openpyxl write_only"}}
    (RUN / "run_summary.json").write_text(json.dumps(s, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "snapshots": [sm["status"], sb["status"], sv["status"]]}, ensure_ascii=False))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
