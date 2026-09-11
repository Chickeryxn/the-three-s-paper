# Q3 交付包（writer package）

> 用途：Q3 论文段落的**唯一素材来源**。写作时不得从散落的实验输出中另取数字。
> 最终方法说明：`methods/Q3/q3_final_method_explanation.md`
> 最终结果分析：`results/Q3/reports/q3_final_result_analysis.md`
> 模型契约哈希：`f6ef7af5819f339c4676d271a52ab59ff379239d8ee7999de215d0239ee6acba`

## 1. 本问的交付

- 表5：每 6 h × 每 0.5 cm 的水分浓度，末行为"烘干结束时间"
- 交付物：`results/Q3/experiments/round1/result3.xlsx`（单表，每 60 s × 0.1 cm，共 3 448 行，末行 t = 206 873 s）

## 2. 可写入论文的数值声明（冻结数字候选）

每条给出唯一来源路径；冻结后论文中每个数字必须来自 `frozen_numbers.json` 的宏。

| 编号 | 声明 | 值 | 来源 |
|---|---|---|---|
| Q3.1 | **烘干所需时间** | **57.4647 h** | `metrics/main.json#drying_time_hours` |
| Q3.2 | 表5 全部 45 个数 | — | `metrics/main.json#table5_moisture_kg_per_kg` |
| Q3.3 | 烘干结束行 | 中心 0.1500、表面 0.0527 | `metrics/main.json#table5_end_row` |
| Q3.4 | 与 Q2 主方法的一致性 | 57.4647 h（逐位相同） | `results/Q2/experiments/round1/metrics/main.json` |
| Q3.5 | 时间加密（全时程 10→1 s） | 0.0036 h | `main_validation.json#time_refinement_full_span` |
| Q3.6 | 网格加密（6 h） | 3.2×10⁻⁷ | `main_validation.json#grid_refinement_6h` |
| Q3.7 | 离散质量守恒 | 4.8×10⁻¹³ | `main_validation.json#mass_balance` |
| Q3.8 | 与解析解约化对照 | 6.05×10⁻⁷ | `metrics/verifier_validation.json#reference_vs_analytical` |
| Q3.9 | 两实现：表5 差 / 结束行差 / 时长差 | ≤1×10⁻⁴ / 0.0 / 26 s | `verifier_validation.json` |
| Q3.10 | Rannacher 启动的影响 | 1.41×10⁻⁷ | `methods/Q3/probes/risk_probe_summary.json` |

## 3. 表格与图清单

| 类型 | 文件 | 说明 |
|---|---|---|
| 表 | 见 §1 | 题目指定格式 |
| 图 | `results/Q3/experiments/round1/figures/` | Type 1 诊断图（内部用；若进论文须过渲染校验） |
| 交付物 | 见 §1 | 题目指定的 xlsx |

## 4. 人类决策引用

`methods/Q3/q3_decisions.jsonl` 与 `planning/framing_decisions.jsonl`。论文中凡涉及方法选择、结果判定、稳定性判定与声明范围的表述，均须与此账本一致，不得由 AI 改述或加强。

## 5. 适用边界（必须写进论文）

1. 结论以题目给定的 h_m、h 与对应附录经验式为条件；
2. 恒温段环境（14400 s 后 T_inf = 50 °C、C_inf = 0.05 kg/kg）为**人为设定的口径**，非实测；
3. 质量方程采用题目给定的 Fick 标准形式；
4. 一维径向轴对称忽略端面轴向输运；
5. 数值方案由网格/时间加密实验认证。

## 6. 未决事项

见 §7。

## 7. 签核状态

本包在**建模者签核（`package_signoff`）之前不得用于生成冻结数字**。签核后由 `solution-package-builder` 产出 `results/Q3/reports/frozen_numbers.json`。
