# Q1 方法卡：预热平衡阶段温湿耦合场（0–1800 s）

> 子问题：Q1 ｜ 生成阶段：G2 方法筛选（§3 的角色分工在 G4 按决策 `q1_method_role_swap` 更新）｜ 本卡由 AI 依据 `planning/parse/problem_parse.json`、`planning/classification/problem_classification.json`、`workspace/data/data_profile.json` 与 `planning/framing_decisions.jsonl` 中的已确认口径编制。
> 本卡只提出候选与证据，**不代替建模者在 G2.5 / G4 做出的人类选择**。

## 1. 问题与交付物（口径已冻结）

- 几何：圆柱，半径 R = 2 cm，长 25 cm；空间维度取**一维径向轴对称**（decision_id: `g_framing_spatial_dimension`）。
- 未知场：温度 T(r,t)、水分浓度 C(r,t)（干基，kg/kg）。
- 初值：T(r,0) = 28 °C，C(r,0) = 2.55 kg/kg（全域均匀）。
- 边界驱动：烘房温度 T∞(t) 与水分浓度 C∞(t)，取自附件1（0–14400 s，步长 60 s，线性插值；t = 100 s 非采样点，必须插值）。
- 交付：表1/表2（7 时刻 × 5 位置，四位小数）与 result1.xlsx（t = 0–1800 s 每 1 s × r = 0–2.0 cm 每 0.1 cm 的两张完整场）。
- 承重口径：质量方程采用题目给定的 Fick 标准形式，ρ、c_p、k 只进入能量方程（decision_id: `g_assumption_mass_equation_form`）。

## 2. 控制方程组（四问共用骨架）

$$\rho c_p \frac{\partial T}{\partial t}=\frac{1}{r}\frac{\partial}{\partial r}\left(k\,r\,\frac{\partial T}{\partial r}\right),\qquad
\frac{\partial C}{\partial t}=\frac{1}{r}\frac{\partial}{\partial r}\left(D\,r\,\frac{\partial C}{\partial r}\right)$$

边界条件（第三类对流，移项形式）：
$$r=R:\quad -k\frac{\partial T}{\partial r}=h\,(T-T_\infty),\qquad -D\frac{\partial C}{\partial r}=h_m\,(C-C_\infty);\qquad
r=0:\quad \frac{\partial T}{\partial r}=\frac{\partial C}{\partial r}=0$$

参数（Q1，附录2）：ρ = 820 kg/m³，c_p = 2600 J/(kg·K)，k = 0.36 W/(m·K)，h = 25 W/(m²·K)，h_m = 8×10⁻⁷ m/s，D = 7×10⁻⁹·exp(−0.89/C) m²/s。

## 3. 角色化候选（role-based shortlist）

> **角色重排（G4 决策 `q1_method_role_swap`）**：本卡在 G2 阶段提出的 M1（格心有限体积 + Crank–Nicolson）与 B1（节点守恒通量式 + BDF）在 G3 各自独立实现并互相验证后，建模者裁定把**顶点（节点）形式提为主方法、格心形式降为可用基线**。理由是报告中承担全部早期误差预算的表面列：在节点形式下 r = R 本身就是离散系统的原生未知量，而在格心形式下它必须由最外层单元中心经 Robin 关系回算。两种离散在全部 35 个报告点上温度差 0.0、含水率差 ≤1×10⁻⁴，表面列 Richardson 极限只差 9.7×10⁻⁷，故重排不改变任何报告数值。下文保留 M1/B1 的原始编号，以便与 G2 阶段的筛选记录对应。

### main_candidate — M2：顶点（节点）有限体积 + 自适应 BDF

- **离散**：顶点式（对偶控制体、守恒通量形式）。节点 $r_j=j\Delta r$，控制体体积 $V_0=\pi\Delta r^2/4$、$V_j=2\pi r_j\Delta r$、$V_N=\pi(R^2-(R-\Delta r/2)^2)$，面 $A_{j\pm1/2}=2\pi r_{j\pm1/2}$。节点 0 的内侧面半径为 0，**轴对称条件由格式自动满足**，无需对 1/r 奇点做特殊处理。Voronoi 权重之和恒等于 $\pi R^2$（实测误差 0.0）。
- **边界与表面值**：外表面的对流项直接进入节点 N 的守恒方程（通量 $2\pi R h_m(C_N-C_\infty)$）；r = R 即节点 N，**报告的表面值是原生解**，不经过任何回算。
- **时间**：把半离散守恒系统交给 `scipy.integrate.solve_ivp` 的自适应隐式多步 BDF（rtol = 1e-9、atol = 1e-11）。因为没有固定步长，时间精度用**求解器容差加密**（rtol 1e-8 ↔ 1e-9，实测表值差 3.89×10⁻¹⁰）与**常扩散系数 Bessel 解析解对照**（6.18×10⁻⁷）认证。
- **线性代数**：BDF 每步的内部带状牛顿求解。
- **为什么作主候选**：报告的两个头条量都是表面值；节点形式让表面值成为方程的直接未知量，避免了格心形式中"由最外层单元中心回算"这一额外近似；同时守恒通量形式给出可核验的离散质量守恒（Voronoi 权重和恒等于 πR²，实测残差 1.74×10⁻¹⁴）。
- **前置条件**：Q4 的收缩域需叠加归一化坐标与表观对流项。

### usable_baseline — B2：格心有限体积 + Crank–Nicolson + Thomas

- **离散**：格心有限体积；单元体积 ∝ (r²₊ − r²₋)，面通量用二阶中心差分；r = 0 处面面积为 0，对称条件**由格式自动满足**。
- **边界**：外表面用半单元串联热阻处理，通量 = A_R(T_N − T∞)/(Δr/(2k) + 1/h)；报告的表面值由 Robin 关系 $C_s=(C_N\,2D/\Delta r+h_m C_\infty)/(2D/\Delta r+h_m)$ 从最外层单元中心回算——这正是主方法要避免的那一步。
- **时间**：**Crank–Nicolson（θ=0.5，二阶、A-稳定、仍为全隐式）**，定步长 Δt = 0.25 s；非线性 D(C) 采用滞后系数（把系数固定在上一时间层，使每步仍是线性三对角系统）。原定的后向 Euler 在 round1 实现阶段被实测否决：最外层有限体积单元的时间常数仅 τ≈0.503 s（Δr=0.05 mm 使边界扩散耦合很强），后向 Euler 的误差几乎全部堆积在 r=2.0 cm 表面列，err≈4.4×10⁻⁴·Δt，压到 5×10⁻⁵ 以下需 Δt≲0.02 s，在 Q2/Q3/Q4 的 259200 s 时程上不可行。决策见 `q1_time_scheme_amendment`，证据见 `methods/Q1/probes/time_scheme_diagnostic.txt`。
- **线性代数**：三对角，Thomas 追赶法，O(N) 每步。
- **独立性**：空间离散（格心 vs 顶点）、时间推进（定步长 θ 法 vs 自适应 BDF）、表面值来源（回算 vs 原生节点）三处都与主方法不同，因此可作为独立交叉验证，而不是主方法的重复实现。

### conditional_fallback — F1：显式 FTCS（前向 Euler + 中心差分）

- **触发条件**：当且仅当 M2 与 B2 在指定点四位小数上不一致、且排查后仍无法归因时启用，作为第三方独立核算。稳定步长 Δt ≤ Δr²/(2·D_max)（risk-probe summary 给出数值）。

## 4. risk-probe summary（摘要）

完整证据见 `methods/Q1/probes/risk_probe_summary.json`（含契约要求的六个小节与 verdict）。关键实测：

| 检查 | 结果 |
|---|---|
| executability：与 Bessel 级数解析解对比（恒定 D、对流边界） | 最大绝对误差 **4.3×10⁻⁶**（N=400），观测空间收敛阶 ≈ 1.73 |
| 与独立基线的交叉验证（真实 Q1 参数） | 最大差异 **2.31×10⁻⁵**，在四位小数容差内 |
| 网格加密 200→400 | 最大差 **8.5×10⁻⁶**（四位小数稳定） |
| 参数扰动：h_m 放大 5% | 最大差 **0.0352** —— 传质系数是本题最敏感参数，论文必须给出该敏感性 |
| output_degeneracy | **中心即全域最大值**（沿半径单调递减），无内部极值；T 沿半径单调递增；四位小数下网格值互不相同，无输出退化 |
| assumption_checks | D 动态范围与显式稳定步长已量化；质量方程采用 Fick 标准形式；r=0 对称由控制体面半径为零自动满足 |
| scale_check | 格心实现跑完 Q1（7200 步 × 400 单元）耗时 ≈19 s；顶点实现在同一时程上约 6 分钟（BDF rtol 1e-9），后者已由运行器快照记录 |

**探针自身发现并修正的三个问题（记录在案，避免复现）**：
1. 外表面必须由对流边界关系式回算（`C_s=(C_N·2D/Δr+h_m·C∞)/(2D/Δr+h_m)`）；直接把最外层单元中心值当作表面值只有一阶精度，会独自吃掉整个误差预算（实测使误差达 1.2×10⁻²）。**注意：这条只适用于格心形式；顶点形式的表面值是原生节点值。**
2. 把 `(1/r)∂/∂r(rD∂C/∂r)` 展开成 `D·[C_rr + C_r/r]` 会**丢掉交叉项** `(∂D/∂r)(∂C/∂r)`；在 D(C) 变化约 20% 时该项误差可达 6×10⁻²，导致独立基线与主方法出现假性不一致。
3. 边界半单元的扩散通量符号必须为负（外法向通量使节点失能）；符号取反会形成反扩散并使积分发散。

## 5. baseline validity（基线有效性论证）

B2 **能完成真任务**：它与 M2 使用同一模型合同、同一输入哈希、同一输出网格，独立产出表1/表2 所需的全部数值，因此属于 `usable_baseline`，不是只能跑通流程的 `diagnostic_reference`。独立性依据：空间离散（格心有限体积 vs 顶点守恒通量形式）与时间推进（定步长 Crank–Nicolson vs 自适应 BDF）**均不同**，B2 不以 M2 的结果作为数值输入。角色互换后的守卫证据见 `methods/Q1/probes/role_swap_evidence/role_swap_check.json`。

## 6. 承重假设与风险

| 假设 | 性质 | 若不成立的影响 |
|---|---|---|
| 一维径向轴对称 | 简化 | 轴向质量渗透 72 h 可达 5.9 cm/端（占长度 23.7%），已在论文中量化为局限 |
| 忽略水分汽化潜热 | 简化 | 题目未给潜热；会使升温阶段偏快 |
| 局部热力学平衡 | 必要 | 无此项则无法用 T∞、C∞ 作边界驱动 |
| 质量方程用 Fick 标准形式（ρ 不入质量方程） | 必要（已冻结） | 若改湿基自洽式，等效扩散系数差 (1+C) 倍（C=2.55 时 3.55 倍），烘干时长会明显改变 |
| 恒温阶段 T∞ = 50 °C、C∞ = 0.05 kg/kg（Q2–Q4） | 必要（已冻结） | 由附件1 稳定段实测核实 |

## 7. 回退触发条件

F1 仅在 M2 与 B2 的指定点四位小数不一致且无法归因时启用；启用须记录触发时刻与不一致量级，不得静默替换主方法。

## 8. 决策历史

- G1 已确认：口径轴1 条件式（先核实中心是否为全域最大）、口径轴2 不适用、口径轴3 判据取最大值并另报达标率与体积加权平均含水率；框架 1/2/3/5 已定；框架4 取 T1 当前物理坐标口径、半径外留空；列集按题目间隔铺满、末列由"药材表面"替换。全部原话见 `planning/framing_decisions.jsonl`。
- G2 本卡：提出 M1 / B1 / F1 三角色候选并给出探针证据。
- G2.5 `q1_method_choice`：M1 为主方法、B1 为验证（由建模者作出）。
- 实施阶段 `q1_time_scheme_amendment`：M1 的时间积分由后向 Euler 改为 Crank–Nicolson。
- G4 `q1_method_role_swap`：把顶点（节点）守恒通量式提为主方法 M2，格心有限体积 + Crank–Nicolson 降为可用基线 B2；V1（Bessel 半解析参照）与 F1 不变。格心实现的数值核心逐字保留，新主方法在全部报告点上与既有顶点实现数值完全一致（守卫：`methods/Q1/probes/role_swap_evidence/role_swap_check.json`）。
