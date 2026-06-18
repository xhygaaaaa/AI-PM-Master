#!/bin/bash
echo "🚀 启动 AI 产品经理学习平台（前端 + 后端微服务）"
echo ""

if [ ! -f .env ]; then
    echo "⚠️  未找到 .env，正在创建..."
    cp .env.example .env
    echo "✅ 请编辑 .env 填入 API 密钥后重新运行"
    exit 1
fi

echo "🔄 启动 FastAPI 评测微服务（端口 8001）..."
uvicorn evaluation_service.main:app --port 8001 --reload &
FASTAPI_PID=$!

sleep 3

echo "🔄 启动 Streamlit 前端（端口 8501）..."
streamlit run main.py &
STREAMLIT_PID=$!

echo ""
echo "✅ 两个服务已启动："
echo "   - 前端界面：http://localhost:8501"
echo "   - 后端文档：http://localhost:8001/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 捕获退出信号，关闭两个进程
trap "kill $FASTAPI_PID $STREAMLIT_PID 2>/dev/null" EXIT
wait
