@echo off
chcp 65001 >/dev/null
echo 🚀 启动 AI 产品经理学习平台（前端 + 后端微服务）
echo.

if not exist .env (
    echo ⚠️  未找到 .env 文件，正在创建...
    copy .env.example .env >/dev/null
    echo ✅ 请编辑 .env 填入 API 密钥后重新运行
    pause
    exit /b
)

echo 🔄 启动 FastAPI 评测微服务（端口 8001）...
start "评测微服务" cmd /k "uvicorn evaluation_service.main:app --port 8001 --reload"

timeout /t 3 >/dev/null

echo 🔄 启动 Streamlit 前端（端口 8501）...
start "Streamlit前端" cmd /k "streamlit run main.py"

echo.
echo ✅ 两个服务已启动：
echo    - 前端界面：http://localhost:8501
echo    - 后端文档：http://localhost:8001/docs
echo.
pause
