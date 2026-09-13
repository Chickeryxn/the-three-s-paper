# 图表规划（四问共用）

> 依据：`g_figure_plan_scope`（建模者 ①A ②A ③A）。参考标杆：resource-library `papers/2020A_paper_structure`、
> `tables/2020A_table_result_reflow`、`figures/topjournal-style`；上游 `nature-figure/multipanel-evidence-architecture`。
> 容量参照（同一维热传导题型获奖论文）：2020A 四篇分别为 26/8/23/11 图、5/5/4/3 表。
> 本规划只保留"每条视觉都承载一条已核验声明"的图；Type 1 诊断图一律不进论文。

## 0. 视觉系统（全图统一）

- 主方法 = `#1A6FC4`；可用基线 = 灰 `#767676`；判据线 = 黑虚线；方向色只在"有符号的变化量"上使用（正 `#2E9E44` / 负 `#E53935`）。
- 数据 alpha = 1.0（不透明），饱和深色；白底、左/下细黑轴、**默认去网格**；图例黑边不透明。
- 中文宋体、西文与数字 Times 类；轴标签带单位；标题即结论。
- Type 2–4 图一律输出到 `paper/figures/` 并写同名 `\<name>.render.json`（`status=PASS`、`rendered_at`、`checks`、`source`），栅格 ≥ 300 dpi。

## 1. 论文图（Type 3，每图一条主结论）

### 图1 `fig01_model_setup_and_environment.png` — 机制与口径
- **类型**：Type 3（示意图 + 数据面板）｜**目标节**：模型假设 / 建模准备
- **核心声明**：模型把三维药材简化为**一维径向轴对称**的圆柱，两阶段环境（预热实测 + 恒温外推）由附件1 驱动。
- **面板**：(a) 圆柱截面与第三类对流边界、r=0 对称、收缩后的当前半径 R(t) 示意；(b) 附件1 实测 T\infty(t)、C\infty(t) 序列与 14400 s 后的外推口径（T\infty=50 °C、C\infty=0.05 kg/kg）。
- **来源**：附件1（`workspace/data_clean/attachment1_env.csv`）、`g_framing_env_extrapolation`、`g_framing_spatial_dimension`。
- **图注（草拟，条件式）**：*图1 模型几何与边界驱动。(a) 药材按一维径向轴对称处理：r=0 处对称、r=R(t) 处第三类对流；(b) 预热阶段的环境温湿度取附件1 实测序列（线性插值），14400 s 之后按已确认口径维持 T\infty=50 °C、C\infty=0.05 kg/kg。该外推为建模口径，非实测数据。*
- **版面（2026-09-11 修订）**：示意图 (a) 原先把 Robin 条件的两条公式直接写在图内，
  与正文第 5.1 节重复，且字号被压到不足 8 pt；现改为纯文字说明
  "r = R(t)：第三类对流边界（表面对流换热与传质）"，**示意图内不再出现任何公式**。
  同时该面板的所有文字改为黑色，收缩后的半径改用**黑色虚线**（原先用红色），
  即改由线型而非颜色区分初始域与当前域；(b) 面板的 "14400 s" 注记一并改黑。
  (b) 中的红/蓝曲线为数据序列，带有图例、按"颜色 + 线型"双重区分，保持不变。

### 图2 `fig02_preheat_fields.png` — 预热阶段温湿场
- **类型**：Type 3｜**目标节**：问题1 结果
- **核心声明**：0–1800 s 内**以升温为主、失水仅限表层**。
- **面板**：(a) T(r) 剖面（100/300/600/900/1200/1500/1800 s）；(b) C(r) 剖面（同时刻）；(c) 中心与表面的时程曲线。
- **冻结声明**：`q1_T_center_1800s`(33.5753 °C)、`q1_T_surface_1800s`(36.7856 °C)、`q1_C_center_1800s`(2.55)、`q1_C_surface_1800s`(1.5102)。
- **来源**：`results/Q1/experiments/round1/result1.xlsx`、`metrics/main.json`。
- **图注（草拟）**：*图2 预热平衡阶段（0–1800 s）的温度与水分场。(a)、(b) 为 7 个报告时刻的径向剖面；(c) 为中心与表面时程。**在题目给定的 h_m = 8×10⁻⁷ m/s 与附录2 经验式下**，1800 s 时中心温度 33.5753 °C、表面 36.7856 °C，而干基含水率中心仍为 2.5500 kg/kg、仅表面降至 1.5102 kg/kg——水分扩散特征时间约 22 h，远长于本阶段 30 min。*

### 图3 `fig03_drying_curve.png` — 长时程烘干曲线
- **类型**：Type 3｜**目标节**：问题3 结果（问题2 共享同一模型）
- **核心声明**：烘干由**内部扩散**控制，判据在 57.46 h 首次越过。
- **面板**：单幅图——中心 / r = 1.0 cm / 表面三个位置的含水率时程 + 0.15 kg/kg 判据线 + 烘干时刻标注。
- **说明**：原图 (a)(b) 两幅信息重复（全域最大含水率曲线与中心时程同形），故只保留三位置时程；
  **参数与口径敏感性已移出本图**，单独成图12 并放在 §8.3 灵敏度分析处，与表9 逐行对应。
- **冻结声明**：`q2_drying_time`/`q3_drying_time`(57.4647 h)。
- **来源**：`results/Q3/experiments/round1/result3.xlsx`（每 60 s 完整场；Q2 与本问共享同一模型）、`metrics/main.json`。
- **图注（草拟）**：*图3 三个位置的含水率时程。虚线为 0.15 kg/kg 判据，点线标出烘干时刻 57.4647 h。*

### 图12 `fig12_sensitivity.png` — 参数与口径灵敏度
- **类型**：Type 3｜**目标节**：§8.3 参数与口径灵敏度（与表9 配对）
- **核心声明**：烘干时长对表面传质系数 h_m 最不敏感（±5% 仅 ∓0.5%，且双向近似对称），
  对扩散系数与环境温度依次更敏感，而主导不确定性来自质量方程的读法这一口径（−14.7%）。
- **面板**：单幅横向条形图——h_m ±5%、C∞ ±0.005（均为双向）、D +5%、T∞ = 52 °C（单向）。
- **冻结声明**：`q2_sens_h_m_minus5pct`、`q2_sens_h_m_plus5pct`、`q2_sens_c_inf_low`、`q2_sens_c_inf_high`、`q2_sens_D_plus5pct`、`q2_sens_T_inf_plus2C`。
- **来源**：`robustness/Q3/q3_robustness_summary.json`，基准时长读自 `results/Q3/experiments/round1/metrics/main.json`。
- **图注（草拟）**：*图12 烘干时长对单项扰动的响应（问题二与问题三）。正值表示时长变长；
  h_m 与环境水分浓度为双向扰动，其条形两两成对，与表9 的对应行数值一致。*

### 图4 `fig04_shrinkage_effect.png` — 收缩效应
- **类型**：Type 3｜**目标节**：问题4 结果
- **核心声明**：**收缩不可忽略**——本问烘干时长 52.6361 h 比不考虑收缩的 57.4647 h 短 8.4%，不能由 Q3 直接推算。
- **面板**：(a) 附件2 半径 R(t) 收缩曲线（2.000 → 1.198 cm）；(b) Q3（不收缩）与 Q4（收缩）的全域最大含水率曲线同判据线对比；(c) 表面列含水率对比。
- **冻结声明**：`q4_drying_time_hours`(52.6361)、`q4_R_at_drying_end_cm`(1.200)、`q4_shrinkage_percent`(40.1)、`q4_vs_q3_drying_time_hours`(−4.8286)、`q3_drying_time`(57.4647)。
- **来源**：`results/Q4/experiments/round1/result4.xlsx`、`metrics/main.json`、附件2、`results/Q3/…/result3.xlsx`。
- **图注（草拟）**：*图4 尺寸收缩对烘干时长的影响。(a) 药材半径按附件2 由 2.000 cm 收缩至 1.198 cm（−40.1%）。(b) 同判据线下，考虑收缩（52.6361 h）比不考虑收缩（57.4647 h）提前 4.83 h。附录4 的扩散系数前因子比附录3 小 5.7 倍，**若忽略收缩会显著拉长时长**；收缩把扩散路径缩短到 0.599 倍，其效应压倒了扩散系数的下降。*

### 图5 `fig05_numerical_verification.png` — 数值可信度
- **类型**：Type 3｜**目标节**：模型检验
- **核心声明**：四问的数值解经**解析对照、三重加密与独立实现交叉验证**；移动边界下的守恒可由解析恒等式逐时步核验。
- **面板**：(a) 网格/时间加密残差（四问，对数刻度）；(b) 主方法与 Bessel 解析解的剖面/点对照；(c) 主方法与独立基线的逐点差（含 1 个末位单位容差带）；(d) Q4 移动边界一致性（关闭传质后 C 与 C\0 的偏差）。
- **冻结声明**：`q1_analytical_max_abs_err`、`q2/3_analytical_*`、`q4_reference_max_abs_err`、各 `*_grid_refinement_diff`、`*_time_*`、`*_mass_balance_rel`、`q1_independent_implementations_diff`、`q4_moving_boundary_dev`。
- **来源**：四问 `metrics/*_validation.json`。
- **图注（草拟）**：*图5 数值可信度证据。(a) 网格与时间加密残差；(b) 与 Bessel 级数解析解的对照（常物性约化）；(c) 主方法与独立基线的逐点最大差，虚线为一个末位单位的容差；(d) Q4：关闭表面传质后干基含水率必须严格不变，实测偏差 1.4×10⁻¹³。*
- **版面（2026-09-11 修订）**：原为 1×4 单行排布（8.2×2.7 in），缩入正文后每个子图仅约 1.7 in 宽，
  刻度与注记不可读。现改为 **2×2**（7.4×5.3 in），正文按 `width=0.92\textwidth` 引入，
  四个子图的最终宽度约为原来的 1.9 倍。

### 图6 `fig06_method_and_roles.png` — 方法链与角色分工
- **类型**：Type 3（流程示意）｜**目标节**：模型建立 / 求解思路
- **核心声明**：四问共享同一控制方程骨架，只在**物性口径、时间方案与坐标口径**上分支；每问都有主方法、可用基线与独立验证三条互不重复的实现路径。
- **面板**：单面板流程图（G1 口径 → 方程骨架 → Q1/Q2/Q3/Q4 分支 → 三角色 → 验证闭环）。
- **来源**：四问方法卡与决策账本。
- **图注（草拟）**：*图6 四问的方法链与角色分工。Q1 用顶点有限体积 + 自适应 BDF；Q2/Q3 用顶点有限体积 + Crank–Nicolson（前 3 步后向 Euler 启动）；Q4 在归一化坐标 \xi = r/R(t) 上增加表观对流项 \xi\dot R/R。每问的主方法、可用基线与独立验证来自不同的空间离散与时间推进，不共享数值输入。*
- **版面（2026-09-11 修订）**：原为 9.4×3.6 in 的 2.6:1 长条，缩入正文后高度只剩约 6 cm，
  6.4 pt 的字号实际落到 4 pt 上下。现改为 7.6×5.0 in（约 1.5:1），字号提到 8.4–9.2 pt，
  两条通栏说明拆成两行；并在生成函数内加入**实测断言**——逐框量测文字包围盒与框体的余量，
  最坏越界必须 ≤ 0 pt，该结论写进 `fig06_method_and_roles.pdf.render.json` 的 procedural checks。
  （原先只靠肉眼与 text-vs-text 重叠检查，抓不到"文字溢出所属方框"这一类缺陷。）

## 2. 附录图（Type 4）

| ID | 内容 | 来源 |
|---|---|---|
| `figA1_q2_full_field.png` | Q2 完整温湿场演化（3 h 内的 T 与 C） | `results/Q2/…/metrics/main.json`、`result2.xlsx` |
| `figA2_q3_full_field.png` | Q3 完整含水率场与各位置时程（0–57.46 h） | `results/Q3/…/result3.xlsx` |
| `figA3_q4_shrinking_field.png` | Q4 收缩域内含水率的时空演化（物理坐标） | `results/Q4/…/result4.xlsx` |

## 3. 表

| ID | 内容 | 类型 | 来源 |
|---|---|---|---|
| 表1/表2 | Q1 温湿场（7 时刻 × 5 位置，四位小数） | 题目指定 | `metrics/main.json` |
| 表3/表4 | Q2 温湿场（3 h 内每 0.5 h × 5 位置） | 题目指定 | `metrics/main.json` |
| 表5 | Q3 含水率（每 6 h × 5 位置，末行烘干结束） | 题目指定 | `metrics/main.json` |
| 表6 | Q4 含水率（每 6 h × 0/0.5/1.0/1.5 cm/药材表面，末行烘干结束） | 题目指定 | `metrics/main.json`；**r > R(t) 列必须留空** |
| 表7 | 参数与经验式汇总（附录2/3/4 + 对流系数口径） | Type 3 | 题目附录、`g_framing_convective_coefficients` |
| 表8 | 四问结果汇总（关键量 + 条件性与局限） | Type 3 | 四问 frozen_numbers |
| 表9 | 验证与稳健性证据汇总（解析误差/加密/守恒/独立实现/敏感性） | Type 3 | 四问 validation 与 robustness |

做表规则（来自 `tables/2020A_table_result_reflow`）：**一张表只讲一个结论**；必带单位、误差、约束满足、是否贴界、口径说明；booktabs 三线表；数值右对齐、单位入表头。

## 4. 取舍与不做的事

- 不把四张 Type 1 诊断图复制进 `paper/figures/`；其内容由 图2–图4 与附录图重新承载。
- 不做"多方法大比拼"式图：四问只有一条主方法线，基线的作用是交叉验证而非备选比较。
- 不新增任何未被冻结声明支撑的面板；每个面板可追溯到具体 `claim_id` 或已确认口径。
- 图注一律条件式，写入各自适用边界；不得由 AI 加强为无条件结论。

## 5. 状态

| 项 | 状态 |
|---|---|
| 规划 | **已完成并经建模者确认**（`g_figure_plan_scope`，消息 #35：①A ②A ③A） |
| 论文图（类型 3） | **已生成** 6 张，见 `paper/figures/fig01…fig06`（PNG + PDF，400 dpi） |
| 附录图（类型 4） | **已生成** 3 张，见 `paper/figures/figA1…figA3` |
| 渲染证据 | 9 个 `<name>.render.json` 全部 `status=PASS`；`scripts/figure_render_audit.py` 通过（当前无 paper section 引用，故 checked_figures 计 18 个文件） |
| 汇总表 | **已生成** `paper/tables/table7/8/9`（Markdown + CSV，逐格可溯源） |
| 图注 | 草拟完成（见 §1），**待建模者逐条审改**（③A） |
| 人工目视确认 | **待建模者**：渲染审计为**机械检查**（文本包围盒是否越界、文本两两是否重叠、面板是否为空、数据是否不透明、是否无网格），无法替代人眼对配色/可读性的判断 |

### 机械渲染审计的实测项（每张图均 PASS）

- `no_text_outside_saved_canvas`：所有标题/轴标签/图例/标注的包围盒都落在 tight bbox 内；
- `no_overlapping_text`：任意两处非刻度文本的包围盒交集不超过 1 px；
- `no_empty_panel`：每个面板都有数据图元；
- `data_opaque`：所有数据图元 alpha = 1.0；
- `no_grid`：无网格线。

### 生成脚本

- `code/figures/figure_style.py`（统一样式与渲染审计）
- `code/figures/make_paper_figures.py`（图 1–6）
- `code/figures/make_appendix_figures.py`（图 A1–A3）
- `code/figures/make_summary_tables.py`（表 7–9）

## 6. 上游绘图项目（nature-figure）使用情况自查

**结论：此前绘图只用了上游的一篇文档，未使用上游的图契约与校验器。**

| 上游文件 | 是否使用 | 说明 |
|---|---|---|
| `multipanel-evidence-architecture.md` | **部分使用** | 规划阶段读了前 70 行，采用“一图一主结论”“面板承担不同推断角色”“可删面板必须删”三条原则 |
| `figure-contract.md` | 未使用 | 未按该模板逐图填写 Core conclusion / archetype / evidence hierarchy / reviewer risk |
| `design-theory.md`、`api.md`、`qa-contract.md` | 未使用 | 未读 |
| `validate_figure.py` | **本次补跑** | 见下 |
| `audit_pdf_text.py` | **本次补跑** | 见下 |
| `audit_panel_alignment.py` | **未跑（遗留）** | 需要 backend-neutral panel-layout JSON，尚未构造 |

配色/版式/渲染规则实际取自**本仓库自写**的 `.agents/skills/math-figure-generator/references/` 下三份文档，
以及 `resource-library/figures/topjournal-style/README.md`（自写规范）。

### 补跑上游校验器后查出的真实缺陷（已修复）

- `audit_pdf_text.py` 发现 fig01 / fig03 / fig05 存在 **4.34–4.90 pt** 的低于 5 pt 文本；
  mathtext 上下标会缩到父字号的约 0.7 倍，而本仓库自写的渲染审计只检查包围盒越界、文本重叠、空面板、
  数据不透明度与网格，**不检查字号下限** —— 因此此前 9 张图全部报 PASS 却带着不可读的小字；
- 已抬高相关字号（`$T_\infty$` 刻度标签、`$5\times10^{-5}$`、`$10^{-8}$`、图1 边界条件标注），
  并补上 `svg.fonttype="none"`、`pdf.fonttype=42` 与 SVG 导出；
- 复测：**9 张图 PDF 全部通过 5 pt 下限**（fig01 最小值 5.04 pt），自写审计仍 5 项全过，论文重编译 13 页无错。

### 未采用的上游规则（与本赛制无关，记录为偏离）

1. `FONT-FAMILY` 要求无衬线白名单（Arial / Helvetica / Liberation Sans / `sans-serif`）；
   本仓库顶刊风格规范面向中文竞赛论文，明确要求宋体 + Times 类衬线。两者冲突，**本文采用衬线**并在此记录偏离；
2. TIFF 投稿栅格、600 dpi 默认、目标期刊宽度、SVG 必需 —— 属期刊投稿要求，非竞赛论文要求；
3. `validate_figure.py` 对生成器脚本报出的 `EDITABLE-TEXT` / `EXPORT-VECTOR` / `EXPORT-RASTER` 三项 FAIL，
   是按单文件扫描的范围假阳性：样式与导出集中在 `figure_style.py`，该文件上同样检查为 PASS，
   产物也在 `paper/figures/` 实际存在。

### 遗留未做

- `audit_panel_alignment.py`（上游对多面板图的强制渲染期对齐门）尚未运行；
  需先给出 backend-neutral 的 panel-layout JSON（每张多面板图的 axes 矩形与网格）。
  本仓库自写的 `no_text_outside_saved_canvas` / `no_overlapping_text` 只是它的弱替代。
