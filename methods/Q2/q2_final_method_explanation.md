# Q2 最终方法说明

> 本文是 Q2 的**权威方法说明**，供论文写作与 solution package 引用。来源：方法卡、决策账本、代码计划、最终结果与稳健性证据。
> 模型契约哈希：`f6ef7af5819f339c4676d271a52ab59ff379239d8ee7999de215d0239ee6acba`（`planning/model_contract.json`）

## 1. 模型对象与控制方程

圆柱形中药材，半径 R、长 25 cm，采用**一维径向轴对称**（决策 `g_framing_spatial_dimension`）。控制方程组：

$$\rho(C)c_p(C)\frac{\partial T}{\partial t}=\frac{1}{r}\frac{\partial}{\partial r}\left(k(C)\,r\,\frac{\partial T}{\partial r}\right),\qquad
\frac{\partial C}{\partial t}=\frac{1}{r}\frac{\partial}{\partial r}\left(D\,r\,\frac{\partial C}{\partial r}\right)$$

**边界条件**（第三类对流，移项形式）：
$$r=R:\ -k\frac{\partial T}{\partial r}=h(T-T_\infty),\quad -D\frac{\partial C}{\partial r}=h_m(C-C_\infty);\qquad r=0:\ \frac{\partial T}{\partial r}=\frac{\partial C}{\partial r}=0$$

**初值**：T = 28 °C、C = 2.55 kg/kg（全域均匀）。

**质量方程的读法**（决策 `g_assumption_mass_equation_form`）：取题目明文给定的 Fick 标准形式，ρ、c_p、k 只进入能量方程。

**几何**：半径恒定 R = 2 cm。**物性随状态变化**，因此热与湿是**双向耦合**——温度场通过 $D(C,T)$ 反馈到含水率（实测 d ln D/dT = 3850/T² ≈ 每开尔文 4%）。

## 2. 数值方法

**空间**：**顶点有限体积**（对偶控制体、守恒通量形式）。节点 $r_j=j\Delta r$；控制体体积 $V_0=\pi\Delta r^2/4$、$V_j=2\pi j\Delta r^2$、$V_N=\pi(R^2-(R-\Delta r/2)^2)$；面面积 $A_{j+1/2}=2\pi(j+\tfrac12)\Delta r$。节点 0 的内侧面面积为零，**轴对称条件由格式自动满足**；r=0 与 r=R 都是原生节点，报告位置零插值。

**时间**：**Crank–Nicolson（θ=0.5，二阶、A-稳定）**，并以前 3 步后向 Euler 启动（Rannacher 平滑）。

**线性代数**：每步一次带状求解（scipy `solve_banded`），O(N)。

**表面值**：r=R 是节点，**原生取值**，无需重建。

## 3. 参数

附录3：ρ = 650+128C、c_p = 1450+2736·C/(C+1)、k = 0.21+0.38·C/(C+1)、D = 2.4×10⁻³·exp(−0.45/C)·exp(−3850/T)；h = 25 W/(m²·K)、h_m = 8×10⁻⁷ m/s（决策 `g_framing_convective_coefficients`）。

**环境驱动**：预热阶段取附件1 实测序列；恒温干燥阶段按决策 `g_framing_env_extrapolation` 维持 T_inf = 50 °C、C_inf = 0.05 kg/kg（数值经附件1 稳定段核实：T 均值 50.0049 °C、C 均值 0.04999）。

## 4. 决策链（塑造本方法的全部人类决定）

见 `methods/Q2/q2_decisions.jsonl`。关键项：

- 口径轴 1（条件式：先核实中心是否为全域最大）、轴 2（不适用）、轴 3（判据取最大值 + 另报达标率与体积加权平均含水率）
- 空间维度、对流系数、环境口径、质量方程读法（G1 全局决策）
- 方法选型、时间格式相关决定（G2.5 / 实施阶段）

## 5. 验证证据

| 项 | 结果 |
|---|---|
| 与解析解（Bessel 级数，常物性约化） | 见 `metrics/verifier_validation.json` |
| 网格加密 | 见 `metrics/main_validation.json#grid_refinement*` |
| 时间加密 | 见 `metrics/main_validation.json#time_refinement*` |
| 离散质量守恒 | 见 `metrics/main_validation.json#mass_balance` |
| 独立实现交叉验证 | 见 `metrics/verifier_validation.json#main_vs_baseline*` |

## 6. 适用边界（必须随方法一并写入论文）

1. 结论以题目给定的 h_m、h 与对应附录经验式为条件；
2. 一维径向轴对称忽略端面轴向输运（量级已量化）；
3. 质量方程采用题目给定的 Fick 标准形式（替代读法的影响已量化）；
4. 数值方案由网格/时间加密实验认证，而非先验论证。
