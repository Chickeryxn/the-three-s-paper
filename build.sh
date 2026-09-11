#!/bin/sh
# 一键生成论文 PDF。用法（在仓库根目录执行）:
#   sh build.sh           改了正文后用这个
#   sh build.sh --full    改了生成脚本或数值后用这个，连表格与图形一起重做
set -e
cd "$(dirname "$0")"

full=0
[ "${1:-}" = "--full" ] && full=1

# macOS 12.3 起系统不再自带 `python`，只有 `python3`；优先 python3 并回退到 python。
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo '  [失败] 找不到 python3 / python，请先安装 Python 3 并加入 PATH'; exit 1
fi
command -v xelatex >/dev/null 2>&1 || { echo '  [失败] 找不到 xelatex，请安装 TeX Live 或 MiKTeX 完整版'; exit 1; }

if [ $full -eq 1 ]; then
  echo '[1/4] 重新生成表格与图形 ...'
  "$PY" code/paper_tables.py
  "$PY" code/paper_tables_extra.py
  "$PY" code/figures/make_paper_figures.py
  "$PY" code/figures/make_appendix_figures.py
else
  echo '[1/4] 跳过表格与图形（需要时用 --full）'
fi

echo '[2/4] 组装 paper/main.tex ...'
"$PY" scripts/latex_assembly.py . --template paper/main_template.tex >/dev/null

echo '[3/4] 编译两遍 ...'
xelatex -interaction=nonstopmode -output-directory=paper paper/main.tex >/dev/null
xelatex -interaction=nonstopmode -output-directory=paper paper/main.tex >/dev/null

echo '[4/4] 检查日志 ...'
errors=$(grep -c '^! ' paper/main.log || true)
overfull=$(grep -c 'Overfull .hbox' paper/main.log || true)
# TeX 会在日志里折行，甚至把 (45 拆成 (4 + 换行 + 5，所以先删掉全部空白再匹配
pages=$(tr -d '[:space:]' < paper/main.log | sed -n 's/.*Outputwrittenon.*(\([0-9]*\)pages.*/\1/p')
echo ''
echo "  页数       : $pages"
echo "  LaTeX 错误 : $errors"
echo "  overfull   : $overfull"
if [ "$errors" != '0' ]; then
  echo '  [失败] 编译存在错误，PDF 不可用。请看 paper/main.log 里的 ! 行。'
  exit 1
fi
echo ''
echo '  完成 -> paper/main.pdf'
