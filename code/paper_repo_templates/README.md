# the-three-s-paper

2026 年高教社杯全国大学生数学建模竞赛 **A 题 药材的烘干问题** 的论文与生成工具链。

本仓库不只放论文源码，也放**生成论文的全部工具**：正文数值由冻结数字经脚本注入，
表格由指标文件生成，图形由绘图脚本重绘。因此任何一处改动都可以追溯到源头，
多人协作时不会出现"谁手改了哪个数字"的问题。

## 快速开始

```bash
git clone https://github.com/Chickeryxn/the-three-s-paper.git
cd the-three-s-paper

# 编译论文（需要 XeLaTeX + 中文字体：宋体 SimSun、黑体 SimHei）
xelatex -interaction=nonstopmode -output-directory=paper paper/main.tex
xelatex -interaction=nonstopmode -output-directory=paper paper/main.tex
```

Windows 下双击 `build.ps1`，macOS / Linux 用 `./build.sh`。
当前成稿：**45 页，0 个 LaTeX 错误，0 个 overfull hbox**。

> `main.tex` 里的路径（`\input{paper/sections/…}`、`\lstinputlisting{code/Q1/…}`）
> 是相对**仓库根目录**写的，务必从根目录编译。

## 仓库结构

```
paper/
  main.pdf                成稿（每次改完请重新编译）
  main.tex                论文主文件 —— 注意：这是生成物
  main_template.tex       模板（前言区、版面设置、宏注入占位符）
  refs.bib                参考文献
  sections/01…07*.tex     正文七节 —— 平时改这里
  tables/table1…9*.tex    表格源码 —— 生成物
  figures/                正文与附录图（PDF 矢量 + PNG 预览 + 渲染证据 JSON）
  audits/                 三项终审记录（一致性 / 完整性 / QA）
  qa_report.md            质量保证报告
code/
  Q1…Q4/                  四个问题的建模代码
      q*_main.py          主方法
      q*_baseline.py      可用基线（独立的空间离散或时间推进）
      q*_verifier.py      独立验证（自建解析参照 + 契约不变量）
      q*_robustness.py    稳健性与灵敏度
  figures/                全部图表生成脚本 + 统一视觉系统
  paper_tables*.py        由指标文件生成表格源码
  freeze_*.py             生成冻结数字
  make_paper_package.py   打交付压缩包
  stage_paper_repo.py     同步本仓库
scripts/latex_assembly.py 由模板与各节生成 main.tex
results/                  指标 JSON、冻结数字、最终结果分析
robustness/               四问的稳健性证据
planning/                 符号表、模型假设、模型契约
methods/                  每问的最终方法说明与决策账本
workspace/data_clean/     清洗后的模型输入（运行代码所必需）
```

## 三条最重要的协作规则

**1. 不要手写数字。** 正文里的每一个数值都是 LaTeX 宏，由
`scripts/latex_assembly.py` 从 `results/Q*/reports/frozen_numbers.json` 注入；
表格由 `code/paper_tables*.py` 从 `metrics/*.json` 生成。
直接改 `paper/main.tex` 或 `paper/tables/*.tex` 里的数字，下一次生成就会被覆盖。

**2. 要改数值，改源头再重新生成。**

```bash
python code/Q2/q2_main.py          # 重跑模型
python code/freeze_q1q3.py         # 重新冻结数字
python scripts/latex_assembly.py . --template paper/main_template.tex
python code/paper_tables.py        # 重新生成表格
```

**3. 改图要改脚本，不要改产物。** `paper/figures/*.pdf` 由
`code/figures/make_paper_figures.py` / `make_appendix_figures.py` 生成，
每个图都带一份 `*.render.json` 渲染自检记录（文字是否越界、是否重叠、字号是否过小等）。
直接替换 PDF 会让自检记录与图对不上。

## 哪些文件是"生成物"

| 文件 | 谁是源头 | 怎么重新生成 |
|---|---|---|
| `paper/main.tex` | `main_template.tex` + `sections/` + `frozen_numbers.json` | `python scripts/latex_assembly.py . --template paper/main_template.tex` |
| `paper/tables/table1…6` | `results/Q*/…/metrics/main.json` | `python code/paper_tables.py` |
| `paper/tables/table7…9` | `metrics/*.json` + `robustness/*.json` | `python code/paper_tables_extra.py` |
| `paper/figures/*` | `code/figures/make_*.py` | `python code/figures/make_paper_figures.py` |
| `results/Q*/reports/frozen_numbers.json` | `code/freeze_*.py` | 见上 |
| `paper/main.pdf` | 上面全部 | 编译两遍 |

**平时只改 `paper/sections/*.tex`（文字）和 `main_template.tex`（版面）。**

## 合并时怎么减少冲突

- `paper/main.tex`、`paper/tables/*.tex`、`paper/main.pdf` 都是生成物，**冲突时不要手工合并**——
  取任意一方，然后在本机重新生成即可。
- 真正的编辑冲突只会出现在 `paper/sections/*.tex` 和 `main_template.tex`，正常合并即可。
- 提交前建议跑一遍完整生成链，确认 `main.tex` 与 `sections/` 一致再提交。

## 数据说明

本仓库为**公开仓库**，因此**不包含赛题原文与官方附件原件**
（`workspace/problem.txt`、`workspace/data_raw/`）。
运行代码所需的清洗后输入（`workspace/data_clean/`）已包含在内，
因此克隆后即可复现全部计算与图形。

问题二的完整计算场 `result2.xlsx`（约 28 MB）同样未纳入版本管理，
运行 `python code/Q2/q2_main.py` 可重新生成。
