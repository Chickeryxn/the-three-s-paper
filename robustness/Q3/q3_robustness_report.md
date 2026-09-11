# Q3 稳健性报告（submission 口径）

> 由 `robustness/Q3/q3_robustness_summary.json` 生成；该 summary 即 lean 口径的稳健性证据。
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
| mass_rel_error | 4.764e-13 |

## 3. 逐项检验

| 检验 | 判定 | 观测量 |
|---|---|---|
| `h_m_perturbation/plus5pct` | PASS | {'t_dry_hours': 57.15833333333333, 't_dry_shift_hours': -0.3063888888888897, 't_dry_shift_percent': -0.5331773600228173, 'max_abs_diff_table_C': 0.0308307524618 |
| `h_m_perturbation/minus5pct` | PASS | {'t_dry_hours': 57.809444444444445, 't_dry_shift_hours': 0.3447222222222237, 't_dry_shift_percent': 0.5998849535705507, 'max_abs_diff_table_C': 0.03360338515291 |
| `h_conv_perturbation/plus5pct` | PASS | {'t_dry_hours': 57.46055555555556, 't_dry_shift_hours': -0.004166666666662877, 't_dry_shift_percent': -0.007250825385616469, 'max_abs_diff_table_C': 0.000645622 |
| `D_perturbation` | CONDITIONAL | {'t_dry_hours': 55.04944444444445, 't_dry_shift_hours': -2.4152777777777743, 't_dry_shift_percent': -4.203061781866163, 'max_abs_diff_table_C': 0.02241786188687 |
| `mass_equation_form` | CONDITIONAL | {'t_dry_hours': 49.00333333333333, 't_dry_shift_hours': -8.46138888888889, 't_dry_shift_percent': -14.72449280476428, 'max_abs_diff_table_C': 0.2474411800773206 |
| `env_extrapolation_c_inf_0.045` | PASS | {'t_dry_hours': 57.367777777777775, 't_dry_shift_hours': -0.09694444444444628, 't_dry_shift_percent': -0.1687025373054998, 'max_abs_diff_table_C': 0.00585972613 |
| `env_extrapolation_c_inf_0.055` | PASS | {'t_dry_hours': 57.577777777777776, 't_dry_shift_hours': 0.11305555555555458, 't_dry_shift_percent': 0.19673906212990408, 'max_abs_diff_table_C': 0.005783405487 |
| `env_extrapolation_t_inf_52` | CONDITIONAL | {'t_dry_hours': 53.97222222222222, 't_dry_shift_hours': -3.4924999999999997, 't_dry_shift_percent': -6.077641838229252, 'max_abs_diff_table_C': 0.01671233482294 |
| `numerical_discretisation` | PASS | {'dt_full_span_shift_hours': 0.0036111111111125638, 'grid_6h_max_abs_diff_C': 3.201625258242302e-07} |
| `independent_implementation` | PASS | {'max_abs_diff_table_C': 0.00010000000000001674, 'max_abs_diff_end_row_C': 0.0, 'drying_time_spread_seconds': 25.99999999998488, 'startup_effect_at_dt1s': 1.41e |
| `mass_balance` | PASS | 4.764e-13 |
| `output_degeneracy` | PASS | {'C_monotone_decreasing': True, 'center_is_global_max': True, 'final_max_C': 0.14999982813971457, 'target': 0.15, 'n_unique_4dp_in_final_profile': 451, 'drying_ |
| `end_face_neglect` | CONDITIONAL | {'span_hours': 57.46472222222222, 'axial_heat_penetration_cm': 18.690010976961712, 'axial_mass_penetration_cm_early': 3.416301133988247, 'axial_mass_penetration |

整体状态：**CONDITIONAL**；总耗时 386.9 s。

## 4. 与冻结声明的对应

本报告支撑的论文数值声明（来源 `results/Q3/reports/frozen_numbers.json`）：

| claim_id | 值 | 单位 | 源 |
|---|---|---|---|
| `q3_drying_time` | 57.46 | h | `results/Q3/experiments/round1/metrics/main.json`$.drying_time_hours |
| `q3_C_center_at_end` | 0.15 | kg/kg | `results/Q3/experiments/round1/metrics/main.json`$.table5_end_row.C[0] |
| `q3_C_surface_at_end` | 0.0527 | kg/kg | `results/Q3/experiments/round1/metrics/main.json`$.table5_end_row.C[4] |
| `q3_C_center_54h` | 0.1539 | kg/kg | `results/Q3/experiments/round1/metrics/main.json`$.table5_moisture_kg_per_kg['54'][0] |
| `q3_consistency_with_Q2` | 57.46 | h | `results/Q2/experiments/round1/metrics/main.json`$.drying_time_hours |
| `q3_grid_refinement_diff` | 3.202e-07 | kg/kg | `results/Q3/experiments/round1/metrics/main_validation.json`$.grid_refinement_6h.max_abs_diff_C |
| `q3_time_refinement_diff` | 0.003611 | h | `results/Q3/experiments/round1/metrics/main_validation.json`$.time_refinement_full_span.abs_diff_hours |
| `q3_mass_balance_rel` | 4.764e-13 | 1 | `results/Q3/experiments/round1/metrics/main_validation.json`$.mass_balance.rel_error |

## 5. 局限

- h_m, h and the appendix-3 closures are problem-supplied inputs; the reported drying time is conditional on them
- the constant-rate environment (50 degC / 0.05 kg/kg after 14400 s) is a human-decided framing assumption, not measured data
- the drying time inherits the flatness of the drying tail: the two implementations agree pointwise to 1.5e-4 yet differ by about 26 s in the crossing time
- axial end-face transport is ignored; over the full span its penetration is far larger than in the 30 min Q1 window

## 6. 回退触发状态

- fallback_id：`F3`
- 触发条件：M3 and B3 disagree beyond the reported tolerance and the disagreement cannot be attributed
- 本轮是否观测到：**False**
- 证据：`results/Q3/experiments/round1/metrics/verifier_validation.json`

