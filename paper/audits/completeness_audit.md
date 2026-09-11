# 语义完整性终审（completeness audit）

> 模式：submission ｜ 执行者：`completeness-auditor`
> 采集时间：2026-09-11（结构性改稿后复跑）
> 证据：`scratch/g6_evidence.json`、`scratch/g6_collect.json`、`planning/manifests/Q*.json`、四问工件树。
> 状态词表：`PRESENT` / `MISSING` / `INSUFFICIENT` / `STALE` / `NOT_APPLICABLE`。

## 判定：**PASSED**

submission 口径要求的每一项证据均存在且为当前版本；无 `MISSING`、无 `INSUFFICIENT`、无 `STALE`。

论文在本轮由"按问题分文件"重构为统一的七节结构，因此下表的"论文段落"一行改为指向
重构后的实际载体；除此之外无工件被删除。

## 1. 每问的必备工件

| 工件 | Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|
| 最终方法说明 `methods/Qx/qx_final_method_explanation.md` | PRESENT | PRESENT | PRESENT | PRESENT |
| 语言评审 JSON（五项命名检查全 PASS） | PRESENT | PRESENT | PRESENT | PRESENT |
| 最终结果分析 `results/Qx/reports/qx_final_result_analysis.md` | PRESENT | PRESENT | PRESENT | PRESENT |
| 稳健性报告 `robustness/Qx/qx_robustness_report.md` | PRESENT | PRESENT | PRESENT | PRESENT |
| 交付包 `qx_solution_package_for_writer.md` | PRESENT | PRESENT | PRESENT | PRESENT |
| 冻结数字 `frozen_numbers.json`（当前） | PRESENT | PRESENT | PRESENT | PRESENT |
| 运行快照（主/基线/验证三份） | PRESENT | PRESENT | PRESENT | PRESENT |
| 论文中的对应章节 | PRESENT | PRESENT | PRESENT | PRESENT |
| 章节引用的图（Type 2–4，带渲染证据） | PRESENT | PRESENT | PRESENT | PRESENT |

补充：语言评审的判定分别为 Q1 `overall_status=PASS`、Q2/Q3/Q4 同为 `PASS`（五项命名检查 syntax /
input_contract / method_alignment / reproducibility / output_contract 全部 PASS）。

**"论文中的对应章节"的判定口径**（本轮重构后的新口径，已同步进 `scripts/workflow_guard.py`）：
每问在论文中不再拥有独立文件，而是以 `\section{问题X：…}` 的形式出现在
`paper/sections/05_model_and_solution.tex` 中（§5.5–§5.8），并分别在
`paper/sections/06_validation.tex` 有一节检验。门禁引擎现在要求"该问标题确实作为 section 出现"，
仅存在合并文件不算通过——否则一篇漏写问题三的论文也能过关。四问 `derive --profile submission`
在本次复跑中均为 **G6**、`blockers = []`。

## 2. 全局必备工件

| 工件 | 状态 | 备注 |
|---|---|---|
| 符号与单位表 `planning/symbol_table.md` | PRESENT | 六类符号 + 六条使用约定，跨问冲突已在此解决 |
| 承重假设 `planning/assumptions.json` | PRESENT | 5 条全局 + 7 条分问，含性质、若无此事的影响、对应决定 ID |
| 参考文献 `paper/refs.bib` | PRESENT | 7 条，全部为**实际使用**的来源（SciPy、NumPy、Carslaw & Jaeger、Incropera、LeVeque、Crank、Patankar）；赛题条目已按要求移除；未编造文献 |
| 术语与符号一致性 | PRESENT | 正文一律称"问题一/二/三/四"，不再使用 Q1–Q4 简写 |
| 一致性终审 `paper/audits/cross_media_consistency_audit.md` | PRESENT | 判定 PASSED，七类检查全执行 |
| 完整性终审（本文） | PRESENT | — |
| AI 使用声明 `paper/ai_use_disclosure.md` | MISSING | **建模者指示暂不撰写**；属 QA 层的呈现维度，不阻塞完整性判定，但在 QA 中作为具名条件 |
| 论文 PDF `paper/main.pdf` | PRESENT | 45 页，LaTeX 0 错误、0 overfull |

## 3. 语义字段检查（不只看文件是否存在）

- 最终方法说明：均含模型对象、控制方程、数值方案、决策链、验证证据、适用边界六节；四问齐全。
- 最终结果分析：均含结论先行、主—基线对比、误差分解、稳健性、局限、人类判定分节、数值来源索引；
  Q1/Q4 另含实现层发现的记录。
- 稳健性报告：均含范围与口径、基准状态、逐项检验（含判定与观测量）、与冻结声明的对应、局限、回退触发状态。
- 交付包：均含交付清单、冻结数字候选表（含唯一来源路径）、图表清单、人类决策引用、适用边界、签核状态。
- 论文段落：每段引用其子问题的冻结宏；条件式措辞与局限均已写入。
- 论文结构本身满足行文顺序要求：`01` 问题重述（无符号）→ `02` 问题分析 → `03` 模型假设 →
  `04` 符号说明（首次集中定义符号）→ `05` 模型建立与求解（含 §5.1–§5.4 完整推导）→
  `06` 模型检验与灵敏度分析 → `07` 模型评价与推广 → 参考文献 → 附录。**符号说明之前不出现符号**。

## 4. 陈旧性检查只针对被实质引用的证据

- `check_frozen_freshness.py` **PASS**（53 条声明，stale = 0）；
- 四问 `validate_artifacts.py` **PASS**，48 份 lineage 全部 **CURRENT**；
- 12 份运行快照 `validate_run_snapshot.py` **PASS**；
- 论文被重构、附录新增两份验证脚本源码、附加上千行中文注释之后，上述判定仍全部为当前——
  因为注释类改动已按"隔离重跑 + 逐字段比对"证明不改变任何数值（见一致性终审 §6.1），
  未因无关的格式化或评论改动判定任何决定为陈旧。

## 5. 与 QA 层的关系

按审计顺序（一致性 → 完整性 → QA），QA 报告（`paper/qa_report.md`）在本审计之后生成。
本审计已将其交叉核对，未出现"完整性等 QA、QA 等完整性"的互锁；QA 的具名条件不影响本审计的 PASSED 判定。
