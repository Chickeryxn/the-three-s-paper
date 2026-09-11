# 跨媒介一致性终审（cross-media consistency audit）

> 模式：`final`（submission 口径，全量四问）｜ 执行者：`consistency-auditor`
> 采集时间：2026-09-11（本次结构性改稿后的复跑）
> 证据：`scratch/g6_evidence.json`（由 `code/g6_evidence.py` 采集）、`scratch/g6_collect.json`、
> `paper/build_report.json`、`scripts/latex_assembly.py --check-only --strict`、
> `scripts/figure_render_audit.py`、`scripts/check_frozen_freshness.py`、
> `scripts/validate_artifacts.py`、`scripts/validate_decisions.py`、`scripts/validate_repo.py`。

## 判定：**PASSED**

七类检查全部执行，未发现分歧。以下逐类给出实测证据，不列空泛的通过项。

本次复跑的触发原因：论文由"按问题分文件"（`paper/sections/q1.tex`–`q4.tex`）重构为
"统一推导 + 分问求解"（`01`–`07`），并同步修改了图表排版与附录代码。这属于
`CANONICAL` 级改动（图路径、论文段落结构变化），故按终审口径全量重跑。

## 1. 数值声明与冻结值、单位一致

- `paper/main.tex` 中由 `scripts/latex_assembly.py` 注入的 **53 个宏定义**，其宏体逐条与
  `results/Q*/reports/frozen_numbers.json` 的 `value` 一致：**宏值不符项 = 0**。
- 冻结引用检查：**warning = 0**（既无"声明未被宏引用"，也无"原始值以裸数字出现"）。
- 单位随宏体一并注入（`kg/kg`、`h`、`s`、`cm`、`%`、`°C` 等），正文不再另写单位。
  宏体形如 `\newcommand{\qone...}{2.55\,kg/kg}`，单位经细空格 `\,` 与数值分隔。
- 量级小于 `1e-2` 或大于 `1e5` 的声明改以 `$6.18\times10^{-7}$` 的科学计数形式注入，
  不再出现"6.18e-07"这类把 `e` 当普通字母排版的写法。本次复核逐条解析宏体数值与冻结值比对，
  **53/53 全部一致**。
- `paper/tables/table1–table6*.tex` 由 `code/paper_tables.py` 从各问 `metrics/main.json` 直接生成，
  正文以 `\input` 引入；**六张必交表不存在手写数值**。其余三张汇总表（表 7–9）同样由
  `code/paper_tables_extra.py` 生成，其中表 9 的每一格都是冻结宏。

## 2. 公式、参数、方法角色与已批准代码/计划一致

- 各问 `run_summary.json` 的 `scheme` 字段与论文所述方法逐一对应：
  问题一「顶点有限体积 + 自适应 BDF（`solve_ivp`）」、问题二/三「顶点有限体积 + Crank--Nicolson（3 步启动）」、
  问题四「ξ 坐标顶点有限体积 + 表观对流 + Crank--Nicolson（3 步启动）」。
- 论文第 5 节 §5.1–§5.4 给出的推导（守恒律 → 控制方程、Robin 边界、特征时间、顶点有限体积的对偶控制体与
  两端点处理、Crank--Nicolson 与 Rannacher 启动、移动边界的链式法则与表观对流项 `xi*Rdot/R`、守恒恒等式、
  不变量检验的构造）与代码中的实现逐条对应；§5.3 的守恒恒等式与
  `code/Q4/q4_main.py` 中 `G(y)` 的定义式同形。
- 论文所述参数（$\rho$、$c_p$、$k$、$D$、$h$、$h_m$、判据 0.15）与 `planning/symbol_table.md`
  以及代码常量一致；附录 2/3/4 的三套经验式在表 7 中并列列出并标注适用问题。
- 符号说明已前移到正文之前（`04_symbols.tex`），且**符号说明之前不出现符号**：
  `01_problem_restatement.tex` 与 `02_problem_analysis.tex` 中不含任何数学符号定义。
- 角色分工与 `validate_independence.py` 的判定一致：四问的 `run_summary.json` 全部
  **PASS**（`RUNTIME_INDEPENDENT`），主/基线/验证三角色脚本互异、运行期引用不共享结果类文件。

## 3. 符号与单位与全局符号表一致

- 符号表 `planning/symbol_table.md` 覆盖几何、场变量、物性、离散量、判据与无量纲数六类，并含六条使用约定；
- 论文与交付物中的温度统一用 °C（仅附录经验式 $\exp(-3850/T)$ 内部为 K，已在符号表与正文标注）；
- 含水率统一为**干基** kg/kg；坐标一律区分物理 $r$ 与归一化 `xi = r/R(t)`；
- 长度单位：内部计算 SI（m），报告层按题目要求 cm；时间：交付物 s、表格 h。**未发现单位混用**。

## 4. 被引用的表、图、代码、数据文件均存在

- 章节中的 `\input{}` 与 `\includegraphics{}` 目标全部存在：**缺失项 = 0**。
- 9 张被引用图全部位于 `paper/figures/`，且**引用一律带显式扩展名 `.pdf`**——
  本轮曾出现 `fig05`/`fig06` 以无扩展名形式引用而被判定"ambiguous extensionless reference"，
  已修正并在本次复跑中确认 `missing_referenced_files = []`。
- 9 张表位于 `paper/tables/`，全部以 `\input` 引入；
- `figure_render_audit.py` 判定 **PASS**：`checked_figures = 27`（9 张图 × PNG/PDF/SVG 三种载体），
  每张图的渲染记录 `status = PASS` 且 `rendered_at` 非空，**errors = 0**。

## 5. 「为何选此方法」、结果/稳定性/声明范围均可解析到人类决定

| 判断类别 | 证据位置 | 记录数 |
|---|---|---|
| 方法选择 | `methods/Q*/q*_decisions.jsonl`（含 `q1_time_scheme_amendment`、`q1_method_role_swap`、`q2_presentation_method_amendment`、`q3_time_scheme_startup` 等修订） | 8 |
| 结果判定 | `q1_result_verdict`、`q1_result_verdict_post_swap`、`q2/q3/q4_result_verdict` | 5 |
| 稳定性判定 | `q1/q2/q4_stability_verdict`、`q3_stability_verdict`、`q3_robustness_supplement` | 5 |
| 声明范围 | `q1/q2/q3/q4_claim_scope` | 4 |
| 交付包签核 | `q1/q2/q3/q4_package_signoff` | 4 |
| 全局口径 | `planning/framing_decisions.jsonl`（11 条：3 根口径轴 + 7 条框架判断 + 图表规划范围） | 11 |

- 四本账本 `validate_decisions.py` 全部 **PASS**（Q1 8 条、Q2 6 条、Q3 7 条、Q4 5 条）；
  每条 `DECIDED` 记录均含 `source.user_answer` 与已核对至会话日志的 `user_message_id`。
- 论文中的条件式措辞（"在题目给定的 $h_m$ 与附录经验式下""恒温段环境为人为口径"等）与
  各问 `stability_verdict` 附加的措辞要求一致，**未发现被加强为无条件结论**。
- 摘要与标题由建模者明确授权 AI 起草（会话消息"2 你来写"），属**待建模者审改定稿的草稿**，
  不构成 AI 自行作出的物理判断或贡献声明。

## 6. 冻结与决定相对于被引证据未过期

- `check_frozen_freshness.py` → **PASS**：53 条声明无一 stale，源文件均未晚于 `frozen_at`；
- 四问 `validate_artifacts.py` → **PASS**，全部声明工件 lineage 为 **CURRENT**；
- 12 份运行快照（四问 × 主/基线/验证）`validate_run_snapshot.py` → **PASS**；
- 四问 `workflow_guard.py derive --profile submission` → **G6**，`blockers = []`；
- `scripts/validate_repo.py .` → **PASS**（退出码 0）；
- `paper/main.log` 记录：**0 个 LaTeX 错误、0 个 overfull hbox、45 页**。

### 6.1 本次"仅注释"改动的一致性处理（须记录在案）

附录代码清单一节要求"做好注释"，因此对 `code/Q1/q1_common.py`、`code/Q1/q1_main.py`、
`code/Q1/q1_verifier.py`、`code/Q4/q4_main.py`、`code/Q4/q4_verifier.py` 五个文件**只增加中文注释**。
按 `AGENTS.md` 的影响分类，注释属 `NONE` 级改动。为避免"我保证没改语义"这类无证据的声明，
本次不采用口头保证，而是把引用到这些文件的脚本在**隔离副本**中重跑并逐字段比对：

| 脚本 | 比对对象 | 结果 |
|---|---|---|
| `code/Q1/q1_main.py` | `metrics/main.json`、`main_validation.json` | 逐字段相同 |
| `code/Q1/q1_verifier.py` | `metrics/verifier.json`、`verifier_validation.json` | 逐字段相同 |
| `code/Q1/q1_robustness.py` | `robustness/Q1/q1_robustness_summary.json` | 逐字段相同 |
| `code/Q4/q4_main.py` | `metrics/main.json`、`main_validation.json` | 逐字段相同 |
| `code/Q4/q4_verifier.py` | `metrics/verifier.json`、`verifier_validation.json` | 逐字段相同 |
| `code/Q4/q4_robustness.py` | `robustness/Q4/q4_robustness_summary.json` | 逐字段相同 |

（比对忽略 `elapsed_s`/`generated_at` 等纯计时字段；复现脚本见 `scratch/comment_only_recheck.py`、
`scratch/verifier_recheck.py`、`scratch/robustness_recheck.py`，结论存档于
`scratch/comment_only_proof.json`。）

据此，四个把这些源文件记入 `created_from` 的 lineage 文件（`code/Q1/reviews/…`、
`code/Q4/reviews/…`、`robustness/Q1/…`、`robustness/Q4/…`）只刷新了记录的 sha256，
**未重新派生任何工件、未改动任何数值**；刷新前后 `validate_artifacts.py` 由 FAIL 转为 PASS。

## 7. 论文引用的图带渲染证据

- 见第 4 类；`figure_render_audit.py` 的 `errors` 为空数组，`checked_figures = 27`、`referenced = 9`；
- 每张图的渲染记录内含**实测**检查项（文本是否越界、非刻度文本是否重叠、面板是否为空、
  数据是否不透明、是否无网格、字号是否低于可读下限），9 张图全部通过；
- 本轮排版修订（坐标轴文字改黑、面板标号移出坐标区、删除与图例冲突的读数框、条形图加斜纹、
  物理符号加粗、流程图去除公式）后全部重新渲染，渲染记录均为最新；
- **图 1（fig06）与图 2（fig05）的版面重做**（2026-09-11）：两张图原先都是"宽而扁"的长条
  （9.4×3.6 in 与 8.2×2.7 in），缩入正文后图 1 高度仅约 6 cm、字号实际落到 4 pt 上下，
  图 2 的四个子图各只有约 1.7 in 宽，刻度与注记不可读。现分别改为 7.6×5.0 in（流程图，单列）
  与 7.4×5.3 in（验证证据，2×2 重新排布），字号提到 8.4–9.2 pt。两图的数据、声明的冻结宏
  与图注所指结论均未改变，只改版面；
- 图 1 另在生成函数内加入**实测断言**：逐框量测文字包围盒与所属方框的余量，最坏越界必须 ≤ 0 pt，
  结论写入 `fig06_method_and_roles.pdf.render.json` 的 procedural checks
  （"text fits inside every box (worst overflow 0.00 pt)"）。这是对原审计盲区的一次补强——
  `figure_style.audit()` 只检查 text-vs-text 重叠与画布裁剪，**不检查文字是否溢出所属方框**，
  而流程图恰恰只会在这一项上出错。
- Type 1 诊断图（`results/Q*/experiments/round1/figures/*.png`）**未进入 `paper/figures/`**，
  论文中不出现诊断图。

## 未发现分歧

本次未产生需要修复的 divergence。若后续修改任何被引用的源工件（`metrics/*.json`、
`frozen_numbers.json`、`paper/figures/*`、`paper/sections/*`），本审计须按 `scoped` 模式重跑对应问。
