# 最终质量保证报告（QA）

> 执行者：`quality-assurance-auditor` ｜ 口径：submission ｜ 前置：一致性终审 PASSED、完整性终审 PASSED
> 采集时间：2026-09-11（结构性改稿后复跑）
> 证据：`scratch/g6_evidence.json`、`scratch/g6_collect.json`、`scripts/qa_report.py` 的结构化输出，
> 以及**直接抽样**的规范源文件（四问 `metrics/*.json`、`frozen_numbers.json`、`decisions.jsonl`、
> `paper/main.tex`、`paper/main.pdf`）。

## 总判定：**CONDITIONAL**

五个维度均通过抽样检查，机械与溯源层无阻塞；但**AI 使用声明缺失**（建模者明确指示暂不撰写），
按 QA 词表这属于"接受但带具名条件、须由建模者确认"，因此总判定为 `CONDITIONAL` 而非 `PASSED`。

## 分层状态（各层独立报告，不相互折算）

| 层 | 状态 | 依据 |
|---|---|---|
| 机械层 | `MECHANICAL_PASS` | `validate_repo` 退出码 0；四问 `validate_artifacts` PASS、`validate_decisions` PASS、12 份运行快照 PASS、`validate_independence` PASS；`check_frozen_freshness` PASS（53/0 stale）；`figure_render_audit` PASS（27/0 error）；LaTeX 0 错误、0 overfull |
| 语义层 | `SEMANTIC_PASS` | 一致性终审七类全过；完整性终审无 MISSING/INSUFFICIENT/STALE |
| 溯源层 | `SEMANTIC_PASS` | 53 条冻结声明全部经宏引用（warning = 0）；宏体数值逐条解析后与冻结值一致（不符项 = 0） |
| 人类判断层 | `HUMAN_JUDGMENT_PENDING` | 四问 26 条 + 全局 11 条判断均有 ledger 记录；**唯 AI 使用声明待建模者给出** |
| 门禁层 | `CONDITIONAL` | G1–G6 四问全部通过（`blockers = []`），但受上一行之条件约束 |

## 维度 1：工作流完整性

- G1→G6 逐问通过（`workflow_guard.py derive --profile submission`：四问均 `gate = G6`、`blockers = []`）；
- 全部人类判断可解析到决定 ID（方法选择 8、结果判定 5、稳定性判定 5、声明范围 4、包签核 4、全局口径 11）；
- 主方法/基线/条件备选：四问的回退项**均未被静默启用**，`fallback_trigger.observed = false`，
  证据落在各问 `verifier_validation.json`。

## 维度 2：证据完整性

- **未发现任何编造**：抽样核对 `drying_time_hours`、表内数值、误差指标，均可回溯到运行快照钉住的 metrics 文件；
  论文中的数值无一是手写的（表格由脚本生成，正文经宏注入）；
- 主要声明均指向冻结数字与稳健性证据：53 条声明与四问稳健性报告一一对应；
- 局限与不确定性可见：各问结果分析与论文段落均写明条件性（$h_m$、附录经验式、恒温段口径、端面忽略、判据尾部平坦）。
- **改动可追溯**：本轮为满足"附录代码做好注释"的要求，对五个建模源文件作了纯注释改动；
  该改动未以口头保证结案，而是在隔离副本中重跑全部六个引用脚本并逐字段比对（结论：全部相同），
  存档于 `scratch/comment_only_proof.json`。这是本轮唯一一次触及已冻结链路的改动，且已被证据封口。

## 维度 3：方法质量

- **基线可用**：四问的基线均能完成真任务（产出同构表与网格），且与主方法使用不同空间离散与时间推进，
  `validate_independence.py` 判定 `RUNTIME_INDEPENDENT`；
- 假设、单位、目标、约束与求解步骤自洽（见 `planning/symbol_table.md` 与 `planning/assumptions.json`）；
- 输出退化与失败触发已处理：四问 `output_degeneracy` 均为 PASS，回退触发条件均已记录且未触发。
- 推导深度：论文 §5.1–§5.4 逐式给出守恒律到控制方程、Robin 边界、特征时间、对偶控制体与两端点处理、
  Crank--Nicolson 与 Rannacher 启动、移动边界链式法则与表观对流项、守恒恒等式与不变量检验的构造，
  推导比重已按侧重计算类的获奖论文校准。

## 维度 4：论文质量

- 问题—方法—结果—结论对齐：`paper/sections/01`–`07` 的每一节都指向同一子问题的冻结声明；
- 行文顺序合规：符号说明（`04`）先于一切符号使用；问题重述阶段不含数据结论；
  定义在前、使用在后；
- 声明与所测证据成比例：论文未宣称任何未测试方法的优越性，也未把条件式结论写成无条件结论；
- **人类所有的物理含义与贡献表述**：问题一至问题三的物理含义与声明范围均转录自 ledger；
  问题四的主结论（收缩不可忽略）出自 `q4_claim_scope`；摘要与题目由建模者授权 AI 起草，
  属**待建模者审改定稿**的草稿。

## 维度 5：呈现

- 必交图表齐备并通过渲染检查：9 张 Type 2–4 图（6 张正文 + 3 张附录）各有渲染记录且 `status = PASS`；
  9 张表由 `metrics` 直接生成；
- 图型使用正确：Type 1 诊断图未进入论文目录；示意图仅用于机制与方法链；
- 排版：图名居中置于图下、表名居中置于表上，浮动体钉在首次提及处；正文黑色；坐标轴文字与刻度均为黑色；
  面板标号移出坐标区；条形图加斜纹区分；流程图不含公式且不再使用 Q 简写；
- 附录：代码另起一页，统一行号/边框/语法着色/自动折行，五份核心程序（含两份独立验证脚本）附有
  指向论文对应小节的中文注释；
- 参考文献真实、完整、引用一致：7 条，全部为实际使用来源，未编造；
- **AI 使用声明缺失**（本报告的唯一具名条件）：`scripts/latex_assembly.py` 报 `ai_declaration_missing = true`，
  生成的 `paper/main.tex` 未含声明段。

## 阻塞项与非阻塞项

| 项 | 类别 | 修复责任方 |
|---|---|---|
| AI 使用声明未提供（`paper/ai_use_disclosure.md` 或 `methods/Q1/q1_decisions.jsonl` 中的 `submission_authorization`） | **具名条件（阻塞 `PASSED`）** | 建模者 |
| 摘要与题目为 AI 起草、待审改定稿 | 非阻塞，需确认 | 建模者 |
| 论文 45 页（含 5 份代码全文附录） | 非阻塞 | 取决于赛制页数限制；如超限可只保留问题一、问题四的主方法清单 |
| 正文粗估约 14 页（不含代码附录） | 非阻塞 | 取决于赛制页数限制 |

## 未做与不做的声明

- 本报告未声明符合任何**会随时间变化**的赛制规则（如当年页数上限、AI 使用申报表格式），
  该类合规性须以当年官方文件为准；
- 本报告未在审计过程中修改任何工件（审计只报告、不修复）；
- 本轮为完成"附录代码注释与排版"而修改的源文件，其一致性影响已在维度 2 中以重跑比对的方式封口，
  但**该改动仍属于对已冻结链路代码的触碰**，故在此显式声明，供建模者复核。

## 结论

在补上 AI 使用声明（或建模者明确指示"本届不要求"）之后，本工作区即可进入最终装配与提交。
在此之前，`paper/main.tex` 可编译但不含声明段。
