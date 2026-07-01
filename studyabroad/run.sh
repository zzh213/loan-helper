#!/bin/bash
# 启动出国读研选校匹配（FastAPI 后端 + 静态前端）
# 用法: ./run.sh  然后浏览器打开 http://127.0.0.1:8200
set -e
cd "$(dirname "$0")"
PORT="${PORT:-8200}"
echo "🎓 选校匹配启动中... http://127.0.0.1:${PORT}"
exec python3 -m uvicorn backend.app:app --host 127.0.0.1 --port "${PORT}"
