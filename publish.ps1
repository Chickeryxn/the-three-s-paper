<#
  构建并推送：一条命令完成 生成 PDF -> 提交 -> 推送。

  用法（在仓库根目录执行）:
    .\publish.ps1                          改了正文，提交信息自动生成
    .\publish.ps1 -Message '改写第 5 节'    自定义提交信息
    .\publish.ps1 -Full -Message '...'      连表格与图形一起重做后再推

  构建失败（编译有错）时不会提交，避免把坏 PDF 推给协作者。
#>
param([string]$Message = '', [switch]$Full)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

# ---- 1. 先构建 -------------------------------------------------------------
$build = Join-Path $PSScriptRoot 'build.ps1'
$buildArgs = @{}
if ($Full) { $buildArgs['Full'] = $true }
& $build @buildArgs
if ($LASTEXITCODE -ne 0) { Write-Host '  构建未通过，已中止提交。' -ForegroundColor Red; exit $LASTEXITCODE }

# ---- 2. 提交身份提醒 -------------------------------------------------------
# GitHub 默认拒绝会暴露私人邮箱的推送（GH007），这里提前警告
$email = (git config user.email) 2>$null
if ($email -and $email -notmatch 'noreply\.github\.com$') {
  Write-Host ''
  Write-Host "  警告：当前 git user.email = $email" -ForegroundColor Yellow
  Write-Host '  GitHub 可能以 GH007（私人邮箱保护）拒绝推送。建议改为 noreply 地址：' -ForegroundColor Yellow
  Write-Host '    git config user.email "<你的ID>+<用户名>@users.noreply.github.com"' -ForegroundColor Yellow
}

# ---- 3. 提交 ---------------------------------------------------------------
git add -A
$staged = git diff --cached --name-only
if (-not $staged) {
  Write-Host ''
  Write-Host '  没有需要提交的改动。' -ForegroundColor DarkGray
  exit 0
}
if (-not $Message) { $Message = 'update: 论文更新 ' + (Get-Date -Format 'yyyy-MM-dd HH:mm') }
git commit -m $Message
if ($LASTEXITCODE -ne 0) { Write-Host '  提交失败。' -ForegroundColor Red; exit 1 }

# ---- 4. 推送 ---------------------------------------------------------------
git push
if ($LASTEXITCODE -ne 0) {
  Write-Host ''
  Write-Host '  推送失败。常见原因：' -ForegroundColor Red
  Write-Host '    - GH007 私人邮箱保护  -> 见上面的建议' -ForegroundColor Red
  Write-Host '    - 远端有新提交        -> 先 git pull --rebase 再重试' -ForegroundColor Red
  exit 1
}
Write-Host ''
Write-Host '  已推送到远端。' -ForegroundColor Green
exit 0
