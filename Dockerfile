# BTAUTOCHECK Docker镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y git curl && \
    rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 设置权限
RUN chmod +x *.sh *.py

# 创建必要的目录
RUN mkdir -p logs downloads backups

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 默认命令
CMD ["python3", "auto_update.py"]

