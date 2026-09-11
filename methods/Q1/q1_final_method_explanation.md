# Q1 最终方法说明

> 本文是 Q1 的**权威方法说明**，供论文写作与 solution package 引用。来源：方法卡、决策账本、代码计划、最终结果与稳健性证据。
> 模型契约哈希：`f6ef7af5819f339c4676d271a52ab59ff379239d8ee7999de215d0239ee6acba`（`planning/model_contract.json`）

## 1. 模型对象与控制方程

圆柱形中药材，半径 R、长 25 cm，采用**一维径向轴对称**（决策 `g_framing_spatial_dimension`）。控制方程组：

$$\rho(C)c_p(C)\frac{\partial T}{\partial t}=\frac{1}{r}\frac{\partial}{\partial r}\left(k(C)\,r\,\frac{\partial T}{\partial r}\right),\qquad
\frac{\partial C}{\partial t}=\frac{1}{r}\frac{\partial}{\partial r}\left(D\,r\,\frac{\partial C}{\partial r}\right)$$

**边界条件**（第三类对流，移项形式）：
$$r=R:\ -k\frac{\partial T}{\partial r}=h(T-T_\infty),\quad -D\frac{\partial C}{\partial r}=h_m(C-C_\infty);\qquad r=0:\ \frac{\partial T}{\partial r}=\frac{\partial C}{\partial r}=0$$

**初值**：T = 28 °C、C = 2.55 kg/kg（全域均匀）。

**质量方程的读法**（决策 `g_assumption_mass_equation_form`）：取题目明文给定的 Fick 标准形式，ρ、c_p、k 只进入能量方程。

**几何**：Q1 中半径恒定 R = 2 cm（预热平衡阶段 0–1800 s，本问不涉及收缩）。

## 2. 数值方法

> **角色裁定（已完成）**：G4 决策 `q1_method_role_swap` 把**顶点（节点）形式提为主方法 M2**、格心形式降为可用基线 B2，并以顶点实现重新生成了 `result1.xlsx` 与全部运行快照。重排不改变任何报告数值：两法在全部 35 个报告点上温度差 **0.0**、含水率差 **≤1×10⁻⁴**（恰在四位小数舍入分界上），表面列 Richardson 极限只差 **9.7×10⁻⁷**；守卫证据见 `methods/Q1/probes/role_swap_evidence/role_swap_check.json`。

**空间**：**顶点有限体积**（对偶控制体、守恒通量形式）。节点 $r_j=j\Delta r$；控制体体积 $V_0=\pi\Delta r^2/4$、$V_j=2\pi r_j\Delta r$、$V_N=\pi(R^2-(R-\Delta r/2)^2)$；面面积 $A_{j\pm1/2}=2\pi r_{j\pm1/2}$。节点 0 的内侧面半径为 0，**轴对称条件由格式自动满足**；r=0 与 r=R 都是原生节点，报告位置零插值。Voronoi 权重之和恒等于 $\pi R^2$（实测误差 0.0）。

**时间**：半离散守恒系统交给 `scipy.integrate.solve_ivp` 的自适应隐式多步 **BDF**（rtol = 1e-9、atol = 1e-11、`dense_output=True`）。该方法没有固定步长，因此时间精度由**求解器容差加密**（rtol 1e-8 ↔ 1e-9，实测表值差 3.89×10⁻¹⁰）与**常扩散系数 Bessel 解析解对照**（6.18×10⁻⁷）共同认证。

**线性代数**：BDF 每步的内部带状牛顿求解。

**表面值**：r=R 是节点 N，**原生取值**，无需由外单元中心回算——这正是把顶点形式提为主方法的理由。

**离散质量守恒**：守恒通量形式逐面望远镜求和，使 $dW/dt=-2\pi R\,h_m(C_N-C_\infty)$ 在离散层面精确成立；以逐求解步分片的自适应求积测量残差得 **1.74×10⁻¹⁴**（相对失水量 5.41×10⁻¹¹）。

## 3. 参数

附录2：ρ = 820 kg/m³、c_p = 2600 J/(kg·K)、k = 0.36 W/(m·K)、h = 25 W/(m²·K)、h_m = 8×10⁻⁷ m/s、D = 7×10⁻⁹·exp(−0.89/C) m²/s。

**环境驱动**：附件1 实测序列（0–14400 s，步长 60 s，线性插值）；注意 t = 100 s 不是采样点，必须插值。

## 4. 决策链（塑造本方法的全部人类决定）

见 `methods/Q1/q1_decisions.jsonl`。关键项：

- 口径轴 1（条件式：先核实中心是否为全域最大）、轴 2（不适用）、轴 3（判据取最大值 + 另报达标率与体积加权平均含水率）
- 空间维度、对流系数、环境口径、质量方程读法（G1 全局决策）
- 方法选型（G2.5）、时间格式（实施阶段）、以及 G4 的角色重排 `q1_method_role_swap`（顶点提为主方法、格心降为基线）

## 5. 验证证据

| 项 | 结果 |
|---|---|
| 与解析解（Bessel 级数，常物性约化） | 主方法 6.18×10⁻⁷，见 `metrics/main_validation.json#analytical_cross_check` |
| 网格加密 | 400↔800 差 3.24×10⁻⁶，见 `metrics/main_validation.json#grid_refinement` |
| 时间精度（自适应 BDF 的容差加密） | rtol 1e-8↔1e-9 差 3.89×10⁻¹⁰，见 `metrics/main_validation.json#time_accuracy` |
| 离散质量守恒 | 残差 1.74×10⁻¹⁴，见 `metrics/main_validation.json#mass_balance` |
| 独立实现交叉验证 | 逐点差 ≤1.0×10⁻⁴、表面 Richardson 极限差 9.72×10⁻⁷，见 `metrics/verifier_validation.json#main_vs_baseline_real_problem` |
| 角色重排守卫（顶点主方法逐位复现既有顶点数值；格心数值核心逐字不变） | 9 项全 PASS，见 `methods/Q1/probes/role_swap_evidence/role_swap_check.json` |

## 6. 适用边界（必须随方法一并写入论文）

1. 结论以题目给定的 h_m、h 与对应附录经验式为条件；
2. 一维径向轴对称忽略端面轴向输运（量级已量化）；
3. 质量方程采用题目给定的 Fick 标准形式（替代读法的影响已量化）；
4. 数值方案由网格/时间加密实验认证，而非先验论证。
