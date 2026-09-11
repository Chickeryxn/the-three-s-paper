# Q1 代码计划（code plan）

> 目标语言：Python 3.14（numpy 2.5.1 / scipy 1.18 / openpyxl 3.1.5）
> 轮次：round1 —— 预热平衡阶段 0–1800 s
> 批准决策：`q1_method_choice`（原 M1 主方法、B1 验证）、`q1_time_scheme_amendment`（格心实现的时间格式改为 Crank–Nicolson）；角色分工经 G4 决策 `q1_method_role_swap` 重排为 **M2 主方法、B2 基线**
> 模型契约：`planning/model_contract.json`，哈希 `f6ef7af5819f339c4676d271a52ab59ff379239d8ee7999de215d0239ee6acba`

## 1. 角色与脚本

| 角色 | ID | 脚本 | 说明 |
|---|---|---|---|
| main_candidate | **M2** | `code/Q1/q1_main.py` | 顶点（节点）守恒通量式 + `solve_ivp` BDF（rtol 1e-9、atol 1e-11） |
| usable_baseline | **B2** | `code/Q1/q1_baseline.py` | 格心有限体积 + Crank–Nicolson + Thomas |
| verifier | **V1** | `code/Q1/q1_verifier.py` | Bessel 半解析参照 + 契约不变量核验 |
| conditional_fallback | F1 | 本轮不实现 | 触发条件未观测到（M2 与 B2 逐点差 ≤1.0e-4，表面列 Richardson 极限差 9.7e-7） |

角色分工在 G4 按决策 `q1_method_role_swap` 重排：顶点形式提为主方法，格心形式降为可用基线。两者的数值核心都是 G3 阶段已验证实现的**逐字复用**，重排不改变任何报告数值；守卫证据见 `methods/Q1/probes/role_swap_evidence/role_swap_check.json`。

主方法与可用基线均须**完整实现并各自运行**；F1 只记录触发条件，不展开实现。

## 2. 输入字段与单位

| 输入 | 来源 | 单位 | 处理 |
|---|---|---|---|
| `T_inf(t)` | `workspace/data_clean/attachment1_env.csv` | °C | 线性插值；注意 t=100 s 非采样点 |
| `C_inf(t)` | 同上 | kg/kg | 线性插值 |
| `rho, cp, k` | 附录2（Q1 为常数） | kg/m³, J/(kg·K), W/(m·K) | 820 / 2600 / 0.36 |
| `h, h_m` | 附录2 | W/(m²·K), m/s | 25 / 8e-7 |
| `D(C)` | 附录2 | m²/s | `7e-9*exp(-0.89/C)` |
| 初值 | 题目 | °C, kg/kg | T=28、C=2.55，全域均匀 |

## 3. B2 计算步骤（格心有限体积 + Crank–Nicolson；G3 阶段的原 M1）

1. 读附件1，构造 `T_inf(t)`、`C_inf(t)` 插值函数。
2. 建格心有限体积网格：N=400，`dr=R/N`，单元中心 `r_i=(i-0.5)dr`，面 `r_{i±1/2}=i·dr`；单元体积 `V_i=π(r_{i+1/2}²-r_{i-1/2}²)`，面面积 `A=2πr`。
3. 组装热方程三对角矩阵（k 为常数，矩阵不随时间变化，只组装一次）；外表面用半单元串联热阻 `G_h=A_R/(dr/(2k)+1/h)`。
4. 时间循环 **Crank–Nicolson（θ=0.5，二阶、A-稳定）**，Δt=0.25 s，N=800：
   - 隐式解温度（Thomas 追赶法）；
   - 滞后系数 `D(C^n)`，面扩散系数取相邻单元算术平均，组装质量三对角并求解；
   - 末层单元的外表面电导 `G_m=A_R/(dr/(2D_N)+1/h_m)`；
   - **时变边界项必须取 `b(t^{n+1})` 作隐式、`b(t^n)` 作显式**；把隐式项取在中点会引入 `O(Δt·b')` 的系统偏差（实测在 Δt=0.25 s 时约 3×10⁻⁴ °C）。

> 时间格式变更记录：原计划的后向 Euler 已按决策 `q1_time_scheme_amendment` 改为 Crank–Nicolson。依据是 round1 实测：最外层有限体积单元的时间常数仅 τ≈0.503 s，后向 Euler 的误差几乎全部集中在 r=2.0 cm 表面列（err≈4.4×10⁻⁴·Δt），压到 5×10⁻⁵ 以下需 Δt≲0.02 s，在 Q2/Q3/Q4 的 259200 s 时程上不可行。
5. **表面值回算**：`C_s=(C_N·2D_N/dr + h_m·C_inf)/(2D_N/dr + h_m)`，温度同理。**禁止**直接把最外层单元中心值当表面值（一阶误差会独占误差预算，风险探针已实测）。
6. 报告映射：以 `[单元中心..., R]` / `[场值..., 表面值]` 构造三次样条，在题目要求的物理半径处取值。
7. 产出：表1/表2（7 时刻 × 5 位置，四位小数）；`result1.xlsx` 两张工作表（A 列时间每 1 s、首行距离 0–2.0 cm 每 0.1 cm）。

## 4. M2 计算步骤（顶点守恒通量式 + 自适应 BDF；G3 阶段的原 B1）

1. 同一输入；节点式网格 `r_j=j·dr`。
2. 守恒通量形式：内部节点用面通量差商；r=0 用 L'Hôpital 形式 `4D_0(C_1-C_0)/dr²`；r=R 用半单元体积 `V_N=(R²-(R-dr/2)²)/2` 与外法向通量 `h_m(C_N-C_inf)`。
3. **必须保持守恒通量形式**：把算子展开成 `D·[C_rr + C_r/r]` 会丢掉交叉项 `(∂D/∂r)(∂C/∂r)`，在变 D 下造成 6e-2 量级的假性偏差（风险探针已实测）。
4. 时间推进交给 `scipy.integrate.solve_ivp(method="BDF", rtol=1e-9, atol=1e-11)`，并**必须检查 `sol.success`**。
5. 报告映射：**r = 0 与 r = R 都是原生节点，报告位置零插值、零回算**；交付物 `result1.xlsx` 的 0.1 cm 网格由节点三次样条插值得到。产出与 B2 **直接可比**的表格。
6. 离散质量守恒：Voronoi 权重之和恒等于 πR²；守恒通量形式逐面望远镜求和，使 `dW/dt = −2πR·h_m(C_N−C∞)` 在离散层面精确成立。残差用逐求解步分片的自适应求积（另以 0.25 s 均匀网格 Simpson 交叉核对）测量。

## 5. V1 验证者步骤（独立数值路径）

1. **不读 M2/B2 的结果作为唯一数值输入**：V1 自己从模型契约与附件1 出发。
2. 构造半解析参照：冻结 `D` 为初始含水率处的值，用圆柱扩散的 Bessel 级数解（对流边界，特征方程 `λJ₁(λ)=Bi·J₀(λ)`，Bi=h_m·R/D）给出参照场。
3. 核验契约不变量（基于 V1 自己的计算）：全域水量变化与表面通量一致；C 沿半径单调递减、T 单调递增；r=0 对称条件成立。
4. 与 M2、B2 的输出做**差异比较**（比较时读取它们的结果，但独立的参照值来自 V1 自身的解析计算）。

## 6. 可比的输出与指标

主方法与基线必须产出同构的量，供直接比较：

| 指标 | 定义 | 容差 |
|---|---|---|
| `max_abs_diff_main_baseline` | 表1/表2 全部 35 个点上的最大绝对差 | < 5e-5 |
| `max_abs_err_vs_analytical` | 与 Bessel 参照的最大绝对差 | < 5e-5 |
| `mass_balance_rel_error` | 全域水量变化与表面通量积分之差，相对量 | < 1e-6 |
| `reported_4dp` | 表格值的四位小数呈现 | 与源值一致 |

## 7. 实现必须监控的风险探针条件

- 网格加密：Δr 三档（N=100/200/400），指定点四位小数须不变；
- **时间精度**：M2 是自适应 BDF，没有固定步长，改用**求解器容差加密**（rtol 1e-8 ↔ 1e-9，N=800）逐报告时刻比较，实测最大差 3.89×10⁻¹⁰；B2 则用步长加密（Δt = 0.5 / 0.25 s）。两者的对照量还有常扩散系数 Bessel 解析解（M2 为 6.18×10⁻⁷）；
- **表面列定点收敛**：在最难的时刻（t=100 s，边界层最薄）对 N=200/400/800 做 Richardson 外推，N=800 的误差须 < 5×10⁻⁵；该点用整场网格加密判定不可靠，必须单独核验；
- 表面值必须由边界关系回算；
- h_m 放大 5% 时末态场最大变化 0.0352（已知敏感性，须在 `metrics` 中复现该量级）；
- 输出不得退化：中心即全域最大值，四位小数下网格值互异。

## 8. 回退触发条件评估

- 条件：M2 与 B2 在表1/表2 指定点四位小数上不一致且无法归因；
- 本轮判定：**未触发**（round1 实测：35 个报告点温度差 0.0、含水率差 ≤1.0e-4，在含一个末位单位的容差内；表面列 Richardson 极限差 9.7e-7）；
- 若触发：按契约记录触发时刻与不一致量级，并启用 F1（显式 FTCS）作第三方核算。

## 9. 轮次产物

```text
results/Q1/experiments/round1/
├── figures/        # Type 1 诊断图（内部使用）
├── tables/         # 表1、表2 的 CSV 与 Markdown
├── metrics/
│   ├── main.json              main_validation.json
│   ├── baseline.json          baseline_validation.json
│   └── verifier.json          verifier_validation.json
└── run_summary.json
```

同时产出交付物 `result1.xlsx`（写入 `results/Q1/experiments/round1/`，原始模板 `workspace/data_raw/result1.xlsx` 保持只读），以及代码评审 `code/Q1/reviews/q1_python_review.json`（五项命名检查：syntax / input_contract / method_alignment / reproducibility / output_contract）。

## 10. 待确认的格式细节

`result1.xlsx` 的 A 列起始行：模板示例首行为 `1`。本计划默认**严格照模板从 t=1 起**（1800 行）。若建模者希望含 t=0，须在实施前说明。
