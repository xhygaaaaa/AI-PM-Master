@echo off
chcp 65001 >/dev/null
echo 🚀 启动 AI 产品经理学习平台
echo.

REM 检查 .env 文件
if not exist .env (
    echo ⚠️  未找到 .env 文件
    echo 正在从 .env.example 创建 .env...
    copy .env.example .env >/dev/null
    echo ✅ .env 文件已创建
    echo.
    echo 请执行以下步骤：
    echo 1. 用文本编辑器打开 .env 文件
    echo 2. 填入你的 LLM_API_KEY
    echo 3. 保存后重新运行 start.bat
    pause
    exit /b
)

REM 启动应用
echo 🔄 正在启动 Streamlit 应用...
echo.
streamlit run main.py
