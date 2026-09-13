<#
  供 VS Code 的 LaTeX Workshop 调用的编译包装脚本。

  为什么需要它：
    main.tex 里的 input / lstinputlisting 路径都相对【仓库根目录】书写
    （见 编译说明.md 第二节）。而 LaTeX Workshop 传给编译命令的文档路径可能是
    绝对或相对形式，且其工作目录不一定是仓库根目录，两者无法用单纯的 args 调和：
      - 在 paper/ 里用绝对路径   -> 推出 paper/paper 这种嵌套目录
      - 无 -output-directory     -> 产物泄漏到当前工作目录（仓库根目录）

  做法（与仓库自带 build.ps1 一致）：
    切到仓库根目录，用相对路径 paper/main.tex 编译两遍（第二遍解析交叉引用），
    并用 -output-directory 把产物固定放在 paper/ 下。

  用法：
    scripts/latex_workshop_build.ps1 -TexFile <main.tex 的路径>
    （绝对路径或相对于当前目录的路径均可）

  注意：本文件必须保存为“UTF-8 带 BOM”。Windows PowerShell 5.1 读取无 BOM 的
  .ps1 时会按 ANSI(GBK) 解码，中文注释会把行边界搞乱并导致语法解析失败。
#>
param(
  [Parameter(Mandatory = $true)]
  [string]$TexFile
)

$ErrorActionPreference = 'Stop'

# 兼容绝对路径与相对路径
$resolved = if ([System.IO.Path]::IsPathRooted($TexFile)) {
  $TexFile
} else {
  Join-Path (Get-Location).Path $TexFile
}
$resolved = [System.IO.Path]::GetFullPath($resolved)

if (-not (Test-Path $resolved)) {
  Write-Host "找不到目标文件: $resolved"
  exit 1
}

# 由 main.tex 的绝对路径反推仓库根目录：repo/paper/main.tex -> repo
$texDir     = Split-Path -Parent $resolved          # repo/paper
$repoRoot   = Split-Path -Parent $texDir            # repo
$texName    = Split-Path -Leaf  $resolved           # main.tex
$texDirName = Split-Path -Leaf  $texDir             # paper

# 相对路径用正斜杠：反斜杠在 TeX 里是转义符
$relPath = "$texDirName/$texName"
$outArg  = "-output-directory=$texDirName"

Set-Location $repoRoot

$exitCode = 0
foreach ($i in 1..2) {
  & xelatex -interaction=nonstopmode -file-line-error -synctex=1 $outArg $relPath
  $exitCode = $LASTEXITCODE
  if ($exitCode -ne 0) { break }
}

exit $exitCode
