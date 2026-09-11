# Q2 稳健性报告（submission 口径）

> 由 `robustness/Q2/q2_robustness_summary.json` 生成；该 summary 即 lean 口径的稳健性证据。
> 生成脚本：`code/robustness_report.py`。所有数值均从源文件读取，未手写。

## 1. 范围与口径

- 提供者角色：`robustness-checker`；消费方：G4 稳定性判定、论文的局限段。
- 检验目标：本题的承重假设与已确认口径，而非通用清单。
- 判读口径：**单项扰动下的可观测后果**，不是统计显著性检验。

## 2. 基准状态

| 项 | 值 |
|---|---|
| t_dry_hours | 57.46 |
| dt_s | 1 |
| steps | 206873 |

## 3. 逐项检验

| 检验 | 判定 | 观测量 |
|---|---|---|
| `h_m_perturbation/plus5pct` | PASS | {'t_dry_hours': 57.15833333333333, 't_dry_shift_hours': -0.3063888888888897, 't_dry_shift_percent': -0.5331773600228173, 'max_abs_diff_table_C': 0.0364923799798 |
| `h_m_perturbation/minus5pct` | PASS | {'t_dry_hours': 57.809444444444445, 't_dry_shift_hours': 0.3447222222222237, 't_dry_shift_percent': 0.5998849535705507, 'max_abs_diff_table_C': 0.03866948792661 |
| `h_conv_perturbation/plus5pct` | PASS | {'t_dry_hours': 57.46055555555556, 't_dry_shift_hours': -0.004166666666662877, 't_dry_shift_percent': -0.007250825385616469, 'max_abs_diff_table_C': 0.002973288 |
| `D_perturbation` | CONDITIONAL | {'t_dry_hours': 55.04944444444445, 't_dry_shift_hours': -2.4152777777777743, 't_dry_shift_percent': -4.203061781866163, 'max_abs_diff_table_C': 0.02647791708216 |
| `mass_equation_form` | CONDITIONAL | {'t_dry_hours': 49.00333333333333, 't_dry_shift_hours': -8.46138888888889, 't_dry_shift_percent': -14.72449280476428, 'max_abs_diff_table_C': 0.4250331820239448 |
| `env_extrapolation_c_inf_0.045` | PASS | {'t_dry_hours': 57.367777777777775, 't_dry_shift_hours': -0.09694444444444628, 't_dry_shift_percent': -0.1687025373054998, 'max_abs_diff_table_C': 2.63948028988 |
| `env_extrapolation_c_inf_0.055` | PASS | {'t_dry_hours': 57.577777777777776, 't_dry_shift_hours': 0.11305555555555458, 't_dry_shift_percent': 0.19673906212990408, 'max_abs_diff_table_C': 2.639480289889 |
| `env_extrapolation_t_inf_52` | CONDITIONAL | {'t_dry_hours': 53.97222222222222, 't_dry_shift_hours': -3.4924999999999997, 't_dry_shift_percent': -6.077641838229252, 'max_abs_diff_table_C': 2.63948028988991 |
| `numerical_discretisation` | PASS | {'dt_full_span_shift_hours': 0.00027777777777515666, 'grid_6h_max_abs_diff_C': 3.201593784529777e-07} |
| `independent_implementation` | PASS | {'max_abs_diff_C': 0.0, 'max_abs_diff_T_C': 0.0, 'drying_time_spread_seconds': 25.99999999998488} |
| `mass_balance` | PASS | 4.369e-13 |
| `output_degeneracy` | PASS | {'C_monotone_decreasing': True, 'center_is_global_max': True, 'drying_time_inside_stated_band': True, 'final_profile_C': [0.15, 0.1499, 0.1496, 0.1492, 0.1485,  |
| `end_face_neglect` | CONDITIONAL | {'span_hours': 57.46472222222222, 'axial_heat_penetration_cm': 18.690010976961712, 'axial_mass_penetration_cm_early': 3.416301133988247, 'axial_mass_penetration |

整体状态：**CONDITIONAL**；总耗时 289 s。

## 4. 与冻结声明的对应

本报告支撑的论文数值声明（来源 `results/Q2/reports/frozen_numbers.json`）：

| claim_id | 值 | 单位 | 源 |
|---|---|---|---|
| `q2_drying_time` | 57.46 | h | `results/Q2/experiments/round1/metrics/main.json`$.drying_time_hours |
| `q2_T_center_3h` | 49.85 | degC | `results/Q2/experiments/round1/metrics/main.json`$.table3_temperature_C['3.0'][0] |
| `q2_T_surface_3h` | 49.97 | degC | `results/Q2/experiments/round1/metrics/main.json`$.table3_temperature_C['3.0'][4] |
| `q2_C_center_3h` | 1.766 | kg/kg | `results/Q2/experiments/round1/metrics/main.json`$.table4_moisture_kg_per_kg['3.0'][0] |
| `q2_C_surface_3h` | 1.008 | kg/kg | `results/Q2/experiments/round1/metrics/main.json`$.table4_moisture_kg_per_kg['3.0'][4] |
| `q2_analytical_max_abs_err` | 5.976e-07 | kg/kg | `results/Q2/experiments/round1/metrics/verifier_validation.json`$.reference_vs_analytical.max_abs_err |
| `q2_grid_refinement_diff` | 3.202e-07 | kg/kg | `results/Q2/experiments/round1/metrics/main_validation.json`$.grid_refinement_6h.max_abs_diff_C |
| `q2_time_refinement_diff` | 0.0002778 | h | `results/Q2/experiments/round1/metrics/main_validation.json`$.time_refinement_full_span.abs_diff_hours |
| `q2_mass_balance_rel` | 4.369e-13 | 1 | `results/Q2/experiments/round1/metrics/main_validation.json`$.mass_balance.rel_error |
| `q2_drying_time_spread` | 26 | s | `results/Q2/experiments/round1/metrics/verifier_validation.json`$.drying_time.abs_diff_seconds |
| `q2_sens_mass_equation_form` | -14.72 | % | `robustness/Q2/q2_robustness_summary.json`$.checks.mass_equation_form.observed.t_dry_shift_percent |
| `q2_sens_T_inf_plus2C` | -6.078 | % | `robustness/Q2/q2_robustness_summary.json`$.checks.env_extrapolation_t_inf_52.observed.t_dry_shift_percent |
| `q2_sens_D_plus5pct` | -4.203 | % | `robustness/Q2/q2_robustness_summary.json`$.checks.D_perturbation.observed.t_dry_shift_percent |
| `q2_sens_h_m_plus5pct` | -0.5332 | % | `robustness/Q2/q2_robustness_summary.json`$.checks.h_m_perturbation.plus5pct.observed.t_dry_shift_percent |
| `q2_table_region_env_insensitivity` | 2.639e-05 | kg/kg | `robustness/Q2/q2_robustness_summary.json`$.checks.env_extrapolation_c_inf_0.045.observed.max_abs_diff_table_C |

## 5. 局限

- h_m, h and the appendix-3 closures are problem-supplied inputs; the reported drying time is conditional on them
- the constant-rate environment (50 degC / 0.05 kg/kg after 14400 s) is a human-decided framing assumption, not measured data
- the drying time inherits the flatness of the drying tail: two independent implementations agreeing pointwise to 1e-4 still differ by ~26 s in the crossing time
- axial end-face transport is ignored; over the full span its penetration is far larger than in the Q1 window

## 6. 回退触发状态

- fallback_id：`F2`
- 触发条件：M2 and B2 disagree beyond the reported tolerance and the disagreement cannot be attributed
- 本轮是否观测到：**False**
- 证据：`results/Q2/experiments/round1/metrics/verifier_validation.json`

