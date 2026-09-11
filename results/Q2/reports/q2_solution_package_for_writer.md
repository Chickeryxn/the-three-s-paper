# Q2 交付包（writer package）

> 用途：Q2 论文段落的**唯一素材来源**。写作时不得从散落的实验输出中另取数字。
> 最终方法说明：`methods/Q2/q2_final_method_explanation.md`
> 最终结果分析：`results/Q2/reports/q2_final_result_analysis.md`
> 模型契约哈希：`f6ef7af5819f339c4676d271a52ab59ff379239d8ee7999de215d0239ee6acba`

## 1. 本问的交付

- 表3/表4：3 h 内每 0.5 h（6 行）× 5 个位置（0/0.5/1/1.5/2.0 cm）
- 交付物：`results/Q2/experiments/round1/result2.xlsx`（温度 + 水分浓度两表，每 1 s × 0.1 cm，覆盖整个烘干过程，206 873 行）

## 2. 可写入论文的数值声明（冻结数字候选）

每条给出唯一来源路径；冻结后论文中每个数字必须来自 `frozen_numbers.json` 的宏。

| 编号 | 声明 | 值 | 来源 |
|---|---|---|---|
| Q2.1 | **烘干时长** | 57.4647 h | `metrics/main.json#drying_time_hours` |
| Q2.2 | 表3/表4 全部 60 个数 | — | `metrics/main.json#table3_*, #table4_*` |
| Q2.3 | 3 h 时中心/表面温度 | 49.8495 / 49.9664 °C | `...#table3_temperature_C["3.0"]` |
| Q2.4 | 3 h 时中心/表面含水率 | 1.7662 / 1.0081 kg/kg | `...#table4_moisture_kg_per_kg["3.0"]` |
| Q2.5 | 3 h 网格加密残差 | 3.2×10⁻⁷ | `main_validation.json#grid_refinement_6h` |
| Q2.6 | 全时程时间加密差 | 2.8×10⁻⁴ h | `main_validation.json#time_refinement_full_span` |
| Q2.7 | 离散质量守恒 | 4.4×10⁻¹³ | `main_validation.json#mass_balance` |
| Q2.8 | 与解析解约化对照 | 5.98×10⁻⁷ | `metrics/verifier_validation.json#reference_vs_analytical` |
| Q2.9 | 两实现逐点差 / 时长差 | 0.0 / 26 s | `verifier_validation.json#main_vs_baseline_tables, #drying_time` |
| Q2.10 | **参数敏感性（论文必写）** | 质量方程读法 −14.72%、T_inf+2 °C −6.08%、D+5% −4.20%、h_m±5% ∓0.6% | `robustness/Q2/q2_robustness_summary.json` |
| Q2.11 | 3 h 表对恒温段假设的不敏感性 | 2.64×10⁻⁵ | 同上 #env_extrapolation_* |

## 3. 表格与图清单

| 类型 | 文件 | 说明 |
|---|---|---|
| 表 | 见 §1 | 题目指定格式 |
| 图 | `results/Q2/experiments/round1/figures/` | Type 1 诊断图（内部用；若进论文须过渲染校验） |
| 交付物 | 见 §1 | 题目指定的 xlsx |

## 4. 人类决策引用

`methods/Q2/q2_decisions.jsonl` 与 `planning/framing_decisions.jsonl`。论文中凡涉及方法选择、结果判定、稳定性判定与声明范围的表述，均须与此账本一致，不得由 AI 改述或加强。

## 5. 适用边界（必须写进论文）

1. 结论以题目给定的 h_m、h 与对应附录经验式为条件；
2. 恒温段环境（14400 s 后 T_inf = 50 °C、C_inf = 0.05 kg/kg）为**人为设定的口径**，非实测；
3. 质量方程采用题目给定的 Fick 标准形式；
4. 一维径向轴对称忽略端面轴向输运；
5. 数值方案由网格/时间加密实验认证。

## 6. 未决事项

见 §7。

## 7. 签核状态

本包在**建模者签核（`package_signoff`）之前不得用于生成冻结数字**。签核后由 `solution-package-builder` 产出 `results/Q2/reports/frozen_numbers.json`。
