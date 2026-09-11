# Q3 最终结果分析（烘干所需时间的确定）

> 子问题：Q3 ｜ 轮次：round1 ｜ 口径：lean（submission 专属关卡见 §9）
> 模型契约哈希：`f6ef7af5819f339c4676d271a52ab59ff379239d8ee7999de215d0239ee6acba`（`planning/model_contract.json`）
> 本文只汇总已落盘证据；**所有数值均给出源文件路径**；人类判定与客观事实分节陈述。

---

## 1. 结论（先结论）

**药材烘干所需时间 = 57.4647 h（2.394 天）**，即全域最大干基含水率首次降到 0.15 kg/kg 的时刻。

- 该值落在题目所述的"2–3 天"区间内。
- 判据由**中心**控制：烘干结束时刻，中心恰为 0.1500，而表面已降到 0.0527；前一采样行（54 h）中心为 0.1539（尚未达标）——与建模者确认的"分层/两级、以中心为准"口径一致（决策 `g_caliber_criterion_granularity`）。
- **与 Q2 主方法独立算出的 57.4647 h 逐位相同**：两问共用同一模型、不同的输出口径，互为印证。

数值可信度：与 Bessel 解析解约化对照 **6.05×10⁻⁷**；两套独立实现（顶点有限体积 vs 格心有限体积）在表5 全部行上差 ≤ **1×10⁻⁴**（四位小数舍入临界）、烘干结束行差 **0.0**；离散质量守恒 **4.8×10⁻¹³**。

---

## 2. 主方法与可用基线的最终对比

| | 主方法 M3 | 可用基线 B3 |
|---|---|---|
| 空间离散 | 顶点有限体积（对偶控制体、守恒通量形式） | 格心有限体积（单元即控制体、守恒通量形式） |
| 时间积分 | Crank–Nicolson + **前 3 步后向 Euler 启动**（Rannacher） | Crank–Nicolson，**无启动** |
| 步长 | Δt = 1 s | Δt = 1 s |
| 烘干时长 | **57.4647 h** | **57.4575 h** |
| 表5（9 行 × 5 点，四位小数） | 见 `table5_main.csv` | 差 ≤ 1×10⁻⁴（末位 ±1） |
| 烘干结束行 | 中心 0.1500 | 差 **0.0** |
| 求解耗时 | 54.6 s | 58.5 s |

**基线不带 Rannacher 启动**是刻意的：它使这组交叉验证同时证明**启动处理不改变答案**（实测该处理在 Δt=1 s 时的影响为 1.41×10⁻⁷，比报告容差 5×10⁻⁵ 小 350 倍）。

**26 秒的时长差**与前两问同源：干燥尾段平坦，临近判据时 dC/dt 趋近于零，场内 10⁻⁷ 量级的差异即可推移穿越时刻。这是判据的固有属性。

---

## 3. 误差与不确定度分解

| 来源 | 量级 | 证据 |
|---|---|---|
| 空间离散（6 h 窗口，400↔800） | **3.2×10⁻⁷** | `main_validation.json#grid_refinement_6h` |
| 时间离散（全时程，Δt 10→1 s） | 时长差 **0.0036 h** | `main_validation.json#time_refinement_full_span` |
| 与解析解约化对照 | **6.05×10⁻⁷** | `verifier_validation.json#reference_vs_analytical` |
| 离散质量守恒 | 主 **4.8×10⁻¹³** / 基线 **2.2×10⁻¹³** | `main_validation.json#mass_balance` |
| 实现差异 | 表5 ≤ **1×10⁻⁴**（舍入）；结束行 **0.0**；时长 **26 s** | `verifier_validation.json` |
| Rannacher 启动 | **1.41×10⁻⁷**（Δt=1 s） | `methods/Q3/probes/risk_probe_summary.json` |

**参数与假设侧**：Q3 与 Q2 是**同一模型、同一参数、同一判据**，因此 Q2 的 11 项稳健性检验结论**直接适用**（已在 `q3_method_card.md` 声明复用，不重复扰动）：

| 扰动 | 对烘干时长的影响 |
|---|---|
| 质量方程读法替代 | **−14.72%** |
| T_inf +2 °C | **−6.08%** |
| D +5% | **−4.20%** |
| h_m ±5% | ∓0.6% |
| C_inf ±0.005 | ±0.2% |
| h +5% | −0.007% |

来源：`robustness/Q2/q2_robustness_summary.json`。

**读法**：数值误差在 10⁻⁷ 量级；**支配性不确定性来自假设与参数**（4%–15%），远大于数值误差。Q3 新增的只有数值配置，而它已被 0.0036 h 与 3.2×10⁻⁷ 覆盖。

---

## 4. 输出退化与集中度

| 指标 | 观测 | 判定 |
|---|---|---|
| 含水率沿半径单调性 | 单调递减 | 无内部极值 |
| 极值位置 | **中心 r=0 即全域最大**（全过程） | 无退化，判据由中心控制 |
| 判据穿越 | **单次** | 烘干时长定义良好 |
| 烘干结束行是否各处达标 | 是（最大 0.1500） | 符合"各处低于 0.15" |
| 烘干时长是否落在题目区间 | 是（57.46 ∈ [48, 72] h） | 通过 |
| 表5 的收敛形态 | 6 h→12 h 降幅最大，之后逐渐平缓 | 典型的扩散控制拖尾 |

> 来源：`main_validation.json#invariants`、`verifier_validation.json#invariants`

---

## 5. 稳健性与回退

主要证据见 §3 表格；完整清单沿用 `robustness/Q2/q2_robustness_summary.json`（11 项，整体 CONDITIONAL）。

**回退触发状态**：F3（显式 FTCS）**未触发**——两实现一致。证据：`verifier_validation.json`。

---

## 6. 局限与适用范围

1. **条件性（参数）**：以题目给定的 h_m、h 与附录3 经验式为条件（D 变化 5% 使时长变化 4.20%）。
2. **条件性（环境外推）**：恒温段 T_inf = 50 °C / C_inf = 0.05 kg/kg 为人为设定口径；**T_inf 变化 2 °C 即使时长变化 6.08%**。
3. **质量方程读法**：采用题目给定的 Fick 标准形式；替代读法使时长变化 14.72%（已量化）。
4. **端面忽略**：一维径向轴对称；全时程轴向质量渗透达长度的 13.7%（Q2 实测）。
5. **时长判据的固有不确定性**：干燥尾段平坦，26 s 的实现间穿越差是判据属性而非实现误差。
6. **不构成全局最优性声明**：本问为前向场模拟，不存在最优化问题。

---

## 7. 人类判定（与客观事实分离）

| decision_id | 类型 | 结论 |
|---|---|---|
| `q3_method_choice` | method_choice | M3 = 顶点有限体积 + CN（Δt=1 s）为主，B3 为验证 |
| `q3_time_scheme_startup` | method_choice | 采用 **Crank–Nicolson + 前 3 步后向 Euler 启动**（Rannacher 平滑） |
| `q3_result_verdict` | result_verdict | **A**：沿用 57.4647 h，表5 与 result3.xlsx 为定稿数值 |
| `q3_stability_verdict` | stability_verdict | **A**：判定稳定；稳健性结论继承 Q2；措辞条件化 |
| `q3_claim_scope` | claim_scope | **A**：全部保留 |

来源：`methods/Q3/q3_decisions.jsonl`。

---

## 8. 数值来源索引

| 数值 | 源文件 |
|---|---|
| 烘干时长、表5、交付物规格、耗时 | `metrics/main.json` |
| 网格/时间加密、质量守恒、不变量 | `metrics/main_validation.json` |
| 基线的表5 与时长 | `metrics/baseline.json`、`metrics/baseline_validation.json` |
| 解析解对照、逐点对比、时长差 | `metrics/verifier.json`、`metrics/verifier_validation.json` |
| 启动处理与步长扫描 | `methods/Q3/probes/risk_probe_summary.json` |
| 参数敏感性（继承） | `robustness/Q2/q2_robustness_summary.json` |
| 角色、快照、预算 | `results/Q3/experiments/round1/run_summary.json` 与 `runs/*/run_metadata.json` |
| 交付物 | `results/Q3/experiments/round1/result3.xlsx` |

**运行预算核实**：三个角色均 status=SUCCESS、return_code=0、executed_by_runner=true、degraded=false、budget_delta={} —— **无预算降级**。

**交付物规格核实**：`result3.xlsx` 单表 `Sheet1`，**3 448 数据行 × 21 数据列**；首行 t=60 s、末行 t=206 873 s（即 57.4647 h 的精确结束时刻）；首行距离 0–2.0 cm。

---

## 9. submission 链条状态

| 前置条件 | 状态 |
|---|---|
| 最终方法说明 `methods/Q3/q3_final_method_explanation.md` | 见本链条产物 |
| 最终结果分析（本文） | **完成** |
| writer package `results/Q3/reports/q3_solution_package_for_writer.md` | 见本链条产物 |
| 冻结数字 `frozen_numbers.json` | 待建模者完成 package sign-off 后生成 |

---

## 10. 与参考标杆的对照（自检）

- **符号/单位唯一**：时间统一 h（表5）与 s（交付物与内部计算），温度 °C，含水率 kg/kg（干基），长度 cm；
- **模型—代码—结果一致**：方法卡所述方案（顶点有限体积 + CN + Rannacher 启动）与 `q3_main.py` 一致，评审五项全 PASS；
- **约束逐条判**：模型契约 12 条硬约束逐条落到代码与验收；
- **收敛与最优性诚实**：网格/时间双加密、解析解约化对照、两套独立实现交叉验证；明确声明本问不涉及最优性；
- **诚实标注局限**：参数条件性、环境外推口径、质量方程读法、端面忽略、判据固有不确定性共五条已写明。
