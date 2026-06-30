#!/usr/bin/env bash
# 一键更新部署:提交本地改动 → 推送 GitHub → 触发 Render 部署 → 等待上线
# 用法:在项目根目录运行  ./deploy.sh  或  ./deploy.sh "你的更新说明"

set -e
cd "$(dirname "$0")"

# 读取密钥配置
if [ ! -f deploy.env ]; then
  echo "❌ 找不到 deploy.env(密钥配置)。请先创建它。"
  exit 1
fi
# shellcheck disable=SC1091
source deploy.env

MSG="${1:-Update site}"

echo "================================================"
echo " 🚀 一键更新部署:小微贷管家"
echo "================================================"

# 1) 提交本地改动
if [ -n "$(git status --porcelain)" ]; then
  echo "📝 [1/4] 提交本地改动…"
  git add -A
  git -c user.email="deploy@local" -c user.name="deploy" commit -q -m "$MSG

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
  echo "    ✅ 已提交:$MSG"
else
  echo "📝 [1/4] 没有新的本地改动,直接重新部署当前版本。"
fi

# 2) 推送到 GitHub
echo "📤 [2/4] 推送到 GitHub…"
PUSH_URL="https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${GITHUB_REPO}.git"
git -c credential.helper= push "$PUSH_URL" main:main 2>&1 | sed "s/${GITHUB_TOKEN}/***/g"
echo "    ✅ 代码已推送"

# 3) 触发 Render 部署
echo "🏗️  [3/4] 触发 Render 重新部署…"
DEPLOY_ID=$(curl -s -X POST \
  "https://api.render.com/v1/services/${RENDER_SERVICE_ID}/deploys" \
  -H "Authorization: Bearer ${RENDER_API_KEY}" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{"clearCache":"do_not_clear"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))")

if [ -z "$DEPLOY_ID" ]; then
  echo "    ❌ 触发部署失败,请检查 Render 密钥是否有效。"
  exit 1
fi
echo "    ✅ 部署已开始(ID: ${DEPLOY_ID})"

# 4) 轮询等待部署完成
echo "⏳ [4/4] 等待构建上线(通常 2-5 分钟)…"
for i in $(seq 1 40); do
  sleep 15
  STATUS=$(curl -s \
    "https://api.render.com/v1/services/${RENDER_SERVICE_ID}/deploys/${DEPLOY_ID}" \
    -H "Authorization: Bearer ${RENDER_API_KEY}" -H "Accept: application/json" \
    | python3 -c "import sys,json;print(json.load(sys.stdin).get('status',''))")
  printf "    … 状态:%s\n" "$STATUS"
  case "$STATUS" in
    live)
      echo ""
      echo "🎉 部署成功!网站已更新到最新版:"
      echo "   ${SITE_URL}"
      exit 0 ;;
    build_failed|update_failed|canceled|deactivated|pre_deploy_failed)
      echo ""
      echo "❌ 部署失败(状态:${STATUS})。"
      echo "   到 Render 后台看日志:https://dashboard.render.com/web/${RENDER_SERVICE_ID}"
      exit 1 ;;
  esac
done

echo "⚠️ 等待超时,但部署可能仍在进行。稍后到后台确认:"
echo "   https://dashboard.render.com/web/${RENDER_SERVICE_ID}"
