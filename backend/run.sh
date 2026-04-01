#!/bin/bash
# 启动 FastAPI 服务器的 bash 脚本

# 进入后端目录
cd "$(dirname "$0")"

echo "🚀 启动 FastAPI 服务器..."
echo "后端将在 http://localhost:8000 运行"
echo "API 文档将在 http://localhost:8000/docs 显示"
echo ""
echo "按 CTRL+C 停止服务器"
echo ""

# 启动 Uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
