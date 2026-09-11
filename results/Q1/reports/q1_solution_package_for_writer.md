# Q1 交付包（writer package）

> 用途：Q1 论文段落的**唯一素材来源**。写作时不得从散落的实验输出中另取数字。
> 最终方法说明：`methods/Q1/q1_final_method_explanation.md`
> 最终结果分析：`results/Q1/reports/q1_final_result_analysis.md`
> 模型契约哈希：`f6ef7af5819f339c4676d271a52ab59ff379239d8ee7999de215d0239ee6acba`

## 1. 本问的交付

- 表1/表2：7 个时刻（100/300/600/900/1200/1500/1800 s）× 5 个位置（0/0.5/1/1.5/2.0 cm）
- 交付物：`results/Q1/experiments/round1/result1.xlsx`（温度 + 水分浓度两表，t=1…1800 s 每 1 s × r=0…2.0 cm 每 0.1 cm）

## 2. 可写入论文的数值声明（冻结数字候选）

每条给出唯一来源路径；冻结后论文中每个数字必须来自 `frozen_numbers.json` 的宏。

| 编号 | 声明 | 值 | 来源 |
|---|---|---|---|
| Q1.1 | 1800 s 时中心温度 | 见 `metrics/main.json#table1_temperature_C["1800"][0]` | main.json |
| Q1.2 | 1800 s 时表面温度 | 见 `...#[4]` | main.json |
| Q1.3 | 1800 s 时中心含水率 | 见 `metrics/main.json#table2_moisture_kg_per_kg["1800"][0]` | main.json |
| Q1.4 | 1800 s 时表面含水率 | 见 `...#[4]` | main.json |
| Q1.5 | 表1/表2 全部 70 个数 | `metrics/main.json` | main.json |
| Q1.6 | 与解析解对照误差 | `metrics/main_validation.json#analytical_max_abs_err` | main_validation.json |
| Q1.7 | 网格加密残差（主方法 400↔800 节点） | `main_validation.json#grid_refinement.max_abs_diff_400_vs_800` | main_validation.json |
| Q1.8 | 时间精度（自适应 BDF 的容差加密 rtol 1e-8↔1e-9） | `main_validation.json#time_accuracy.max_abs_diff_1e_8_vs_1e_9` | main_validation.json |
| Q1.9 | 离散质量守恒 | `main_validation.json#mass_balance.rel_balance_error` | main_validation.json |
| Q1.10 | 两套独立实现的收敛极限差 | `metrics/verifier_validation.json#convergence_limit_comparison.abs_diff` | verifier_validation.json |
| Q1.11 | h_m 敏感性 | `robustness/Q1/q1_robustness_summary.json#h_m_perturbation` | robustness |

> 主方法为顶点（节点）守恒通量式 + 自适应 BDF（M2），可用基线为格心有限体积 + Crank–Nicolson（B2）；分工由 G4 决策 `q1_method_role_swap` 确定，守卫证据 `methods/Q1/probes/role_swap_evidence/role_swap_check.json`。

## 3. 表格与图清单

| 类型 | 文件 | 说明 |
|---|---|---|
| 表 | 见 §1 | 题目指定格式 |
| 图 | `results/Q1/experiments/round1/figures/` | Type 1 诊断图（内部用；若进论文须过渲染校验） |
| 交付物 | 见 §1 | 题目指定的 xlsx |

## 4. 人类决策引用

`methods/Q1/q1_decisions.jsonl` 与 `planning/framing_decisions.jsonl`。论文中凡涉及方法选择、结果判定、稳定性判定与声明范围的表述，均须与此账本一致，不得由 AI 改述或加强。

## 5. 适用边界（必须写进论文）

1. 结论以题目给定的 h_m、h 与对应附录经验式为条件；
2. 恒温段环境（14400 s 后 T_inf = 50 °C、C_inf = 0.05 kg/kg）为**人为设定的口径**，非实测；
3. 质量方程采用题目给定的 Fick 标准形式；
4. 一维径向轴对称忽略端面轴向输运；
5. 数值方案由网格/时间加密实验认证。

## 6. 未决事项

见 §7。

## 7. 签核状态

本包在**建模者签核（`package_signoff`）之前不得用于生成冻结数字**。签核后由 `solution-package-builder` 产出 `results/Q1/reports/frozen_numbers.json`。
