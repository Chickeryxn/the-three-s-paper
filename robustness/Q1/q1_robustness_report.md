# Q1 稳健性报告（submission 口径）

> 由 `robustness/Q1/q1_robustness_summary.json` 生成；该 summary 即 lean 口径的稳健性证据。
> 生成脚本：`code/robustness_report.py`。所有数值均从源文件读取，未手写。

## 1. 范围与口径

- 提供者角色：`robustness-checker`；消费方：G4 稳定性判定、论文的局限段。
- 检验目标：本题的承重假设与已确认口径，而非通用清单。
- 判读口径：**单项扰动下的可观测后果**，不是统计显著性检验。

## 2. 基准状态

## 3. 逐项检验

| 检验 | 判定 | 观测量 |
|---|---|---|
| `solver_equivalence` | PASS | 8.882e-15 |
| `scheme_independence` | PASS | 0 |
| `h_m_perturbation` | CONDITIONAL | {'h_m x0.95': {'max_abs_diff_C': 0.03643444617292557, 'at_r_cm': 2.0, 'surface_C': 1.5466716156021647, 'surface_shift': 0.03643444617292557, 'relative_change':  |
| `D_perturbation` | CONDITIONAL | {'max_abs_diff_C': 0.015986160282109196, 'at_r_cm': 2.0, 'relative_change': 0.01058519854080324} |
| `mass_equation_form` | FAIL | {'max_abs_diff_C': 0.3231343525501935, 'at_r_cm': 2.0, 'surface_C': 1.8333715219794327, 'surface_shift': 0.3231343525501935, 'relative_change': 0.21396265374154 |
| `environment_interpolation` | PASS | {'max_abs_diff_C': 3.710491478514655e-07, 'at_r_cm': 2.0} |
| `end_face_neglect` | CONDITIONAL | {'axial_heat_penetration_cm': 1.7433873995086342, 'axial_mass_penetration_cm': 0.2981237858593824, 'length_cm': 25.0, 'end_face_area_share': 0.0741, 'heat_penet |
| `numerical_discretisation` | PASS | {'main_grid': 3.2406530383610743e-06, 'main_tolerance': 3.890383570848144e-10, 'baseline_grid': 2.1355154204982796e-06} |
| `independent_implementation` | PASS | 9.723e-07 |
| `output_degeneracy` | PASS | {'C_monotone_decreasing': True, 'center_is_global_max': True, 'profile': [2.55, 2.5497, 2.5383, 2.3755, 1.5102], 'surface_to_center_drop_1800s': 1.0397552287111 |

整体状态：**CONDITIONAL**；总耗时 60.99 s。

## 4. 与冻结声明的对应

本报告支撑的论文数值声明（来源 `results/Q1/reports/frozen_numbers.json`）：

| claim_id | 值 | 单位 | 源 |
|---|---|---|---|
| `q1_T_center_1800s` | 33.58 | degC | `results/Q1/experiments/round1/metrics/main.json`$.table1_temperature_C['1800'][0] |
| `q1_T_surface_1800s` | 36.79 | degC | `results/Q1/experiments/round1/metrics/main.json`$.table1_temperature_C['1800'][4] |
| `q1_C_center_1800s` | 2.55 | kg/kg | `results/Q1/experiments/round1/metrics/main.json`$.table2_moisture_kg_per_kg['1800'][0] |
| `q1_C_surface_1800s` | 1.51 | kg/kg | `results/Q1/experiments/round1/metrics/main.json`$.table2_moisture_kg_per_kg['1800'][4] |
| `q1_analytical_max_abs_err` | 6.184e-07 | kg/kg | `results/Q1/experiments/round1/metrics/main_validation.json`$.analytical_cross_check.max_abs_err |
| `q1_grid_refinement_diff` | 3.241e-06 | kg/kg | `results/Q1/experiments/round1/metrics/main_validation.json`$.grid_refinement.max_abs_diff_400_vs_800 |
| `q1_time_accuracy_tolerance_diff` | 3.89e-10 | kg/kg | `results/Q1/experiments/round1/metrics/main_validation.json`$.time_accuracy.max_abs_diff_1e_8_vs_1e_9 |
| `q1_mass_balance_rel` | 5.407e-11 | 1 | `results/Q1/experiments/round1/metrics/main_validation.json`$.mass_balance.rel_balance_error |
| `q1_independent_implementations_diff` | 9.723e-07 | kg/kg | `results/Q1/experiments/round1/metrics/verifier_validation.json`$.convergence_limit_comparison.abs_diff |
| `q1_h_m_plus5pct_surface_shift` | -0.03524 | kg/kg | `robustness/Q1/q1_robustness_summary.json`$.checks.h_m_perturbation.observed['h_m x1.05'].surface_shift |

## 5. 局限

- h_m and D are problem-supplied inputs, not fitted quantities; the reported values are conditional on them
- the interior moisture is essentially unchanged over the 1800 s window, so Q1 cannot discriminate between competing long-time diffusivity models
- the axial end faces are ignored; the estimate above bounds the effect for Q1 but not for the multi-day questions

## 6. 回退触发状态

- fallback_id：`F1`
- 触发条件：M2 and B2 disagree beyond the reported tolerance and the disagreement cannot be attributed
- 本轮是否观测到：**False**
- 证据：`independent_implementation check above`

