# Q4 交付包（writer package）

> 用途：Q4 论文段落的**唯一素材来源**。写作时不得从散落的实验输出中另取数字。
> 最终方法说明：`methods/Q4/q4_final_method_explanation.md`
> 最终结果分析：`results/Q4/reports/q4_final_result_analysis.md`
> 模型契约哈希：`f6ef7af5819f339c4676d271a52ab59ff379239d8ee7999de215d0239ee6acba`

## 1. 本问的交付

- 表6：每隔 6 h、到药材中心距离 0 / 0.5 / 1.0 / 1.5 cm 与"药材表面"的水分浓度；末行为**烘干结束时间**。
  **r > R(t) 的列留空**（T1 口径）：R(t) 在约 12 h 内降到 1.5 cm 以下，故 1.5 cm 列从某时刻起为空。
- 交付物：`results/Q4/experiments/round1/result4.xlsx`（Sheet1，A 列时间每 60 s，末行为精确烘干结束时刻；21 个数据列 = 0.0…1.9 cm + 药材表面）。

## 2. 可写入论文的数值声明（冻结数字候选）

| 编号 | 声明 | 来源 |
|---|---|---|
| Q4.1 | 烘干时长 52.6361 h | `metrics/main.json#drying_time_hours` |
| Q4.2 | 烘干结束时半径 1.200 cm（收缩 40.1%） | `metrics/main.json#radius.R_at_drying_end_cm` / `#radius.shrinkage_percent` |
| Q4.3 | 表6 全部数值（9 行 × 5 列 + 结束行） | `metrics/main.json#table6_moisture_kg_per_kg`、`#table6_end_row` |
| Q4.4 | 与解析解（冻结半径 + 常数 D）对照误差 1.15×10⁻⁶ | `metrics/verifier_validation.json#reference_vs_analytical.max_abs_err` |
| Q4.5 | 移动边界一致性偏差 1.42×10⁻¹³ | `metrics/main_validation.json#moving_boundary_invariance.observed_max_abs_deviation_of_C_from_C0` |
| Q4.6 | 离散守恒恒等式残差 2.56×10⁻¹⁴ | `metrics/main_validation.json#mass_balance.rel_residual` |
| Q4.7 | 网格加密（400↔800 @6 h）2.12×10⁻⁶ | `metrics/main_validation.json#grid_refinement_6h.max_abs_diff_C` |
| Q4.8 | 时间加密（Δt 10↔5 s）0.0 h | `metrics/main_validation.json#time_refinement_full_span.abs_diff_hours` |
| Q4.9 | 半径插值（PCHIP vs 线性）0.0028 h | `metrics/main_validation.json#radius_interpolation.abs_diff_hours` |
| Q4.10 | 独立格心实现：表6 差 4.0×10⁻⁴、时长差 15 s | `metrics/verifier_validation.json#main_vs_baseline_table6`、`#drying_time` |
| Q4.11 | h_m ±5% → 时长 ∓0.128 / 0.144 h | `robustness/Q4/q4_robustness_summary.json#h_m_perturbation` |
| Q4.12 | D +5% → −2.172 h | `#D_perturbation` |
| Q4.13 | T\infty +2 °C → −3.131 h | `#env_extrapolation_t_inf_52` |
| Q4.14 | 质量方程改用湿基自洽式 → −9.225 h | `#mass_equation_form` |
| Q4.15 | 与 Q3（不收缩）57.4647 h 对比：本问缩短 4.83 h（−8.4%） | `metrics/main.json` + `results/Q3/experiments/round1/metrics/main.json#drying_time_hours` |

## 3. 表格与图清单

| 类型 | 文件 | 说明 |
|---|---|---|
| 表6 | 见 §1 | 题目指定格式；**留空列必须在论文中保留为空** |
| 图 | `results/Q4/experiments/round1/figures/fig1_q4_curves.png` | Type 1 诊断图（左：中心/表面含水率与判据线；右：附件2 收缩曲线） |

## 4. 人类决策引用

`methods/Q4/q4_decisions.jsonl` 与 `planning/framing_decisions.jsonl`。论文中凡涉及方法选择、结果判定、稳定性判定与声明范围的表述，均须与此账本一致，不得由 AI 改述或加强。

## 5. 适用边界（必须写进论文）

1. 结论以题目给定的 h_m、h 与附录4 经验式为条件；
2. 恒温段环境（14400 s 后 T\infty = 50 °C、C\infty = 0.05 kg/kg）为**人为设定的口径**，非实测；
3. 收缩各向同性且严格按附件2；质量方程取 Fick 标准形式，几何收缩在模型内不是质量汇；
4. 一维径向轴对称忽略端面轴向输运（52.6 h 内渗透达数厘米/端）；
5. 时间格式对 Δt 一阶（滞后系数），Δt = 5 s 时剩余误差约 10⁻⁵；
6. 表6 表面列的主—基一致性为 4×10⁻⁴，建议按 3 位小数引用或注明该确认水平。

## 6. 签核状态

本包在**建模者签核（`package_signoff`）之前不得用于生成冻结数字**。签核后由 `solution-package-builder` 产出 `results/Q4/reports/frozen_numbers.json`。
