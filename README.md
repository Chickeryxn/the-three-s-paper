# the-three-s-paper

2026 年高教社杯全国大学生数学建模竞赛 **A 题 药材的烘干问题** 的论文、**生成论文 PDF 的完整工具链**，
以及论文中每一个数字的溯源证据。

本仓库的核心约定是：**论文 PDF 不是手写出来的，是生成出来的**。
正文数值由冻结数字经脚本注入为 LaTeX 宏，表格由指标文件生成，图形由绘图脚本重绘。
因此任何一处改动都能追溯到源头，多人协作时不会出现"谁手改了哪个数字"。

---

## 目录

- [1. 快速开始](#1-快速开始)
- [2. PDF 生成链：四个阶段](#2-pdf-生成链四个阶段)
- [3. 编译环境与依赖](#3-编译环境与依赖)
- [4. 排版配置逐条说明](#4-排版配置逐条说明)
- [5. 数值注入配置](#5-数值注入配置)
- [6. 图形生成配置](#6-图形生成配置)
- [7. 表格生成配置](#7-表格生成配置)
- [8. 构建步骤与预期输出](#8-构建步骤与预期输出)
- [9. 已知坑（本项目实际踩过的）](#9-已知坑本项目实际踩过的)
- [10. 提交前自检清单](#10-提交前自检清单)
- [11. 协作规则](#11-协作规则)
- [12. 生成物对照表](#12-生成物对照表)
- [13. 目录结构与数据说明](#13-目录结构与数据说明)

---

## 1. 快速开始

### 1.1 克隆后先确认能编译

```bash
git clone https://github.com/Chickeryxn/the-three-s-paper.git
cd the-three-s-paper
```

然后（Windows PowerShell）：

```powershell
.\build.ps1
```

macOS / Linux：

```sh
sh build.sh
```

预期看到：

```
[1/4] 跳过表格与图形（需要时用 -Full）
[2/4] 组装 paper/main.tex ...
[3/4] 编译两遍 ...
[4/4] 检查日志 ...

  页数       : 45
  LaTeX 错误 : 0
  overfull   : 0

  完成 -> paper/main.pdf
```

### 1.2 日常流程：改内容 → 出 PDF → 推送

只有三步。**平时只动 `paper/sections/*.tex`（文字）和 `paper/main_template.tex`（版面）**：

```powershell
# ① 改内容
#    paper/sections/01…07*.tex    ← 正文文字
#    paper/main_template.tex      ← 版面、宏包、样式

# ② 生成 PDF
.\build.ps1

# ③ 提交并推送（先构建，编译有错就不提交）
.\publish.ps1 -Message '改写第 5.2 节的推导'
```

macOS / Linux 对应 `sh build.sh` 与 `sh publish.sh '提交信息'`。

`publish.ps1` 的行为是：**先构建 → 构建不通过就中止 → 通过才 commit + push**。
这样不会把无法编译的中间状态推给协作者。提交信息省略时自动生成带时间戳的一条。

### 1.3 你改了什么 → 该跑什么

| 你改动的地方 | 命令 | 大约耗时 |
|---|---|---|
| `paper/sections/*.tex`、`paper/main_template.tex`（正文与版面） | `.\build.ps1` | 约 1 分钟 |
| `code/figures/*.py`（绘图脚本） | `.\build.ps1 -Full` | 约 2–5 分钟 |
| `code/paper_tables*.py`（表格生成脚本） | `.\build.ps1 -Full` | 约 2–5 分钟 |
| `code/Q*/q*_main.py` 等模型代码、`results/` 下的数值 | 先重跑模型并重新冻结，再 `.\build.ps1 -Full`，见 §11 | 数分钟起 |

`-Full` 会读 `results/Q*/…/result1|3|4.xlsx` 作为绘图输入；这三个文件（共 0.9 MB）在仓库里，
所以克隆后直接可用。脚本在缺失时会明确报出缺哪个文件并中止，不会跑到一半才崩。
（问题二的 `result2.xlsx` 约 28 MB，没有纳入版本库，但论文管线并不读它。）

**只改文字就用普通 `build`。** 加 `-Full` 会把 `paper/tables/table1…9*.tex` 与 `paper/figures/*` 全部重新生成，
没必要就别开——它会重画所有图并刷新渲染记录，产生大量无意义的 diff。

### 1.4 两个脚本各做了什么

`build.ps1` / `build.sh` 依次执行六件事：

1. 检查 `python` 与 `xelatex` 是否在 PATH 中，缺失则给出明确提示；
2. 检查 `paper/main.pdf` 是否被 PDF 阅读器占用——占用时直接提示"请关闭后重试"，
   而不是让 `dvipdfmx` 抛一句难懂的 `Unable to open`（见 §9.8）；
3. `-Full` 时先重新生成表格与图形；
4. `python scripts/latex_assembly.py . --template paper/main_template.tex` 组装 `main.tex`；
5. 编译两遍；
6. 从 `paper/main.log` 读出页数 / 错误数 / overfull 并打印；**有编译错误则退出码为 1**。

> 第 6 步的页数解析有个坑：TeX 会把长路径的日志行折行，甚至把 `(45` 拆成 `(4` + 换行 + `5`。
> 所以脚本先删掉日志里的全部空白再匹配，直接对原日志做行匹配会静默返回空值。

### 1.5 重跑生成脚本后，git 为什么会显示一堆改动

跑完 `-Full` 后 `git status` 通常会出现几十个改动，**其中大部分是噪声，属正常现象**：

| 现象 | 原因 | 要不要提交 |
|---|---|---|
| `paper/figures/*.pdf` 显示为已修改，且字节数完全相同 | Matplotlib 会在 PDF 里写入生成时间戳 | 可不提交；内容视觉上一致 |
| `paper/figures/*.render.json` 的 `rendered_at` 变了 | 渲染自检记录的时间戳 | 同上 |
| `paper/main.pdf` 字节数小幅变化 | 编译时间戳 | 同上 |
| 大量文本文件显示为已修改，但 `git diff` 看不出内容差异 | Windows 上 `core.autocrlf=true` 的行尾差异 | 会被 `git add` 自动消解，不产生真实提交 |

`.gitattributes` 已设置 `* text=auto eol=lf`，把最后一类噪声压到最低。
判断到底有没有真实改动，用：

```bash
git diff --ignore-cr-at-eol --stat
```

### 1.6 两条必须知道的约定

1. **`main.tex` 是生成物**，由模板 + 各节 + 冻结数字拼出来。直接改它，下次生成就丢。
2. **路径一律相对仓库根目录**（`\input{paper/sections/…}`、`\lstinputlisting{code/Q1/…}`、
   `\graphicspath{{paper/figures/}}`），所以必须从根目录编译；
   把 `main.tex` 单独拷到别处会立刻大量报 File not found。

## 2. PDF 生成链：四个阶段

```
  ① 数值                     ② 生成中间产物                    ③ 组装                ④ 编译

  code/Q*/q*_main.py   ──→  results/Q*/…/metrics/*.json  ──┐
  code/Q*/q*_robustness.py ─→ robustness/Q*/*.json       ──┤
                                                            ├─→ code/paper_tables*.py ──→ paper/tables/*.tex ──┐
  code/freeze_*.py     ──→  results/Q*/reports/           ──┤                                                   │
                              frozen_numbers.json ─────────┘                                                   │
                                    │                                                                         │
                                    └─→ scripts/latex_assembly.py（注入 53 个宏）─→ paper/main.tex ───────────┼─→ xelatex ×2 ─→ paper/main.pdf
                                                                                                              │
  workspace/data_clean/ + metrics ──→ code/figures/make_*.py ──→ paper/figures/*.pdf ─────────────────────────┘
```

| 阶段 | 命令 | 产物 |
|---|---|---|
| ① 跑模型 | `python code/Q2/q2_main.py` | `results/Q2/…/metrics/main.json`、`result2.xlsx` |
| ② 冻结数字 | `python code/freeze_q1q3.py` | `results/Q*/reports/frozen_numbers.json` |
| ② 生成表格 | `python code/paper_tables.py`、`paper_tables_extra.py` | `paper/tables/table1…9*.tex` |
| ② 生成图形 | `python code/figures/make_paper_figures.py` | `paper/figures/*.pdf|png|svg` + `*.render.json` |
| ③ 组装 | `python scripts/latex_assembly.py . --template paper/main_template.tex` | `paper/main.tex` |
| ④ 编译 | `xelatex … ×2` | `paper/main.pdf` |

**日常只改第 ③ 阶段的输入**：`paper/sections/*.tex`（文字）与 `paper/main_template.tex`（版面）。
第 ② 阶段的产物一律不要手改。

## 3. 编译环境与依赖

### 3.1 本项目实测通过的版本

| 组件 | 版本 |
|---|---|
| 引擎 | MiKTeX-XeTeX 4.18（MiKTeX 26.5） |
| 语言/字体 | Python 3.14.2；SimSun、SimHei、Times New Roman |
| 计算 | NumPy 2.5.1、SciPy 1.18.0 |
| 绘图 | Matplotlib 3.11.1 |
| 交付表 | openpyxl 3.1.5 |

### 3.2 为什么必须用 XeLaTeX

文档类是 `ctexart`，需要**直接调用系统字体**（宋体 SimSun、黑体 SimHei）。
pdfLaTeX 走的是 Type1/OT1 编码，中文要走 CJK 宏包或字体映射，本模板没有适配，会直接失败。

### 3.3 LaTeX 宏包清单

全部由 `paper/main_template.tex` 的前言区加载，共 **10 条 `\usepackage`（17 个宏包）**：

| 宏包 | 用途 |
|---|---|
| `ctexart`（文档类） | 中文排版、宋体/黑体切换、章节中文化 |
| `geometry` | 页边距 `margin=2.5cm` |
| `amsmath, amssymb, bm` | 公式环境、数学符号、粗体数学（物理量符号加粗） |
| `graphicx` | 插图，配合 `\graphicspath` |
| `booktabs, longtable, tabularx, multirow, array` | 三线表、跨页表、自动换行宽表 |
| `float` | 提供 `[H]` 浮动体位置（把图表钉在首次提及处） |
| `caption, subcaption` | 图注/表注字体与位置 |
| `enumitem` | 列表间距控制 |
| `xcolor` | 代码清单的灰阶着色 |
| `listings` | 附录 Python 代码清单 |
| `hyperref`（`hidelinks`） | 目录/交叉引用跳转，**关闭彩色边框** |

建议用 TeX Live 或 MiKTeX 的**完整安装**；最小安装会缺 `ctex` 或中文字体配置。

### 3.4 平台差异

- **Windows**：宋体/黑体随系统自带，开箱即用。
- **macOS / Linux**：系统没有 SimSun/SimHei，需要自行安装（或改 `ctexset` 里的字体名）。
  编译本身不会报错，但中文会静默回退到其他字体，版式与成稿不一致——**这点很容易漏检**。
- 换行符由 `.gitattributes` 统一（`* text=auto`，二进制文件显式标注），
  避免 Windows/macOS 协作时整文件显示为已修改。

## 4. 排版配置逐条说明

全部集中在 `paper/main_template.tex`。以下逐条列出**实际生效的配置**与**为什么这么设**。

### 4.1 页面与正文

| 配置 | 值 | 理由 |
|---|---|---|
| 文档类 | `\documentclass[12pt,a4paper]{ctexart}` | 正文 12 pt；A4 |
| 页边距 | `margin=2.5cm` | 国赛常用版心 |
| 行距 | `\linespread{1.4}\selectfont` | 目标是**行距 20 pt**；对标 2020A 获奖论文 A147 实测值（正文 12 pt 宋体、行距 20 pt） |
| 正文颜色 | 全黑 | 超链接用 `hidelinks` 关闭彩色边框；坐标轴文字、刻度数字同样是黑色 |

### 4.2 标题层级

```latex
\ctexset{
  section/format=\large\bfseries\heiti,
  section/number=\chinese{section},        % 一、二、三……
  subsection/format=\normalsize\bfseries\heiti,
  subsubsection/format=\normalsize\bfseries\heiti,
}
```

- 一级标题用**中文数字**（一、二、三），与获奖论文的序号形式一致，不用阿拉伯数字。
- 各级标题一律**黑体**；一级 `\large`，二/三级 `\normalsize`。
- 二级标题编号为 `2.1`、`2.2` 这种阿拉伯形式，正文引用时以它为准。

### 4.3 图注与表注

```latex
\captionsetup{font={small},labelsep=quad,justification=centering}
\captionsetup[table]{position=below}
```

- **图名在图下方、表名在表上方**，两者都**居中**（`justification=centering`）。
- 编号与题注之间用等宽空格分隔（`labelsep=quad`）。
- 字号 `small`，比正文小一号。

### 4.4 浮动体位置

正文里图表一律写作 `\begin{figure}[H]` / `\begin{table}[H]`（`float` 宏包的强制定位），
即**钉在首次提及处**，不参与 LaTeX 的自动浮动调度。

代价是可能出现单页留白；换来的是"图必须紧跟提及它的那一段"这一排版要求能被稳定满足。

### 4.5 代码清单（附录）

```latex
\lstdefinestyle{pycode}{ language=Python, basicstyle=\ttfamily\scriptsize, ... }
\lstset{style=pycode}
```

要点：
- `basicstyle=\ttfamily\scriptsize` —— 字号必须用**带名字的字号命令**（如 `\scriptsize`），
  **不要**写成 `\fontsize{7.8}{9.6}\selectfont`，后者会让 listings 的间距计算崩掉（见 §9.4）。
- `postbreak=\mbox{$\hookrightarrow$\space}` —— 折行的续行标记。
  **不能用 `\textcolor`**，同样会破坏间距计算（见 §9.3）。
- `frame=single` + `numbers=left` + `xleftmargin=20pt` —— 整幅细框、左侧行号、正文缩进对齐。
- `breaklines=true` + `breakatwhitespace=false` —— 长行自动折行。
- 语法着色走**灰阶**（关键字黑体、注释 55% 灰、字符串 70% 灰），不引入彩色。

### 4.6 图片搜索路径

```latex
\graphicspath{{paper/figures/}}
```

正文里因此只写文件名。**但一律带上显式扩展名**，写成
`\includegraphics[width=0.97\textwidth]{fig06_method_and_roles.pdf}`，
不要写成不带扩展名的形式（见 §9.7）。

### 4.7 参考文献

用 `thebibliography` 环境，条目由 `scripts/latex_assembly.py` 从 `paper/refs.bib` 解析后**内联**进 `main.tex`
（不依赖 BibTeX/biber 外部工具链，减少环境差异）。当前 7 条，全部是论文实际引用的来源。

## 5. 数值注入配置

### 5.1 占位符

`paper/main_template.tex` 里有 4 个占位符，由 `latex_assembly.py` 替换：

| 占位符 | 替换内容 |
|---|---|
| `__FROZEN_MACROS__` | 53 条 `\newcommand`，来自 `results/Q*/reports/frozen_numbers.json` |
| `__INPUTS__` | 各节的 `\input{}` 列表 |
| `__REFERENCES__` | 由 `paper/refs.bib` 生成的 `\bibitem` |
| `__AI_DECLARATION__` | AI 使用声明（当前未提供，为空） |

`render_main()` 在替换前会先确认模板里**这 4 个注入点一个都不少**；缺任何一个就直接抛 `ValueError`
并拒绝组装——宁可报错，也不生成一份声明段被悄悄丢掉的论文。
（AI 使用声明当前为空，属预期：注入点存在、内容为空字符串。）

### 5.2 宏命名规则

claim id → 宏名由 `sanitize_macro_name()` 转换，规则是**把数字写成英文单词**：

```
q1_T_center_1800s        →  \qoneTcenteroneeightzerozeros
q4_R_at_drying_end_cm    →  \qfourRatdryingendcm
```

**为什么不是直接把数字删掉或加前缀**：TeX 的控制字（control word）只接受字母，
数字的 catcode 是 12。若写成 `\q1Tcenter`，TeX 会解析成"控制字 `\q` + 文本 `1Tcenter`"，
于是**每一条 `\newcommand` 都失效**，而 XeLaTeX **不会报错**——正文里就会出现一堆乱码般的文字。
把数字拼成单词后，宏名恒为纯字母，问题根除。

两条 claim id 若折叠成同一个宏名（`q1_avg` 与 `q1avg` 都会变成 `qoneavg`），
后者会自动加 8 位 sha1 后缀，而不是静默产生重复定义。

### 5.3 数字格式

`latex_number()` 决定数值怎么排：

| 量级 | 输出 | 例 |
|---|---|---|
| `0` | `0` | |
| `1e-2 ≤ \|v\| < 1e5` | 普通十进制 | `33.5753`、`0.15`、`52.6361` |
| `\|v\| < 1e-2` 或 `\|v\| ≥ 1e5` | 显式幂次 | `$6.18\times10^{-7}$`、`$2.5\times10^{5}$` |

**为什么要这样**：`6.18e-07` 这种写法在排版上是错的——`e` 会被当作普通字母排出来，
评委看到的是"6.18e-07"而不是科学计数法。所以小量级一律转成 `$a\times10^{b}$`。
普通十进制用 `repr()` 而非 `%f`，保证能**逐位还原冻结值**（冻结值本身已是 4 位小数）。

### 5.4 单位

单位写在**宏体内部**，用细空格 `\,` 与数值分隔：

```latex
\newcommand{\qoneCcenteroneeightzerozeros}{2.55\,kg/kg}
```

因此正文里只写 `\qoneCcenteroneeightzerozeros`，**不再另写单位**——避免出现"数值来自冻结、单位手写"的脱节。

### 5.5 引用完整性检查

`build_report()` 会产出 `paper/build_report.json`，其中：

- `frozen_reference_warnings` —— 既报告"声明未被任何宏引用"，也报告"该数值以裸数字出现在正文"。**当前为 0**。
- `bare_number_scan` —— 扫描正文里的裸数字（章节号、年份、单位换算等属于正常出现），作为人工复核的线索。

## 6. 图形生成配置

### 6.1 统一视觉系统

集中在 `code/figures/figure_style.py`，所有图共用：

| 配置 | 值 | 理由 |
|---|---|---|
| 主方法色 | `#1A6FC4` | 全篇一致，读者凭颜色即可认出主方法 |
| 可用基线色 | `#767676` 灰 | 与主方法形成主次关系 |
| 判据线 | 黑色虚线 | 与数据序列区分 |
| 数据透明度 | `alpha=1.0` | 不透明，避免打印后发灰 |
| 网格 | 关闭 | 去装饰 |
| 背景 | 白色 | |
| 中文字体 | SimSun（`font.serif`） | 与正文一致；数学用 STIX |
| 图例 | 黑边、不透明、无花哨圆角 | |
| 线宽 | 1.4 pt，轴 0.8 pt | |

### 6.2 输出产物

`finish()` 每张图输出**三个载体 + 两份渲染记录**：

```
paper/figures/<name>.pdf           ← LaTeX 用这个（矢量）
paper/figures/<name>.png           ← 预览用，400 dpi
paper/figures/<name>.svg           ← 备用（.gitignore 已排除，约 40 MB）
paper/figures/<name>.render.json          ← 渲染自检记录
paper/figures/<name>.pdf.render.json      ← 同上，文件名与正文引用的完全一致
```

**为什么要写两份 render.json**：正文里引用的是 `figxx.pdf`，而渲染审计脚本按字面名字找证据文件；
只写一份会导致审计报"missing render evidence"。

### 6.3 渲染自检（5 项，实测而非声明）

`audit(fig)` 在**已绘制完成的画布**上量测，不是检查代码：

| 检查项 | 判据 |
|---|---|
| `no_text_outside_saved_canvas` | 每个文本包围盒都落在 `bbox_inches="tight"` 的实际输出范围内 |
| `no_overlapping_text` | 注解/标题/轴标签/图例之间无重叠（刻度标签由 matplotlib 排布，排除在外以免误报） |
| `no_empty_panel` | 每个可见子图都有数据（线、矩形或散点） |
| `data_opaque` | 所有数据元素 `alpha ≥ 0.999` |
| `no_grid` | 无网格线 |

### 6.4 字号下限与"框内文字"约束

- **字号下限**：mathtext 的下标会缩到约 0.7 倍，所以 `fontsize` 设 8 pt 时，实际可能出现 5 pt 以下的上/下标。
  全篇图内文字在 PDF 里实测**不低于 5.04 pt**。加图时请勿低于此线。
- **示意图的文字必须落在自己的框内**：`audit()` 只查"文字与文字重叠"，**不查"文字溢出所属方框"**。
  流程图 `fig06` 因此在生成函数里内置了一条实测断言——逐框量测文字包围盒与矩形的四边余量，
  最坏越界必须 ≤ 0 pt，结论写进 `fig06_method_and_roles.pdf.render.json` 的 procedural checks：
  `"text fits inside every box (worst overflow 0.00 pt)"`。
- **宽高比决定可读性**：图在正文里会被缩放到 `\textwidth` 的某个比例。
  原 `fig06` 是 9.4×3.6 in 的 2.6:1 长条，缩入正文后高度只剩约 6 cm、6.4 pt 的字实际落到 4 pt 上下。
  现在内容密集的图一律控制在 **1.4:1 ~ 1.5:1**。

## 7. 表格生成配置

| 脚本 | 产物 | 数据来源 |
|---|---|---|
| `code/paper_tables.py` | `table1…table6*.tex`（题目要求的必交表） | 各问 `metrics/main.json` |
| `code/paper_tables_extra.py` | `table7_parameters.tex`、`table8_results.tex`、`table9_verification.tex` | `metrics/*.json` + `robustness/*.json` |
| `code/figures/make_summary_tables.py` | 汇总表的 Markdown/CSV 版本（便于核对，不进论文） | 同上 |

两条排版约定：

1. **必交表不写手数**：`table1…6` 的每一格都是从 `metrics` 直接格式化的。
2. **宽表用 `tabularx`**：表 8/9 之前用固定列宽的 `tabular`，表头过宽导致 40.83 pt 的 overfull；
   改成 `\begin{tabularx}{\textwidth}{l *{5}{>{\centering\arraybackslash}X}}` 后表头自动换行，overfull 归零。
   同时把 `\begin{table}[htbp]` 统一改成 `[H]`，与图一起钉在首次提及处。

## 8. 构建步骤与预期输出

```bash
# 1) 组装 main.tex（把模板、各节、冻结宏、参考文献拼起来）
python scripts/latex_assembly.py . --template paper/main_template.tex

# 2) 编译两遍
xelatex -interaction=nonstopmode -output-directory=paper paper/main.tex
xelatex -interaction=nonstopmode -output-directory=paper paper/main.tex
```

**为什么必须两遍**：第一遍写 `.aux`，此时交叉引用（`\ref`、目录、页码）尚未解析，
页面长度会变化；第二遍读入 `.aux` 后才稳定。
判断成稿务必以**第二遍**的 `paper/main.log` 为准。

**预期**：

| 指标 | 值 | 怎么查 |
|---|---|---|
| 页数 | 45 | `grep "Output written" paper/main.log` |
| 错误 | 0 | `grep -c "^! " paper/main.log` |
| overfull hbox | 0 | `grep -c "Overfull" paper/main.log` |
| 体积 | ≈3.33 MB | |

> 第一遍常会报 1 个 overfull，第二遍为 0，属正常现象（交叉引用未解析导致版面长度不同）。

## 9. 已知坑（本项目实际踩过的）

以下每一条都是真实发生过、且**第一眼看不出来**的问题。改论文时请留意。

### 9.1 `\\命令` 双重反斜杠：XeLaTeX 不报错，但正文出现字面量

批量脚本写文件时若不慎把 `\subsection` 写成 `\\subsection`，
**XeLaTeX 不会报错**——它把 `\\` 当成换行、把 `subsection` 当普通文字排出来。
曾经出现过渲染出的 PDF 里赫然印着 `subsection`×4、`textbf`×13、`**`×14，而日志显示"0 errors"。

**教训**："0 errors"不等于正确。改完必须抽查渲染页，或搜一遍正文里的可疑字面量。

### 9.2 Python 字符串里的 `\t`

`latex_number()` 返回的字符串含 `\times`。若写在不加转义的普通字符串里，
`"$6.18\times10^{-7}$"` 中的 `\t` 会被解释成**制表符**，正文里就印出 `1.15	imes10^{-6}` 这样的字面量。
**写法**：Python 字面量里用 `"\\times"`，或用原始字符串。

### 9.3 `listings` 的 `postbreak` 不能用 `\textcolor`

`postbreak=\mbox{\textcolor{gray}{$\hookrightarrow$}\space}` 会让 listings 的间距计算崩溃，
每次编译报 **165 个错误**（72 个 `Missing number, treated as zero`、72 个 `Illegal unit of measure`、21 个 `Improper 'at' size`）。
改用无着色的 `postbreak=\mbox{$\hookrightarrow$\space}` 即恢复正常。

### 9.4 `listings` 的 `basicstyle` 不要用 `\fontsize{}{}\selectfont`

同样触发上面那组错误。字号请用 `\scriptsize`、`\footnotesize` 这类**带名字**的命令。

### 9.5 宽表：`tabular` → `tabularx`

见表 8/9 的处理（§7）。判据是日志里的 `Overfull \hbox (Npt too wide)`，
并且日志会指明**是哪个文件、哪几行**，定位很快。

### 9.6 图"宽而扁"导致缩小后不可读

横向 1×4 排布的四个子图，缩入 `\textwidth` 后每个子图只有约 1.7 in 宽，刻度挤成一团。
改成 2×2 后子图宽度约增至 1.9 倍。**排版前先算一下缩放比**：
正文宽度 ≈16 cm，图宽 8 in ≈ 20.3 cm，缩放比 0.79，图上 9 pt 的字最终只有约 7.1 pt。

### 9.7 `\includegraphics` 不写扩展名

写成 `{fig05_numerical_verification}` 会同时存在 `.pdf/.png/.svg` 三个同名文件，
导致渲染审计报 `ambiguous extensionless reference` 且判 FAIL。**一律写 `.pdf`。**

### 9.8 Windows 上 PDF 阅读器占用输出文件

编译时报：

```
dvipdfmx:fatal: Unable to open "…\paper\main.pdf".
No output PDF file written.
```

原因是用 WPS / Adobe 等阅读器打开了 `paper/main.pdf`，文件被加写锁。
**编译前先关掉 PDF 阅读器。**（本项目的 `main.pdf` 反复被占用过，一度以为 LaTeX 坏了。）

### 9.9 宏名含数字

见 §5.2。这类问题的特征是"编译通过、正文却出现成片的奇怪文字"。

## 10. 提交前自检清单

```bash
# 1) 重新生成 main.tex，确认与 sections/ 一致
python scripts/latex_assembly.py . --template paper/main_template.tex

# 2) 编译两遍，看第二遍的日志
xelatex -interaction=nonstopmode -output-directory=paper paper/main.tex
xelatex -interaction=nonstopmode -output-directory=paper paper/main.tex

# 3) 三项硬指标
grep -c "^! " paper/main.log                    # 期望 0
grep -c "Overfull" paper/main.log               # 期望 0
grep "Output written" paper/main.log            # 期望 45 pages

# 4) 冻结引用完整性（期望 frozen_reference_warnings 为 0）
python scripts/latex_assembly.py . --template paper/main_template.tex --check-only
```

此外请**抽查 2~3 页渲染图**，确认没有 §9.1 那类字面量残留。

## 11. 协作规则

**1. 不要手写数字。** 正文里的每一个数值都是 LaTeX 宏，由 `scripts/latex_assembly.py`
从 `results/Q*/reports/frozen_numbers.json` 注入；表格由 `code/paper_tables*.py` 从 `metrics/*.json` 生成。
直接改 `main.tex` 或 `paper/tables/*.tex` 里的数字，下一次生成就会被覆盖。

**2. 要改数值，改源头再重新生成。**

```bash
python code/Q2/q2_main.py            # 重跑模型
python code/freeze_q1q3.py           # 重新冻结数字
python scripts/latex_assembly.py . --template paper/main_template.tex
python code/paper_tables.py          # 重新生成表格
```

**3. 改图要改脚本，不要改产物。** `paper/figures/*.pdf` 由 `code/figures/make_*.py` 生成，
每张图带一份 `*.render.json` 自检记录；直接替换 PDF 会让记录与图对不上。

### 合并时怎么减少冲突

- `paper/main.tex`、`paper/tables/*.tex`、`paper/main.pdf` 都是**生成物**，
  冲突时不要手工合并——取任意一方，在本机重新生成即可。
- 真正的编辑冲突只会出现在 `paper/sections/*.tex` 与 `main_template.tex`，正常合并。
- 提交前跑一遍完整生成链，确认 `main.tex` 与 `sections/` 一致。

## 12. 生成物对照表

| 文件 | 源头 | 重新生成 |
|---|---|---|
| `paper/main.tex` | `main_template.tex` + `sections/` + `frozen_numbers.json` | `python scripts/latex_assembly.py . --template paper/main_template.tex` |
| `paper/tables/table1…6` | `results/Q*/…/metrics/main.json` | `python code/paper_tables.py` |
| `paper/tables/table7…9` | `metrics/*.json` + `robustness/*.json` | `python code/paper_tables_extra.py` |
| `paper/figures/*` | `code/figures/make_*.py` | `python code/figures/make_paper_figures.py` |
| `results/Q*/reports/frozen_numbers.json` | `code/freeze_*.py` | 见上 |
| `paper/main.pdf` | 以上全部 | 编译两遍 |
| `paper/build_report.json` | `latex_assembly.py --check-only` | 同上 |

**平时只改 `paper/sections/*.tex` 与 `paper/main_template.tex`。**

## 13. 目录结构与数据说明

```
paper/
  main.pdf                成稿（45 页）
  main.tex                生成物 —— 论文主文件
  main_template.tex       模板（前言区、版面、宏占位符）—— 改版面改这里
  refs.bib                参考文献
  sections/01…07*.tex     正文七节 —— 改文字改这里
  tables/table1…9*.tex    表格源码（生成物）
  figures/                图（PDF 矢量 + PNG 预览 + 渲染自检 JSON）
  audits/                 一致性终审、完整性终审
  qa_report.md            质量保证报告（三项终审中的第三项）
code/
  Q1…Q4/                  四个问题的建模代码
      q*_main.py          主方法
      q*_baseline.py      可用基线（不同空间离散或时间推进）
      q*_verifier.py      独立验证（自建解析参照 + 契约不变量）
      q*_robustness.py    稳健性与灵敏度
  figures/                图表生成脚本 + 统一视觉系统（figure_style.py）
  paper_tables*.py        由指标生成表格源码
  freeze_*.py             生成冻结数字
  make_paper_package.py   打交付压缩包
  stage_paper_repo.py     同步本仓库
scripts/latex_assembly.py 组装 main.tex
results/                  指标 JSON、冻结数字、最终结果分析
robustness/               四问稳健性证据
planning/                 符号表、模型假设、模型契约
methods/                  每问最终方法说明与决策账本
workspace/data_clean/     清洗后的模型输入（运行代码所必需）
```

### 数据说明

本仓库为**公开仓库**，因此**不含赛题原文与官方附件原件**
（`workspace/problem.txt`、`workspace/data_raw/`）。
运行代码所需的清洗后输入（`workspace/data_clean/`）已包含，克隆后即可复现全部计算与图形。

**纳入**版本库的交付表：`result1.xlsx`、`result3.xlsx`、`result4.xlsx`（共 0.9 MB）——
它们是绘图脚本的输入，缺了 `-Full` 就跑不起来。

**未纳入**版本库：

| 文件 | 大小 | 原因 | 怎么重新生成 |
|---|---|---|---|
| `results/Q2/…/result2.xlsx` | 约 28 MB | 体积大，且论文管线不读它 | `python code/Q2/q2_main.py` |
| `paper/figures/*.svg` | 约 40 MB | LaTeX 用的是 PDF 矢量版 | `python code/figures/make_paper_figures.py` |
| `results/**/runs/` | 小 | 每次运行的快照，属过程记录 | 重跑模型自动生成 |
