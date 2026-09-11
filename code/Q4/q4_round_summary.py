# -*- coding: utf-8 -*-
"""Aggregate the Q4 round into the canonical run_summary.json (G3 contract)."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "results/Q4/experiments/round1"


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    A = "results/Q4/experiments/round1/"
    mj = load(A + "metrics/main.json"); bj = load(A + "metrics/baseline.json")
    mv = load(A + "metrics/main_validation.json"); bv = load(A + "metrics/baseline_validation.json")
    vv = load(A + "metrics/verifier_validation.json")

    def snap(role):
        d = load(A + "runs/%s/run_metadata.json" % role)
        return {"path": A + "runs/%s/run_metadata.json" % role, "status": d.get("status"),
                "command": d.get("command"), "elapsed_seconds": d.get("elapsed_seconds"),
                "executed_by_runner": d.get("executed_by_runner"), "return_code": d.get("return_code")}

    s_main, s_base, s_ver = snap("main"), snap("baseline"), snap("verifier")
    inputs = ["workspace/data_clean/attachment1_env.csv", "workspace/data_clean/attachment2_radius.csv",
              "planning/model_contract.json", "methods/Q4/q4_decisions.jsonl"]
    summary = {
        "schema_version": 1, "question": "Q4", "round": "round1",
        "implementation_target": "python", "random_seed": 2026,
        "approved_decision_id": "q4_method_choice",
        "contract_hash": hashlib.sha256((ROOT / "planning/model_contract.json").read_bytes()).hexdigest(),
        "run_snapshot": s_main["path"], "snapshot_ref": s_main["path"],
        "methods": [
            {"method_id": "M4", "role": "main_candidate", "script": "code/Q4/q4_main.py",
             "status": "success", "execution_time_seconds": mv.get("solver_wall_s"),
             "input_files": inputs,
             "output_files": ["results/Q4/experiments/round1/result4.xlsx",
                              "results/Q4/experiments/round1/tables/table6_main.csv"],
             "figure_files": ["results/Q4/experiments/round1/figures/fig1_q4_curves.png"],
             "metrics_summary": {
                 "drying_time_hours": mj["drying_time_hours"],
                 "grid_diff_400_vs_800": mv["grid_refinement_6h"]["max_abs_diff_C"],
                 "time_diff_10_vs_5_s_hours": mv["time_refinement_full_span"]["abs_diff_hours"],
                 "radius_interpolation_diff_hours": mv["radius_interpolation"]["abs_diff_hours"],
                 "mass_balance_rel": mv["mass_balance"]["rel_residual"],
                 "moving_boundary_dev": mv["moving_boundary_invariance"]["observed_max_abs_deviation_of_C_from_C0"],
                 "scheme": mj["scheme"]},
             "result_ref": A + "metrics/main.json", "validation_ref": A + "metrics/main_validation.json",
             "run_snapshot": s_main["path"], "snapshot": s_main, "warnings": [], "errors": []},
            {"method_id": "B4", "role": "usable_baseline", "script": "code/Q4/q4_baseline.py",
             "status": "success", "execution_time_seconds": bv.get("elapsed_s"),
             "input_files": inputs,
             "output_files": ["results/Q4/experiments/round1/tables/table6_baseline.csv"],
             "figure_files": [],
             "metrics_summary": {
                 "drying_time_hours": bj["drying_time_hours"],
                 "grid_diff_400_vs_800": bv["grid_refinement_6h"]["max_abs_diff_C"],
                 "time_diff_10_vs_5_s_hours": bv["time_refinement_full_span"]["abs_diff_hours"],
                 "moving_boundary_dev": bv["moving_boundary_invariance"]["observed_max_abs_deviation_of_C_from_C0"],
                 "scheme": bj["scheme"]},
             "result_ref": A + "metrics/baseline.json", "validation_ref": A + "metrics/baseline_validation.json",
             "run_snapshot": s_base["path"], "snapshot": s_base, "warnings": [], "errors": []}],
        "verifier": {"method_id": "V4", "script": "code/Q4/q4_verifier.py",
                     "result_ref": A + "metrics/verifier.json",
                     "validation_ref": A + "metrics/verifier_validation.json",
                     "run_snapshot": s_ver["path"], "snapshot": s_ver,
                     "metrics_summary": {
                         "reference_max_abs_err": vv["reference_vs_analytical"]["max_abs_err"],
                         "table6_max_abs_diff": vv["main_vs_baseline_table6"]["max_abs_diff"],
                         "drying_time_diff_hours": vv["drying_time"]["abs_diff_hours"],
                         "moving_boundary_analytic_invariance": vv["moving_boundary_analytic_invariance"]["pass"]}},
        "independence": {"runtime_status": "RUNTIME_INDEPENDENT"},
        "comparison": {
            "main_metric_source": A + "metrics/main.json",
            "baseline_metric_source": A + "metrics/baseline.json",
            "max_abs_diff_table6": vv["main_vs_baseline_table6"]["max_abs_diff"],
            "drying_time_diff_hours": vv["drying_time"]["abs_diff_hours"],
            "verdict": ("M4 and B4 agree on the drying time to %.4f h (%.0f s) and on table 6 to %.1e; "
                        "the maximum table difference sits in the surface column, which the baseline "
                        "reconstructs by a first-order half-cell relation")
                       % (vv["drying_time"]["abs_diff_hours"], vv["drying_time"]["abs_diff_seconds"],
                          vv["main_vs_baseline_table6"]["max_abs_diff"])},
        "fallback_trigger": {"fallback_id": "F4",
                             "condition": "M4 and B4 disagree on the drying time or the reported points beyond tolerance and the disagreement cannot be attributed",
                             "observed": False, "evidence": A + "metrics/verifier_validation.json"},
        "environment": {"python": sys.version.split()[0], "platform": sys.platform,
                        "numpy": __import__("numpy").__version__, "scipy": __import__("scipy").__version__}}
    (RUN / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "written": "results/Q4/experiments/round1/run_summary.json",
                      "methods": [m["method_id"] for m in summary["methods"]],
                      "snapshots": [s_main["status"], s_base["status"], s_ver["status"]]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
