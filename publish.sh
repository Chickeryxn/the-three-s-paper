#!/bin/sh
# 构建并推送：生成 PDF -> 提交 -> 推送。用法（在仓库根目录执行）:
#   sh publish.sh                     改了正文
#   sh publish.sh '改写第 5 节'        自定义提交信息
#   sh publish.sh '' --full           连表格与图形一起重做
set -e
cd "$(dirname "$0")"

msg="$1"
if [ "$2" = "--full" ]; then
  sh build.sh --full
else
  sh build.sh
fi

email=$(git config user.email || true)
case "$email" in
  *noreply.github.com) ;;
  *) echo '';
     echo "  警告：当前 git user.email = $email";
     echo '  GitHub 可能以 GH007（私人邮箱保护）拒绝推送。建议改为 noreply 地址：';
     echo '    git config user.email "<你的ID>+<用户名>@users.noreply.github.com"' ;;
esac

git add -A
if [ -z "$(git diff --cached --name-only)" ]; then
  echo ''
  echo '  没有需要提交的改动。'
  exit 0
fi
[ -n "$msg" ] || msg="update: 论文更新 $(date '+%Y-%m-%d %H:%M')"
git commit -m "$msg"
git push || { echo ''; echo '  推送失败。常见原因：'; echo '    - GH007 私人邮箱保护 -> 见上面的建议'; echo '    - 远端有新提交       -> 先 git pull --rebase 再重试'; exit 1; }
echo ''
echo '  已推送到远端。'
