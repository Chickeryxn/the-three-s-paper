# Q1 最终结果分析（预热平衡阶段温湿场）

> 子问题：Q1 ｜ 轮次：round1 ｜ 口径：lean（submission 专属关卡未评估）
> 模型契约哈希：`f6ef7af5819f339c4676d271a52ab59ff379239d8ee7999de215d0239ee6acba`（`planning/model_contract.json`）
> 本文只汇总已落盘证据；**所有数值均给出源文件路径**，人类判定与客观事实分节陈述。

---

## 1. 结论（先结论）

在题目给定的参数与附录经验式下，预热平衡阶段（0–1800 s）的数值解为：

- **温度**由初值 28 °C 上升：1800 s 时中心 **33.5753 °C**、表面 **36.7856 °C**，表面先升温、中心滞后，中心—表面温差 3.21 °C。
- **干基含水率**基本未变：中心 **2.5500 kg/kg**（即初值 2.55），表面已失水至 **1.5102 kg/kg**。
- 该形态的物理解释：水分扩散特征时间约 22 h（R²/D），而本阶段只有 30 min，**因此本阶段以升温为主、失水仅限表层**。

数值可信度：解析解对照误差 **6.18×10⁻⁷**，离散质量守恒绝对残差 **1.74×10⁻¹⁴**（相对失水量 5.41×10⁻¹¹），两套独立实现的外推极限相差 **9.72×10⁻⁷**。
适用边界：**结论以题目给定的 h_m = 8×10⁻⁷ m/s 与附录经验式为条件**，且忽略端面轴向输运（详见 §6）。

---

## 2. 主方法与可用基线的最终对比

| | 主方法 M2 | 可用基线 B2 |
|---|---|---|
| 方案 | 顶点（节点）守恒通量式 + 自适应 BDF | 格心有限体积 + Crank–Nicolson + Thomas 追赶 |
| 网格 | 801 节点（dr = 0.025 mm），r = 0 与 r = R 均为原生节点 | 800 单元（dr = 0.025 mm），表面值由 Robin 关系回算 |
| 时间 | 自适应 BDF，rtol 1e-9、atol 1e-11（无固定步长） | 定步长 Δt = 0.25 s |
| 网格加密 | 400↔800 差 **3.241×10⁻⁶** | 400↔800 差 **2.136×10⁻⁶** |
| 解析解对照（Bessel） | **6.184×10⁻⁷** | **2.857×10⁻⁶** |
| 表面列 Richardson 极限 | **2.2470452** | **2.2470462** |
| 表面列 N=800 误差 | 1.86×10⁻⁵ | 1.68×10⁻⁵ |
| 运行耗时（运行器记录） | 368.9 s | 198.9 s |

> 角色分工在 G4 按决策 `q1_method_role_swap` 重排：顶点形式提为主方法、格心形式降为基线。两者数值核心**逐字复用** G3 阶段已验证的实现，重排不改变任何报告数值；守卫见 `methods/Q1/probes/role_swap_evidence/role_swap_check.json`（9 项全 PASS）。

**逐点对比**（35 个报告点，t=100…1800 s × r=0/0.5/1/1.5/2.0 cm）：

- 温度：**35 点全部相同**（最大差 0.0）
- 含水率：34 点相同；**仅 1 点差 1×10⁻⁴**，位于 t=100 s、r=2.0 cm

该单点差的判定：真值恰为 **2.2470455**，正落在四位小数的舍入分界 2.24705 上，两实现分别落在分界两侧。**这是量化效应而非真实偏差**——两法的 Richardson 极限只差 **9.72×10⁻⁷**。

> 来源：`results/Q1/experiments/round1/metrics/main.json`、`baseline.json`、`main_validation.json`、`baseline_validation.json`、`verifier_validation.json`

---

## 3. 误差与不确定度分解

| 来源 | 量级 | 证据 |
|---|---|---|
| 空间离散（主方法） | 3.2×10⁻⁶（400↔800 节点） | `main_validation.json#grid_refinement` |
| 时间精度（自适应 BDF 的容差加密） | 3.9×10⁻¹⁰（rtol 1e-8↔1e-9） | `main_validation.json#time_accuracy` |
| 与解析解的差别 | 6.2×10⁻⁷ | `main_validation.json#analytical_cross_check` |
| 离散质量守恒 | 1.7×10⁻¹⁴（机器精度；Voronoi 权重和与 πR² 之差为 0.0） | `main_validation.json#mass_balance` |
| 空间离散（基线，供对照） | 2.1×10⁻⁶（400↔800 单元） | `baseline_validation.json#grid_refinement` |
| 实现差异（独立算法） | 9.7×10⁻⁷ | `verifier_validation.json#convergence_limit_comparison` |
| 环境插值方式 | 线性 vs 三次样条可忽略 | `q1_robustness_summary.json#environment_interpolation` |
| **参数 h_m（±5%）** | **表面 ±0.035 kg/kg（±2.3%）** | `q1_robustness_summary.json#h_m_perturbation` |
| 参数 D（+5%） | 表面 +0.016 kg/kg（+1.1%） | `q1_robustness_summary.json#D_perturbation` |
| h、ρc_p（+5%） | **对含水率零影响** | 同上 |

**读法**：数值误差在 10⁻⁶ 量级，远小于题目的四位小数要求；**支配性不确定性来自题目给定的 h_m**，它使表面值在第四位上产生 350 个单位的变化。

**结构性事实**：附录2 的 D 只依赖 C、不依赖 T，故 Q1 中热与湿是**单向耦合**——温度场不反馈到含水率。因此 h 与 ρc_p 的扰动对含水率的影响严格为零，这不是数值巧合。

---

## 4. 输出退化与集中度

| 指标 | 观测 | 判定 |
|---|---|---|
| 含水率沿半径单调性 | 单调递减 | 无内部极值 |
| 极值位置 | **中心 r=0 即全域最大** | 无退化 |
| 温度沿半径单调性 | 单调递增 | — |
| 四位小数下网格值互异 | 801 个节点值中 501 个取值互异 | 无输出退化（重复来自中心区的物理平台 C≡2.55，不是数值退化） |
| 场的变化幅度（1800 s） | 中心 2.5500 → 表面 1.5102 | 全部敏感性集中在表面列 |

> 来源：`main_validation.json#invariants`、`q1_robustness_summary.json#output_degeneracy`

**解读**：1800 s 内水分的响应集中在极薄表层，"集中度"很高。这意味着**本阶段的场对内部扩散模型的判别力很弱**——不同扩散模型在本窗口内会给出几乎相同的内部值，差异只出现在表面。这是把本阶段结论外推到多日时程时必须声明的限制。

---

## 5. 稳健性证据

完整清单见 `robustness/Q1/q1_robustness_summary.json`（9 项，整体 CONDITIONAL）：

| 检验 | 判定 |
|---|---|
| `solver_equivalence`（向量化求解器 vs 已验证求解器） | PASS（8.9×10⁻¹⁵） |
| `scheme_independence`（敏感性扫描实现 vs 主方法 M2） | PASS（差 0.0） |
| `numerical_discretisation` | PASS |
| `independent_implementation` | PASS（9.7×10⁻⁷） |
| `environment_interpolation` | PASS |
| `output_degeneracy` | PASS |
| `h_m_perturbation` | CONDITIONAL |
| `D_perturbation` | CONDITIONAL |
| `end_face_neglect` | CONDITIONAL（Q1 窗口内轴向质量渗透 <2% 长度） |
| `mass_equation_form` | FAIL（替代读法会大幅改变表面值） |

**多日时程的附带敏感性**（探索性，见 `robustness/Q1/q1_robustness_advisory_multiday.json`）：
按附录3 物性与已定环境口径，多日烘干时长为 **57.38 h（2.39 天）**，落在题目所说的 2–3 天区间内；
h_m 放大 5% 使时长变为 57.07 h（**−0.54%**），时间步长减半后时长不变。
即**多日时长对 h_m 的敏感度远低于 Q1 的表面值**（−0.54% vs ±2.3%），原因是干燥由内部扩散控制（干端传质 Biot 数约 20）。

**回退触发状态**：F1（显式 FTCS）**未触发**——两实现一致，未超出报告容差。证据：`verifier_validation.json#convergence_limit_comparison`。

---

## 6. 局限与适用范围

1. **条件性**：全部数值以题目给定的 h_m = 8×10⁻⁷ m/s、h = 25 W/(m²·K) 与附录2 经验式为条件；h_m 变化 5% 会使表面值变化 2.3%。
2. **质量方程读法**：本模型采用题目明文给定的 Fick 标准形式（决策 `g_assumption_mass_equation_form`）。若改用与湿基密度严格自洽的写法则等效扩散系数相差 (1+C) 倍，会显著改变表面值——该差异已量化并在稳健性检验中记为 FAIL，属**已声明的条件性局限**，不是本模型的缺陷。
3. **端面忽略**：采用一维径向轴对称（决策 `g_framing_spatial_dimension`）。Q1 窗口内轴向质量渗透 <2% 长度，假设成立；但该量随时间增长，多日时程下必须重新评估。
4. **阶段局限**：1800 s 内内部含水率几乎不变，本窗口**不足以判别内部扩散模型**（见 §4）。
5. **不构成全局最优性声明**：本问为前向场模拟，不存在最优化问题，故不涉及最优性证明。

---

## 7. 人类判定（与客观事实分离）

| decision_id | 类型 | 结论 |
|---|---|---|
| `q1_method_choice` | method_choice | M1 为主方法、B1 为验证 |
| `q1_time_scheme_amendment` | method_choice | M1 时间积分由后向 Euler 改为 Crank–Nicolson |
| `q1_result_verdict` | result_verdict | A：沿用当前结论，表1/表2 与 result1.xlsx 为定稿数值 |
| `q1_stability_verdict` | stability_verdict | A：判定稳定；**附带要求：措辞条件化并写明上述局限** |
| `q1_claim_scope` | claim_scope | A：保留全部拟声明结论 |
| `q1_method_role_swap` | method_choice | ②A：顶点有限体积提为主方法 M2、格心有限体积 + CN 降为基线 B2（附两条保障） |

来源：`methods/Q1/q1_decisions.jsonl`。以上为建模者判定，非 AI 结论。

---

## 8. 数值来源索引

| 数值 | 源文件 |
|---|---|
| 表1/表2 全部数值、交付物规格 | `metrics/main.json` |
| 网格/时间/解析对照/质量守恒/不变量 | `metrics/main_validation.json` |
| 基线同类指标、表面收敛 | `metrics/baseline_validation.json` |
| 交叉验证、收敛极限差、解析守恒 | `metrics/verifier_validation.json` |
| 参数敏感性、稳健性清单 | `robustness/Q1/q1_robustness_summary.json` |
| 多日时长敏感性（探索性） | `robustness/Q1/q1_robustness_advisory_multiday.json` |
| 角色、快照、耗时、预算 | `results/Q1/experiments/round1/run_summary.json` 与 `runs/*/run_metadata.json` |
| 交付物 | `results/Q1/experiments/round1/result1.xlsx` |

**运行预算核实**：三个角色均 `status=SUCCESS`、`return_code=0`、`executed_by_runner=true`、`degraded=false`、`budget_delta={}` —— **无预算降级**，本报告不得按缩减预算解读。

---

## 9. 与参考标杆的对照（自检）

对照 `resource-library/papers/2020A_paper_structure` 与 `tables/2020A_table_result_reflow` 提出的可迁移规则自查：

- **符号/单位唯一**：温度统一 °C、含水率统一 kg/kg（干基）、长度 cm、内部计算用 SI，未出现 ℃/K 混用；
- **模型—代码—结果一致**：方法卡所述方案（顶点守恒通量式 + 自适应 BDF）与 `q1_main.py` 实现一致、基线方案（格心有限体积 + CN + Thomas）与 `q1_baseline.py` 实现一致，评审五项检查全 PASS；
- **约束逐条判**：模型契约 12 条硬约束逐条落到代码与验收；
- **收敛与最优性诚实**：给出网格/时间双加密、解析解对照、独立实现交叉验证；本问无最优化，明确声明不涉及最优性；
- **诚实标注局限**：h_m 条件性、质量方程读法、端面忽略三条已显式写明。
