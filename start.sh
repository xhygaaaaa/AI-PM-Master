#!/bin/bash

echo "🚀 启动 AI 产品经理学习平台"
echo ""

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件"
    echo "正在从 .env.example 创建 .env..."
    cp .env.example .env
    echo "✅ .env 文件已创建，请编辑填入你的 API 密钥"
    echo ""
    echo "请执行以下步骤："
    echo "1. 用文本编辑器打开 .env 文件"
    echo "2. 填入你的 LLM_API_KEY"
    echo "3. 保存后重新运行 ./start.sh"
    exit 1
fi

# 启动应用
echo "🔄 正在启动 Streamlit 应用..."
echo ""
streamlit run main.py
