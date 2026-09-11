# Q4 稳健性报告（submission 口径）

> 由 `robustness/Q4/q4_robustness_summary.json` 生成；该 summary 即 lean 口径的稳健性证据。
> 生成脚本：`code/robustness_report.py`。所有数值均从源文件读取，未手写。

## 1. 范围与口径

- 提供者角色：`robustness-checker`；消费方：G4 稳定性判定、论文的局限段。
- 检验目标：本题的承重假设与已确认口径，而非通用清单。
- 判读口径：**单项扰动下的可观测后果**，不是统计显著性检验。

## 2. 基准状态

| 项 | 值 |
|---|---|
| t_dry_hours | 52.64 |
| dt_s | 5 |
| steps | 37898 |
| mass_rel_residual | 2.557e-14 |

## 3. 逐项检验

| 检验 | 判定 | 观测量 |
|---|---|---|
| `h_m_perturbation/plus5pct` | PASS | {'t_dry_hours': 52.50833333333333, 't_dry_shift_hours': -0.12777777777778, 't_dry_shift_percent': -0.24275687371365662, 'max_abs_diff_table_C': nan, 'compared_r |
| `h_m_perturbation/minus5pct` | PASS | {'t_dry_hours': 52.78055555555556, 't_dry_shift_hours': 0.1444444444444457, 't_dry_shift_percent': 0.27442081376326166, 'max_abs_diff_table_C': nan, 'compared_r |
| `h_conv_perturbation/plus5pct` | PASS | {'t_dry_hours': 52.63333333333333, 't_dry_shift_hours': -0.0027777777777799884, 't_dry_shift_percent': -0.005277323341605339, 'max_abs_diff_table_C': nan, 'comp |
| `D_perturbation` | CONDITIONAL | {'t_dry_hours': 50.46388888888889, 't_dry_shift_hours': -2.1722222222222243, 't_dry_shift_percent': -4.126866853132095, 'max_abs_diff_table_C': nan, 'compared_r |
| `mass_equation_form` | CONDITIONAL | {'t_dry_hours': 43.41111111111111, 't_dry_shift_hours': -9.225000000000001, 't_dry_shift_percent': -17.525990817457387, 'max_abs_diff_table_C': nan, 'compared_r |
| `env_extrapolation_c_inf_0.045` | PASS | {'t_dry_hours': 52.53333333333333, 't_dry_shift_hours': -0.10277777777778141, 't_dry_shift_percent': -0.19526096363924908, 'max_abs_diff_table_C': nan, 'compare |
| `env_extrapolation_c_inf_0.055` | PASS | {'t_dry_hours': 52.766666666666666, 't_dry_shift_hours': 0.13055555555555287, 't_dry_shift_percent': 0.24803419705524846, 'max_abs_diff_table_C': nan, 'compared |
| `env_extrapolation_t_inf_52` | CONDITIONAL | {'t_dry_hours': 49.50555555555555, 't_dry_shift_hours': -3.13055555555556, 't_dry_shift_percent': -5.947543405984493, 'max_abs_diff_table_C': nan, 'compared_row |
| `numerical_discretisation` | PASS | {'grid_6h_max_abs_diff_C': 2.116968417231746e-06, 'dt_full_span_shift_hours': 0.0, 'radius_kind_shift_hours': 0.002777777777772883} |
| `moving_boundary_consistency` | PASS | {'main': 1.4166445794216997e-13, 'baseline': 9.370282327836321e-14} |
| `independent_implementation` | PASS | {'max_abs_diff_table_C': 0.00040000000000006697, 'drying_time_spread_hours': 0.0041666666666699825, 'reference_max_abs_err_vs_bessel': 1.153605800663371e-06} |
| `mass_balance` | PASS | 2.557e-14 |
| `output_degeneracy` | PASS | {'C_monotone_decreasing': True, 'center_is_global_max': True, 'final_max_C': 0.14999961879687534, 'target': 0.15, 'n_unique_4dp_in_final_profile': 508, 'drying_ |
| `end_face_neglect` | CONDITIONAL | {'span_hours': 52.63611111111111, 'axial_heat_penetration_cm': 12.717188556419078, 'axial_mass_penetration_cm_early': 1.408606792287737, 'axial_mass_penetration |

整体状态：**CONDITIONAL**；总耗时 112.4 s。

## 4. 与冻结声明的对应

本报告支撑的论文数值声明（来源 `results/Q4/reports/frozen_numbers.json`）：

| claim_id | 值 | 单位 | 源 |
|---|---|---|---|
| `q4_drying_time_hours` | 52.64 | h | `results/Q4/experiments/round1/metrics/main.json`$.drying_time_hours |
| `q4_R_at_drying_end_cm` | 1.2 | cm | `results/Q4/experiments/round1/metrics/main.json`$.radius.R_at_drying_end_cm |
| `q4_shrinkage_percent` | 40.1 | % | `results/Q4/experiments/round1/metrics/main.json`$.radius.shrinkage_percent |
| `q4_table6_t6_center` | 1.947 | kg/kg | `results/Q4/experiments/round1/metrics/main.json`$.table6_moisture_kg_per_kg['6'][0] |
| `q4_table6_t6_surface` | 0.5654 | kg/kg | `results/Q4/experiments/round1/metrics/main.json`$.table6_moisture_kg_per_kg['6'][4] |
| `q4_table6_end_center` | 0.15 | kg/kg | `results/Q4/experiments/round1/metrics/main.json`$.table6_end_row.C[0] |
| `q4_table6_end_surface` | 0.0526 | kg/kg | `results/Q4/experiments/round1/metrics/main.json`$.table6_end_row.C[4] |
| `q4_reference_max_abs_err` | 1.154e-06 | kg/kg | `results/Q4/experiments/round1/metrics/verifier_validation.json`$.reference_vs_analytical.max_abs_err |
| `q4_moving_boundary_dev` | 1.417e-13 | kg/kg | `results/Q4/experiments/round1/metrics/main_validation.json`$.moving_boundary_invariance.observed_max_abs_deviation_of_C_from_C0 |
| `q4_mass_balance_rel` | 2.557e-14 | 1 | `results/Q4/experiments/round1/metrics/main_validation.json`$.mass_balance.rel_residual |
| `q4_grid_refinement_diff` | 2.117e-06 | kg/kg | `results/Q4/experiments/round1/metrics/main_validation.json`$.grid_refinement_6h.max_abs_diff_C |
| `q4_time_refinement_hours` | 0 | h | `results/Q4/experiments/round1/metrics/main_validation.json`$.time_refinement_full_span.abs_diff_hours |
| `q4_radius_interp_hours` | 0.002778 | h | `results/Q4/experiments/round1/metrics/main_validation.json`$.radius_interpolation.abs_diff_hours |
| `q4_baseline_table6_diff` | 0.0004 | kg/kg | `results/Q4/experiments/round1/metrics/verifier_validation.json`$.main_vs_baseline_table6.max_abs_diff |
| `q4_baseline_drying_time_seconds` | 15 | s | `results/Q4/experiments/round1/metrics/verifier_validation.json`$.drying_time.abs_diff_seconds |
| `q4_sens_h_m_plus5pct_hours` | -0.1278 | h | `robustness/Q4/q4_robustness_summary.json`$.checks.h_m_perturbation.plus5pct.observed.t_dry_shift_hours |
| `q4_sens_D_plus5pct_hours` | -2.172 | h | `robustness/Q4/q4_robustness_summary.json`$.checks.D_perturbation.observed.t_dry_shift_hours |
| `q4_sens_T_inf_plus2C_hours` | -3.131 | h | `robustness/Q4/q4_robustness_summary.json`$.checks.env_extrapolation_t_inf_52.observed.t_dry_shift_hours |
| `q4_sens_mass_equation_form_hours` | -9.225 | h | `robustness/Q4/q4_robustness_summary.json`$.checks.mass_equation_form.observed.t_dry_shift_hours |
| `q4_vs_q3_drying_time_hours` | -4.829 | h | `results/Q4/experiments/round1/metrics/main.json`$.drying_time_hours (minus results/Q3/.../main.json $.drying_time_hours) |

## 5. 局限

- h_m, h and the appendix-4 closures are problem-supplied inputs; the reported drying time is conditional on them
- the constant-rate environment (50 degC / 0.05 kg/kg after 14400 s) is a human-decided framing assumption, not measured data
- contraction is assumed isotropic and to follow attachment 2 exactly; the dry-basis mass equation does not carry rho, so the geometric shrinkage is not a mass sink in the model
- the baseline reconstructs the surface column by a first-order half-cell relation; its own grid dependence is 4.1e-4, so the cross-check is at that level while the main is grid-converged to 2.1e-6
- the drying time inherits the flatness of the drying tail
- axial end-face transport is ignored

## 6. 回退触发状态

- fallback_id：`F4`
- 触发条件：M4 and B4 disagree on the drying time or the reported points beyond tolerance and the disagreement cannot be attributed
- 本轮是否观测到：**False**
- 证据：`results/Q4/experiments/round1/metrics/verifier_validation.json`

