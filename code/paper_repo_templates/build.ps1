<#
  一键生成论文 PDF。

  用法（在本仓库根目录执行）:
    .\build.ps1            改了正文（paper/sections/*.tex 或 paper/main_template.tex）后用这个
    .\build.ps1 -Full      改了生成脚本或数值后用这个，连表格与图形一起重做

  成功时退出码为 0，并打印页数 / 错误数 / overfull 数。编译有错则退出码为 1。
#>
param([switch]$Full)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Fail([string]$msg) {
  Write-Host ''
  Write-Host "  [失败] $msg" -ForegroundColor Red
  exit 1
}

# ---- 1. 环境检查 ----------------------------------------------------------
if (-not (Get-Command python  -ErrorAction SilentlyContinue)) { Fail '找不到 python，请先安装并加入 PATH' }
if (-not (Get-Command xelatex -ErrorAction SilentlyContinue)) { Fail '找不到 xelatex，请安装 TeX Live 或 MiKTeX 完整版' }

# ---- 2. 输出文件是否被 PDF 阅读器占用 -------------------------------------
# dvipdfmx 在文件被占用时报 Unable to open main.pdf，信息很不直观，这里提前拦下
if (Test-Path 'paper/main.pdf') {
  try {
    $fs = [System.IO.File]::Open((Resolve-Path 'paper/main.pdf').Path,
                                 [System.IO.FileMode]::Open,
                                 [System.IO.FileAccess]::ReadWrite,
                                 [System.IO.FileShare]::None)
    $fs.Close()
  } catch {
    Fail 'paper/main.pdf 正被其他程序占用（多半是 PDF 阅读器）。请关闭后重试。'
  }
}

# ---- 2b. -Full 所需的数据文件 ---------------------------------------------
if ($Full) {
  $need = @(
    'results/Q1/experiments/round1/result1.xlsx',
    'results/Q3/experiments/round1/result3.xlsx',
    'results/Q4/experiments/round1/result4.xlsx'
  )
  $gone = @($need | Where-Object { -not (Test-Path $_) })
  if ($gone.Count -gt 0) {
    Write-Host ''
    Write-Host '  [失败] 缺少绘图脚本要读的数据文件：' -ForegroundColor Red
    foreach ($g in $gone) { Write-Host ('    ' + $g) -ForegroundColor Red }
    Write-Host '  重新生成：python code/Q1/q1_main.py（Q3 / Q4 同理）' -ForegroundColor Yellow
    exit 1
  }
}

# ---- 3. 重新生成中间产物 --------------------------------------------------
if ($Full) {
  Write-Host '[1/4] 重新生成表格与图形 ...' -ForegroundColor Cyan
  python code/paper_tables.py;                  if ($LASTEXITCODE -ne 0) { Fail 'code/paper_tables.py 失败' }
  python code/paper_tables_extra.py;            if ($LASTEXITCODE -ne 0) { Fail 'code/paper_tables_extra.py 失败' }
  python code/figures/make_paper_figures.py;    if ($LASTEXITCODE -ne 0) { Fail '生成正文图失败' }
  python code/figures/make_appendix_figures.py; if ($LASTEXITCODE -ne 0) { Fail '生成附录图失败' }
} else {
  Write-Host '[1/4] 跳过表格与图形（需要时用 -Full）' -ForegroundColor DarkGray
}

# ---- 4. 组装 main.tex ------------------------------------------------------
Write-Host '[2/4] 组装 paper/main.tex ...' -ForegroundColor Cyan
python scripts/latex_assembly.py . --template paper/main_template.tex | Out-Null
if ($LASTEXITCODE -ne 0) { Fail 'latex_assembly.py 失败：检查 frozen_numbers.json 与模板占位符' }

# ---- 5. 编译两遍 -----------------------------------------------------------
# 第一遍写 .aux，交叉引用尚未解析，版面长度会变；第二遍才稳定
Write-Host '[3/4] 编译两遍 ...' -ForegroundColor Cyan
foreach ($i in 1..2) {
  xelatex -interaction=nonstopmode -output-directory=paper paper/main.tex | Out-Null
}

# ---- 6. 报告 ---------------------------------------------------------------
Write-Host '[4/4] 检查日志 ...' -ForegroundColor Cyan
$log      = Get-Content 'paper/main.log' -Raw -Encoding UTF8
$errors   = ([regex]::Matches($log, '(?m)^! ')).Count
$overfull = ([regex]::Matches($log, 'Overfull \\hbox')).Count
# TeX 会在日志里折行，甚至把 (45 拆成 (4 + 换行 + 5，所以先删掉全部空白再匹配
$flat     = ($log -replace '\s+', '')
$pages    = ([regex]::Match($flat, 'Outputwrittenon.*?\((\d+)pages')).Groups[1].Value

Write-Host ''
Write-Host ("  页数       : {0}" -f $pages)
Write-Host ("  LaTeX 错误 : {0}" -f $errors)
Write-Host ("  overfull   : {0}" -f $overfull)
if ($errors -gt 0) { Fail '编译存在错误，PDF 不可用。请看 paper/main.log 里的 ! 行。' }
if ($overfull -gt 0) {
  Write-Host '  注意：存在 overfull hbox（不阻塞提交，但请到 paper/main.log 定位）' -ForegroundColor Yellow
}
Write-Host ''
Write-Host '  完成 -> paper/main.pdf' -ForegroundColor Green
exit 0
