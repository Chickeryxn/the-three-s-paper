# Q2 最终结果分析（整个烘干过程的温湿耦合场）

> 子问题：Q2 ｜ 轮次：round1 ｜ 口径：lean（submission 专属关卡未评估）
> 模型契约哈希：`f6ef7af5819f339c4676d271a52ab59ff379239d8ee7999de215d0239ee6acba`（`planning/model_contract.json`）
> 本文只汇总已落盘证据；**所有数值均给出源文件路径**；人类判定与客观事实分节陈述。

---

## 1. 结论（先结论）

覆盖预热平衡与恒温干燥两阶段的温湿耦合场已解出：

- **烘干时长 57.46 h（2.39 天）**：全域最大干基含水率降到 0.15 kg/kg 所需的时间。该值落在题目所述的"2–3 天"区间内，构成对模型与已定环境口径的一次独立合理性检验。
- **两阶段结构清晰**：约 2–3 h 内温度逼近烘房温度（3 h 时中心 49.8495 °C、表面 49.9664 °C），其后进入恒温干燥；含水率从表层向内逐步下降，3 h 时表面已降到 1.0081 kg/kg、中心仍有 1.7662 kg/kg。
- **中心是最后干燥的位置**：全过程全域最大含水率恒等于中心值，与干燥物理一致。

数值可信度：顶点有限体积与格心有限体积两套独立实现**在 30 个报告点上四位小数完全一致**（差 0.0）；与解析解约化对照误差 **5.98×10⁻⁷**；离散质量守恒 **4.37×10⁻¹³**。

适用边界：**结论以题目给定的 h_m、h 与附录3 经验式为条件**；且恒温段环境（14400 s 后 T_inf=50 °C、C_inf=0.05 kg/kg）是**人为设定的口径**而非实测数据（详见 §6）。

---

## 2. 主方法与可用基线的最终对比

| | 主方法 M2 | 可用基线 B2 |
|---|---|---|
| 空间离散 | **顶点有限体积**（对偶控制体、守恒通量形式） | **格心有限体积**（单元即控制体、守恒通量形式） |
| 未知量位置 | 节点 j·Δr（r=0 与 r=R 均为原生节点） | 单元中心 (i−½)Δr |
| 边界处理 | 边界即节点；对偶控制体内侧面面积为 0，轴对称**自动满足** | 边界在面上；表面值由半单元串联热阻**回算** |
| 时间积分 | Crank–Nicolson（θ=0.5） | Crank–Nicolson（θ=0.5） |
| 网格 | 801 节点，Δr = 0.025 mm | 800 单元，Δr = 0.025 mm |
| 报告点对齐 | **21 个报告位置全是精确节点，零插值** | 报告位置错开半格，需三次样条插值 |
| 烘干时长 | **57.4647 h** | **57.4575 h** |
| 求解耗时（运行器记录） | 57.5 s | 59.6 s |

**逐点对比**（表3/表4 共 30 个报告点，t=0.5…3.0 h × r=0/0.5/1/1.5/2.0 cm）：

- 温度：**最大差 0.0**
- 含水率：**最大差 0.0**

**烘干时长的 26 秒差**：两法在每个报告点上完全一致，但阈值穿越时刻相差 26 s（0.013%）。原因是**干燥尾段极平**——临近判据时 dC/dt 趋近于零，场内 10⁻⁷ 量级的差异即可把穿越时刻推移几十秒。这是该判据的固有属性，不是实现差异。

> 来源：`results/Q2/experiments/round1/metrics/main.json`、`baseline.json`、`verifier_validation.json`

---

## 3. 误差与不确定度分解

| 来源 | 量级 | 证据 |
|---|---|---|
| 空间离散（6 h 窗口，400↔800） | **3.2×10⁻⁷** | `main_validation.json#grid_refinement_6h` |
| 时间离散（全时程，Δt 2→1 s） | 烘干时长差 **2.8×10⁻⁴ h** | `main_validation.json#time_refinement_full_span` |
| 与解析解约化对照（常物性 + 常环境 → Bessel） | **5.98×10⁻⁷** | `verifier_validation.json#reference_vs_analytical` |
| 离散质量守恒 | 主 **4.37×10⁻¹³** / 基线 **2.17×10⁻¹³** | `main_validation.json#mass_balance` |
| 实现差异（顶点 vs 格心） | 表格 **0.0**；时长 **26 s** | `verifier_validation.json#main_vs_baseline_tables` |
| **参数 D（+5%）** | 时长 **−2.415 h（−4.20%）** | `q2_robustness_summary.json#D_perturbation` |
| **假设 T_inf（+2 °C）** | 时长 **−3.493 h（−6.08%）** | `...#env_extrapolation_t_inf_52` |
| **假设 C_inf（±0.005）** | 时长 ±0.1 h（±0.2%） | `...#env_extrapolation_c_inf_0.045/0.055` |
| 参数 h_m（±5%） | 时长 ∓0.3 h（∓0.6%） | `...#h_m_perturbation` |
| 参数 h（+5%，经 D(C,T) 反馈） | 时长 **−0.0042 h（−0.007%）** | `...#h_conv_perturbation` |
| **质量方程读法替代** | 时长 **−8.461 h（−14.72%）** | `...#mass_equation_form` |

**读法**：数值误差在 10⁻⁷ 量级，远小于四位小数要求；**支配性不确定性来自假设与参数，不是数值**。按影响排序为：**质量方程读法（14.7%）> T_inf（6.1%）> D（4.2%）> h_m（0.6%）> C_inf（0.2%）> h（0.007%）**。

**与 Q1 的对比值得注意**：Q1 里 h_m 是唯一支配项（表面 ±2.3%），在 Q2 里它退到第四位。原因是 Q2 由**内部扩散控制**（干端传质 Biot 数约 20），表面不再是瓶颈，h_m 失去杠杆；而 D 与 T（因而 T_inf）直接决定扩散快慢。

**一个强结论**：T_inf 与 C_inf 的扰动对**表3/表4（3 h 内）的最大影响只有 2.64×10⁻⁵**。原因是恒温段自 14400 s（4 h）才开始，**3 h 内的表格完全由附件1 的实测环境决定，与恒温段假设无关**。因此预热平衡段的数值结果是无条件可信的。

---

## 4. 输出退化与集中度

| 指标 | 观测 | 判定 |
|---|---|---|
| 含水率沿半径单调性 | 单调递减 | 无内部极值 |
| 极值位置 | **中心 r=0 即全域最大**（全过程恒成立） | 无退化，且与判据口径一致 |
| 温度沿半径单调性 | 单调递增 | — |
| 判据是否被满足 | 是，且**单次穿越** | 烘干时长定义良好 |
| 烘干时长是否落在题目所述区间 | **是**（57.46 h ∈ [48, 72] h） | 通过 |
| 终态剖面 | 中心 0.1500、表面 0.0964 | 符合"各处达标" |

> 来源：`main_validation.json#invariants`、`q2_robustness_summary.json#output_degeneracy`

**解读**：本问的含水率场不存在集中或退化风险——场单调、极值位置明确、判据单次穿越。与 Q1 不同，本问的场在 3 h 内已充分演化（中心从 2.55 降到 1.77），**具备判别内部扩散模型的能力**，这一点 Q1 做不到。

---

## 5. 稳健性证据

完整清单见 `robustness/Q2/q2_robustness_summary.json`（11 项，整体 CONDITIONAL）：

| 检验 | 判定 |
|---|---|
| `numerical_discretisation`（网格 + 时间） | PASS |
| `independent_implementation`（顶点 vs 格心） | PASS（表格差 0.0） |
| `mass_balance` | PASS（4.37×10⁻¹³） |
| `output_degeneracy` | PASS |
| `h_m_perturbation` / `h_conv_perturbation` | PASS |
| `env_extrapolation_c_inf_*` | PASS |
| `D_perturbation` | CONDITIONAL（−4.20%） |
| `env_extrapolation_t_inf_52` | CONDITIONAL（−6.08%） |
| `mass_equation_form` | CONDITIONAL（−14.72%） |
| `end_face_neglect` | CONDITIONAL |

**端面忽略的量级（Q2 必须重新评估）**：全时程 57.46 h 内，轴向热渗透 **18.69 cm**（占 25 cm 长度的 **75%**）、轴向质量渗透 **3.42 cm/端**（**13.7%** 长度）。这远大于 Q1 窗口内的 <2%，是本问的实质性局限。

**回退触发状态**：F2（显式 FTCS）**未触发**——两实现逐点一致。

---

## 6. 局限与适用范围

1. **条件性（参数）**：全部数值以题目给定的 h_m = 8×10⁻⁷ m/s、h = 25 W/(m²·K) 与附录3 经验式为条件。实测 D 变化 5% 使时长变化 4.20%。
2. **条件性（环境外推）**：恒温段 T_inf = 50 °C、C_inf = 0.05 kg/kg 是人为设定的口径（附件1 只到 14400 s）。**T_inf 仅变化 2 °C 即使时长变化 6.08%**——这是本问最大的口径风险，必须显式声明。
3. **质量方程读法**：采用题目明文给定的 Fick 标准形式（决策 `g_assumption_mass_equation_form`）。替代读法使时长变化 14.72%，已量化并记为条件性局限。
4. **端面忽略**：一维径向轴对称（决策 `g_framing_spatial_dimension`）。全时程轴向质量渗透达长度的 13.7%，该假设在多日时程下是实质性的，须在论文中量化说明。
5. **时长判据的固有不确定性**：干燥尾段平坦，两套独立实现的 26 s 穿越时刻差是该判据的属性，不是实现误差。
6. **不构成全局最优性声明**：本问为前向场模拟，不存在最优化问题。

---

## 7. 人类判定（与客观事实分离）

| decision_id | 类型 | 结论 |
|---|---|---|
| `q2_method_choice` | method_choice | M2 为主方法、B2 为验证 |
| `q2_presentation_method_amendment` | method_choice | 正文以**顶点有限体积**为主方法，格心降为验证 |
| `q2_result_verdict` | result_verdict | **A**：沿用当前结论，表3/表4 与 result2.xlsx 为定稿数值 |
| `q2_stability_verdict` | stability_verdict | **A**：判定稳定；**附条件**：措辞条件化 + 写明上述四条条件性 |
| `q2_claim_scope` | claim_scope | **全部保留**（C1 时长 / C2 两阶段 / C3 四位小数 / C4 内部扩散控制 / C5 中心最后干燥 / C6 机理链条） |

来源：`methods/Q2/q2_decisions.jsonl`。以上为建模者判定，非 AI 结论。

> `stability_verdict` 的措辞条件化要求与 `claim_scope` 的"全部保留"**并行适用**：保留声明强度，同时在论文中写明条件性与敏感性数值。

---

## 8. 数值来源索引

| 数值 | 源文件 |
|---|---|
| 表3/表4、烘干时长、交付物规格、耗时 | `metrics/main.json` |
| 网格/时间加密、质量守恒、不变量 | `metrics/main_validation.json` |
| 基线表格、基线的质量守恒 | `metrics/baseline.json`、`metrics/baseline_validation.json` |
| 解析解对照、主基线逐点对比、时长差 | `metrics/verifier.json`、`metrics/verifier_validation.json` |
| 全部敏感性 | `robustness/Q2/q2_robustness_summary.json` |
| 角色、快照、预算、耗时 | `results/Q2/experiments/round1/run_summary.json` 与 `runs/*/run_metadata.json` |
| 交付物 | `results/Q2/experiments/round1/result2.xlsx` |

**运行预算核实**：三个角色均 status=SUCCESS、return_code=0、executed_by_runner=true、degraded=false、budget_delta={} —— **无预算降级**。

**交付物规格核实**：`result2.xlsx` 两张工作表（温度 / 水分浓度），每张 **206,873 数据行 × 21 数据列**，A 列时间自 1 s 起，首行距离 0–2.0 cm；温度以**摄氏度**输出（该单位错误已在快照前发现并修正）。

---

## 9. 与参考标杆的对照（自检）

对照 `resource-library/papers/2020A_paper_structure` 与 `tables/2020A_table_result_reflow` 提出的可迁移规则自查：

- **符号/单位唯一**：温度统一 °C、含水率统一 kg/kg（干基）、长度 cm、内部计算用 SI；**本轮曾出现温度以开尔文写入交付物的单位错误，已在快照前修正并复查**；
- **模型—代码—结果一致**：方法卡所述方案（顶点有限体积 + Crank–Nicolson）与 `q2_main.py` 一致，评审五项检查全 PASS；
- **约束逐条判**：模型契约 12 条硬约束逐条落到代码与验收；
- **收敛与最优性诚实**：给出网格、时间双加密、解析解约化对照、两套独立实现交叉验证；本问无最优化，明确声明不涉及最优性；
- **诚实标注局限**：参数条件性、环境外推口径、质量方程读法、端面忽略、时长判据固有不确定性共五条已显式写明。
