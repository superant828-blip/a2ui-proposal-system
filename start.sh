#!/bin/bash
# 启动改善提案系统

cd /home/test/.openclaw/workspace/a2ui-proposal-system

# 启动后端 API
echo "启动 API 服务..."
python3 backend/api.py &
API_PID=$!

echo "API 服务已启动 (PID: $API_PID)"
echo "访问 http://localhost:8004/docs 查看 API 文档"

# 等待
wait $API_PID
