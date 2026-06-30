#!/usr/bin/env bash
# 一键启动小微贷管家(自动加载 .env 中的 API Key 并接入通义千问)
set -e

cd "$(dirname "$0")"

# 加载 .env(如果存在)
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# 停掉占用 8000 端口的旧进程
PIDS=$(lsof -ti tcp:8000 || true)
if [ -n "$PIDS" ]; then
  echo "停止旧服务: $PIDS"
  for pid in $PIDS; do kill "$pid" 2>/dev/null || true; done
  sleep 1
fi

# 提示是否已配置大模型
if [ -n "$AZURE_OPENAI_ENDPOINT" ] && [ -n "$AZURE_OPENAI_API_KEY" ] && [ -n "$AZURE_OPENAI_DEPLOYMENT" ]; then
  echo "✅ 已检测到 Azure OpenAI 配置,智能助手将接入 Azure(${AZURE_OPENAI_DEPLOYMENT})"
elif [ -n "$DASHSCOPE_API_KEY" ] && [[ "$DASHSCOPE_API_KEY" == sk-* ]] && [[ "$DASHSCOPE_API_KEY" != *"粘贴"* ]]; then
  echo "✅ 已检测到 API Key,智能助手将接入通义千问(${QWEN_MODEL:-qwen-plus})"
else
  unset DASHSCOPE_API_KEY
  echo "⚠️  未配置有效的大模型,将使用本地 Ollama 或内置知识库降级模式。"
  echo "    可在 .env 配置 Azure OpenAI 或以 sk- 开头的通义千问密钥后重新运行。"
fi

echo "🚀 启动中... http://127.0.0.1:8000/"
cd backend
exec python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
