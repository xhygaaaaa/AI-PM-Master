# Docker 镜像 - 同时支持 Streamlit 前端和 FastAPI 后端
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置国内 pip 镜像（加速安装）
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 先复制依赖文件（利用 Docker 缓存层）
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 暴露两个端口：8501（Streamlit）和 8001（FastAPI）
EXPOSE 8501 8001

# 默认启动 Streamlit（FastAPI 由 docker-compose 单独指定命令）
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
