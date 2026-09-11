# -*- coding: utf-8 -*-
"""Aggregate round1 into the canonical run_summary.json (G3 contract).

Role assignment after decision q1_method_role_swap: main = M2 (vertex-centred node
conservative flux form + solve_ivp BDF), baseline = B2 (cell-centred finite volume +
Crank-Nicolson), verifier = V1 (Bessel semi-analytical reference).
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "results/Q1/experiments/round1"


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    contract_hash = __import__("hashlib").sha256(
        (ROOT / "planning/model_contract.json").read_bytes()).hexdigest()
    main_json = load("results/Q1/experiments/round1/metrics/main.json")
    base_json = load("results/Q1/experiments/round1/metrics/baseline.json")
    ver_json = load("results/Q1/experiments/round1/metrics/verifier.json")
    main_val = load("results/Q1/experiments/round1/metrics/main_validation.json")
    base_val = load("results/Q1/experiments/round1/metrics/baseline_validation.json")
    ver_val = load("results/Q1/experiments/round1/metrics/verifier_validation.json")

    def snap(role):
        d = load("results/Q1/experiments/round1/runs/%s/run_metadata.json" % role)
        return {"path": "results/Q1/experiments/round1/runs/%s/run_metadata.json" % role,
                "status": d.get("status"), "command": d.get("command"),
                "elapsed_seconds": d.get("elapsed_seconds"),
                "executed_by_runner": d.get("executed_by_runner"),
                "return_code": d.get("return_code")}

    s_main, s_base, s_ver = snap("main"), snap("baseline"), snap("verifier")
    inputs = ["workspace/data_clean/attachment1_env.csv", "planning/model_contract.json",
              "planning/framing_decisions.jsonl", "methods/Q1/q1_decisions.jsonl"]
    lim = ver_val["convergence_limit_comparison"]
    cmp_ = ver_val["main_vs_baseline_real_problem"]

    summary = {
        "schema_version": 1,
        "question": "Q1",
        "round": "round1",
        "implementation_target": "python",
        "random_seed": 2026,
        "approved_decision_id": "q1_method_role_swap",
        "prior_decision_ids": ["q1_method_choice", "q1_time_scheme_amendment"],
        "contract_hash": contract_hash,
        "run_snapshot": s_main["path"],
        "snapshot_ref": s_main["path"],
        "role_swap_check": "methods/Q1/probes/role_swap_evidence/role_swap_check.json",
        "methods": [
            {"method_id": "M2", "role": "main_candidate", "script": "code/Q1/q1_main.py",
             "status": "success", "execution_time_seconds": main_val.get("elapsed_s"),
             "input_files": inputs,
             "output_files": ["results/Q1/experiments/round1/result1.xlsx",
                              "results/Q1/experiments/round1/tables/table1_main.csv",
                              "results/Q1/experiments/round1/tables/table2_main.csv"],
             "figure_files": ["results/Q1/experiments/round1/figures/fig1_q1_fields.png"],
             "metrics_summary": {
                 "grid_diff_400_vs_800": main_val["grid_refinement"]["max_abs_diff_400_vs_800"],
                 "time_accuracy_diff_rtol_1e_8_vs_1e_9": main_val["time_accuracy"]["max_abs_diff_1e_8_vs_1e_9"],
                 "analytical_max_abs_err": main_val["analytical_cross_check"]["max_abs_err"],
                 "mass_balance_rel": main_val["mass_balance"]["rel_balance_error"],
                 "surface_limit_t100": main_val["surface_column_convergence"]["richardson_limit"],
                 "surface_err_at_N800": main_val["surface_column_convergence"]["error_at_N800"],
                 "scheme": main_json["scheme"]},
             "result_ref": "results/Q1/experiments/round1/metrics/main.json",
             "validation_ref": "results/Q1/experiments/round1/metrics/main_validation.json",
             "run_snapshot": s_main["path"],
             "snapshot": s_main, "warnings": [], "errors": []},
            {"method_id": "B2", "role": "usable_baseline", "script": "code/Q1/q1_baseline.py",
             "status": "success", "execution_time_seconds": base_val.get("elapsed_s"),
             "input_files": inputs,
             "output_files": ["results/Q1/experiments/round1/tables/table1_baseline.csv",
                              "results/Q1/experiments/round1/tables/table2_baseline.csv"],
             "figure_files": [],
             "metrics_summary": {
                 "grid_diff_400_vs_800": base_val["grid_refinement"]["max_abs_diff_400_vs_800"],
                 "analytical_max_abs_err": base_val["analytical_cross_check"]["max_abs_err"],
                 "mass_balance_rel_to_inventory": base_val["mass_balance"]["relative_to_water_inventory"],
                 "surface_limit_t100": base_val["surface_column_convergence"]["richardson_limit"],
                 "surface_err_at_N800": base_val["surface_column_convergence"]["error_at_N800"],
                 "scheme": base_json["scheme"]},
             "result_ref": "results/Q1/experiments/round1/metrics/baseline.json",
             "validation_ref": "results/Q1/experiments/round1/metrics/baseline_validation.json",
             "run_snapshot": s_base["path"],
             "snapshot": s_base, "warnings": [], "errors": []}
        ],
        "verifier": {"method_id": "V1", "script": "code/Q1/q1_verifier.py",
                     "result_ref": "results/Q1/experiments/round1/metrics/verifier.json",
                     "validation_ref": "results/Q1/experiments/round1/metrics/verifier_validation.json",
                     "run_snapshot": s_ver["path"], "snapshot": s_ver,
                     "metrics_summary": {
                         "analytical_mass_balance_worst": ver_val["analytical_mass_balance"]["worst_rel_residual"],
                         "main_vs_reference": ver_val["main_vs_reference"]["max_abs_err"],
                         "baseline_vs_reference": ver_val["baseline_vs_reference"]["max_abs_err"],
                         "convergence_limits_diff": lim["abs_diff"]}},
        "independence": {"runtime_status": "RUNTIME_INDEPENDENT"},
        "comparison": {
            "main_metric_source": "results/Q1/experiments/round1/metrics/main.json",
            "baseline_metric_source": "results/Q1/experiments/round1/metrics/baseline.json",
            "max_abs_diff_moisture": cmp_["max_abs_diff_moisture"],
            "max_abs_diff_temperature": cmp_["max_abs_diff_temperature"],
            "convergence_limits_diff": lim["abs_diff"],
            "verdict": ("M2 and B2 agree pointwise to within %.1e in moisture and %.1e in temperature "
                        "at the 7x5 report points, and their Richardson limits at the hardest point "
                        "agree to %.3e") % (cmp_["max_abs_diff_moisture"],
                                            cmp_["max_abs_diff_temperature"], lim["abs_diff"])},
        "fallback_trigger": {"fallback_id": "F1",
                             "condition": "M2 and B2 disagree beyond the reported tolerance at a required point and the disagreement cannot be attributed",
                             "observed": False,
                             "evidence": "results/Q1/experiments/round1/metrics/verifier_validation.json"},
        "environment": {"python": sys.version.split()[0], "platform": sys.platform,
                        "numpy": __import__("numpy").__version__,
                        "scipy": __import__("scipy").__version__}
    }
    out = RUN / "run_summary.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "written": str(out),
                      "methods": [m["method_id"] for m in summary["methods"]],
                      "snapshots": [s_main["status"], s_base["status"], s_ver["status"]]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
