# 2026 年高教社杯全国大学生数学建模竞赛 A 题
# 药材的烘干问题 —— 论文包

本包含论文 LaTeX 源码、全部图表、建模程序、数值结果与原始附件。
解压后请**保持目录结构不变**，直接编译 paper/main.tex 即可。

## 一、先看什么

| 想做什么 | 看这个 |
|---|---|
| 直接读论文 | **paper/main.pdf**（45 页，含代码附录） |
| 改论文、重新编译 | **paper/main.tex** |
| 看公式与推导的源文件 | paper/sections/01…07*.tex |
| 看图表源文件 | paper/tables/*.tex、paper/figures/*.pdf |
| 跑模型、复核数值 | code/Q1…Q4/*.py |
| 核对论文里每个数字的来源 | results/Q*/reports/frozen_numbers.json |

## 二、编译方法

需要 **XeLaTeX**（TeX Live 或 MiKTeX，建议完整安装）与中文字体（宋体 SimSun、黑体 SimHei）。
在包根目录执行，**连续编译两遍**（第二遍用于解析交叉引用与页码）：

    xelatex -interaction=nonstopmode -output-directory=paper paper/main.tex
    xelatex -interaction=nonstopmode -output-directory=paper paper/main.tex

Windows 下也可直接双击 build.ps1（macOS / Linux 用 build.sh）。

实测结果：**45 页，0 个 LaTeX 错误，0 个 overfull hbox**。

> 注意：main.tex 的路径是相对**包根目录**写的（\input{paper/sections/…}、
> \lstinputlisting{code/Q1/…}），因此必须从包根目录编译，不要单独把 main.tex 拷到别处。

## 三、目录结构

    paper/
      main.pdf                 成稿（45 页）
      main.tex                 论文主文件，可直接编译
      main_template.tex        模板（前言区、宏定义占位符）
      refs.bib                 参考文献
      sections/01…07*.tex      正文七节
      tables/table1…9*.tex     表格源码
      figures/fig01…fig06、figA1…figA3   正文与附录图（PDF 矢量 + PNG 预览）
      audits/                  三项终审记录
      qa_report.md             质量保证报告
    code/
      Q1…Q4/                   四个问题的建模代码（主方法 / 基线 / 独立验证 / 稳健性）
      figures/                 全部图表生成脚本（含统一视觉系统与渲染自检）
      paper_tables*.py         由数值结果生成表格源码
      freeze_*.py              生成冻结数字
    scripts/latex_assembly.py  由模板与各节重新生成 main.tex
    results/
      Q*/experiments/round1/   交付表 result1…4.xlsx、指标 JSON、运行快照
      Q*/reports/              frozen_numbers.json（论文中每个数字的唯一来源）
    robustness/                四问的稳健性与灵敏度证据
    planning/                  符号表、模型假设、模型契约（论文符号说明的依据）
    workspace/                 题目原文、附件 1/2、清洗后的数据

## 四、复现数值结果

    python code/Q1/q1_main.py      # 问题一主方法
    python code/Q1/q1_baseline.py  # 问题一基线
    python code/Q1/q1_verifier.py  # 问题一独立验证
    # Q2 / Q3 / Q4 同理
    python code/figures/make_paper_figures.py   # 重绘正文图

仅依赖 Python 标准库 + NumPy / SciPy / Matplotlib / openpyxl。
问题四主方法在本机约 27 s，问题一主方法约 6 min。

## 五、几点说明

1. **论文中的每一个数字都不是手写的。** 正文数值由 frozen_numbers.json 经
   scripts/latex_assembly.py 生成为 LaTeX 宏注入；表格由 code/paper_tables*.py
   从 metrics/*.json 直接生成。要改数字必须改源头再重新生成。
2. **图形文件只收录 PDF 与 PNG。** SVG 版本（约 40 MB，字体已转路径）未收录，
   因为 LaTeX 用的是 PDF 矢量版；若需要 SVG，运行 code/figures/make_paper_figures.py 可重新导出。
3. **本包{HEAVY} 27.5 MB 的 result2.xlsx**（问题二的完整计算场，行数很多）。
   若只需论文与代码，删掉该文件即可把包压到 8 MB 以内；
   需要时运行 python code/Q2/q2_main.py 可重新生成。
4. 图表渲染证据记录在 paper/figures/*.render.json。
