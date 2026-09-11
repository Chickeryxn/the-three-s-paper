# Q4 最终结果分析（考虑尺寸变化的烘干过程）

> 子问题：Q4 ｜ 轮次：round1 ｜ 口径：lean（submission 专属关卡未评估）
> 模型契约哈希：`f6ef7af5819f339c4676d271a52ab59ff379239d8ee7999de215d0239ee6acba`（`planning/model_contract.json`）
> 本文只汇总已落盘证据；**所有数值均给出源文件路径**，人类判定与客观事实分节陈述。

---

## 1. 结论（先结论）

在题目给定的参数、附录4 经验式与已冻结的环境口径下：

- **烘干时长 = 52.6361 h（约 2.19 天）**，判据为全域最大干基含水率 ≤ 0.15 kg/kg。
- 该时刻药材半径已收缩到 **1.200 cm**（初始 2.000 cm，收缩 **40.1%**，其中前 24 h 完成 99.4%）。
- **与 Q3 的对比是本问最重要的物理解读**：Q3（附录3 物性、不收缩）得 57.4647 h，本问（附录4 物性、收缩）得 52.6361 h，**缩短 4.83 h（−8.4%）**。注意附录4 的 D 前因子（4.2×10⁻⁴）比附录3（2.4×10⁻³）小 5.7 倍，**若忽略收缩，仅换物性会把时长显著拉长**；收缩把扩散路径缩短到 R_min/R₀ = 0.599，这一几何效应压倒了扩散系数的下降。因此**收缩不可忽略**，Q4 的时长不能由 Q3 直接推算。

数值可信度：与 Bessel 解析解（冻结半径 + 常数 D 的极限）对照误差 **1.15×10⁻⁶**；移动边界一致性检验（关闭表面传质后干基含水率必须不变）偏差 **1.42×10⁻¹³**；离散守恒恒等式残差 **2.56×10⁻¹⁴**；与独立格心实现的烘干时长相差 **15 s**。

适用边界：结论以题目给定的 h_m = 8×10⁻⁷ m/s、附录4 经验式与"收缩严格按附件2"为条件；忽略端面轴向输运。

---

## 2. 主方法与可用基线的最终对比

| | 主方法 M4 | 可用基线 B4 |
|---|---|---|
| 方案 | ξ 坐标顶点（节点）有限体积 + Crank–Nicolson + 3 步 Rannacher 启动 | ξ 坐标格心有限体积 + Crank–Nicolson（无启动） |
| 表面值来源 | ξ=1 是原生节点，**直接未知量** | 由最外层单元中心经 Robin 半单元关系回算 |
| 网格 / 时间 | 801 节点，Δt = 5 s | 800 单元，Δt = 5 s |
| **烘干时长** | **52.6361 h** | **52.6319 h**（差 15 s） |
| 表6 逐点最大差 | — | **4.0×10⁻⁴**（出现在早期表面列） |
| 网格加密（400↔800 @6 h） | **2.12×10⁻⁶** | 4.10×10⁻⁴ |
| 解析对照（冻结半径 + 常数 D） | **1.15×10⁻⁶** | 见 `baseline_validation.json` |
| 移动边界一致性偏差 | **1.42×10⁻¹³** | 9.4×10⁻¹⁴ |
| 运行耗时（运行器记录） | 见 `run_summary.json` | 见 `run_summary.json` |

两法在 t ≥ 18 h 之后逐点一致到 1×10⁻⁴；差异集中在 t = 6、12 h 的表面列，量级 4×10⁻⁴，这正是基线用一阶半单元关系回算表面值的代价。**表6 的数值应在论文中按 3 位小数引用**，或注明确认水平。

---

## 3. 主方法的时间精度（必须声明的口径）

非线性系数取上一时间层（滞后系数）使格式**对 Δt 一阶**。取 6 h 的表面值：

| Δt / s | 20 | 10 | 5 | 2.5 | Richardson 极限 |
|---|---|---|---|---|---|
| 表面 C | 0.5654344 | 0.5654216 | 0.5654349 | 0.5654412 | **0.5654476** |

取 Δt = 5 s 后剩余一阶误差约 1×10⁻⁵，低于报告精度；全时程 Δt 10↔5 s 的烘干时长差为 **0.0 h**。

---

## 4. 误差与不确定度分解

| 来源 | 量级 | 证据 |
|---|---|---|
| 与解析解的差别 | 1.2×10⁻⁶ | `main_validation.json#`（verifier `reference_vs_analytical`） |
| 空间离散 | 2.1×10⁻⁶（400↔800 @6 h） | `main_validation.json#grid_refinement_6h` |
| 时间离散 | 1×10⁻⁵（Δt = 5 s 的剩余一阶误差） | `main_validation.json#time_order_evidence` |
| 半径插值口径 | 0.0028 h | `main_validation.json#radius_interpolation` |
| 离散守恒 | 2.6×10⁻¹⁴ | `main_validation.json#mass_balance` |
| 独立实现 | 4.0×10⁻⁴（表6）/ 15 s（时长） | `verifier_validation.json` |
| **参数 h_m（±5%）** | **∓0.13 / 0.14 h（∓0.24% / 0.27%）** | `q4_robustness_summary.json#h_m_perturbation` |
| 参数 D（+5%） | **−2.17 h（−4.1%）** | `#D_perturbation` |
| 环境 T\infty（+2 °C） | **−3.13 h（−5.9%）** | `#env_extrapolation_t_inf_52` |
| 环境 C\infty（±0.005） | ∓0.10 / 0.13 h（∓0.2%） | `#env_extrapolation_c_inf_*` |
| 参数 h（+5%） | −0.003 h | `#h_conv_perturbation` |
| 质量方程读法（湿基自洽式） | **−9.23 h（−17.5%）** | `#mass_equation_form` |

**读法**：与 Q1–Q3 不同，本问的**主导不确定性不是 h_m**（只有 ±0.25%），而是**烘干判据尾部的平坦性**与**模型口径本身**——质量方程读法一项就能改变 17.5%，环境温度高 2 °C 改变 5.9%。h_m 影响小的原因是干燥由内部扩散控制（传质 Biot 数约 20 量级），表面传质阻力不是瓶颈。

---

## 5. 稳健性证据

完整清单见 `robustness/Q4/q4_robustness_summary.json`（13 项，整体 CONDITIONAL）：

| 检验 | 判定 |
|---|---|
| `moving_boundary_consistency`（关闭传质后 C≡C₀） | **PASS（1.4×10⁻¹³）** |
| `mass_balance`（移动域离散恒等式） | **PASS（2.6×10⁻¹⁴）** |
| `numerical_discretisation`（网格/步长/半径插值） | PASS |
| `independent_implementation` | PASS（4.0×10⁻⁴ / 15 s） |
| `output_degeneracy` | PASS |
| `env_extrapolation_c_inf_0.045 / 0.055` | PASS |
| `h_m_perturbation`（±5%） | PASS（<1 h） |
| `h_conv_perturbation`（+5%） | PASS |
| `D_perturbation`（+5%） | **CONDITIONAL（−2.17 h）** |
| `env_extrapolation_t_inf_52` | **CONDITIONAL（−3.13 h）** |
| `mass_equation_form` | **CONDITIONAL（−9.23 h）** |
| `end_face_neglect` | CONDITIONAL（52.6 h 内轴向渗透达数厘米/端） |

**回退触发状态**：F4（显式 FTCS）**未触发**——两实现一致，未超出报告容差。证据：`verifier_validation.json`。

---

## 6. 局限与适用范围

1. **条件性**：全部数值以题目给定的 h_m、h 与附录4 经验式为条件。
2. **质量方程读法**：采用题目明文的 Fick 标准形式（决策 `g_assumption_mass_equation_form`）。ρ 不入质量方程，因此几何收缩在模型内不是质量汇；替代读法使时长缩短 17.5%，已量化为已声明的条件性局限。
3. **收缩的建模**：各向同性、严格按附件2（决策口径），Ṙ 由 PCHIP 解析求导；改用线性插值只改变 0.0028 h。
4. **端面忽略**：一维径向轴对称。52.6 h 内轴向水分渗透达数厘米/端，远大于 Q1 窗口内的 2%，必须在论文中写明。
5. **判据尾部平坦**：判据取全域最大值，烘干时间对数值噪声敏感（两实现表6 相差 4×10⁻⁴，时长相差 15 s）。
6. **不构成全局最优性声明**：本问为前向场模拟，不涉及最优化。

---

## 7. 人类判定（与客观事实分离）

| decision_id | 类型 | 结论 |
|---|---|---|
| `q4_method_choice` | method_choice | A：M4 为主方法、B4 为验证、F4 为条件备选 |

来源：`methods/Q4/q4_decisions.jsonl`。结果/稳定性/声明范围三项判定**尚待建模者在 G4 作出**。

---

## 8. 数值来源索引

| 数值 | 源文件 |
|---|---|
| 烘干时长、表6、参考解、交付物规格 | `metrics/main.json` |
| 网格/时间/半径插值/移动边界/守恒/不变量 | `metrics/main_validation.json` |
| 基线同类指标 | `metrics/baseline_validation.json` |
| 解析对照、表6 交叉验证、时长差 | `metrics/verifier_validation.json` |
| 参数与口径敏感性 | `robustness/Q4/q4_robustness_summary.json` |
| 角色、快照、耗时、预算 | `results/Q4/experiments/round1/run_summary.json` 与 `runs/*/run_metadata.json` |
| 交付物 | `results/Q4/experiments/round1/result4.xlsx`（3159 行 × 21 数据列） |

**运行预算核实**：三个角色均 `status=SUCCESS`、`return_code=0`、`executed_by_runner=true`、`budget_delta={}` —— **无预算降级**。

---

## 9. 与参考标杆的对照（自检）

- **符号/单位唯一**：浓度 kg/kg（干基）、长度 cm（报告）/m（内部）、时间 s（交付物）/h（表6），无混用；
- **模型—代码—结果一致**：方法说明所述 ξ 顶点有限体积 + 表观对流 + Rannacher 启动与 `q4_main.py` 实现一致，评审五项检查全 PASS；
- **约束逐条判**：模型契约硬约束逐条落到代码与验收；T1 留空口径由 verifier 逐格核验（`blank_rule_exact = true`）；
- **收敛与最优性诚实**：给出解析对照、移动边界一致性、网格/时间/半径插值三重加密、独立实现交叉验证；明确声明本问无最优化；
- **诚实标注局限**：质量方程读法、收缩建模、端面忽略、判据平坦四条已显式写明，并指出主方法与基线在表面列的一致性水平（4×10⁻⁴）。
