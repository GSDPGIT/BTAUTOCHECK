# ========================================
# BTAUTOCHECK Docker镜像
# 企业级BT面板自动化安全检测与管理系统
# ========================================

FROM python:3.9-slim

LABEL maintainer="Lee自用" \
      version="2.0" \
      description="BTAUTOCHECK - BT-Panel Auto Security Check System"

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        curl \
        unzip \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 设置执行权限
RUN chmod +x *.sh && \
    find . -name "*.py" -exec chmod +x {} \;

# 创建必要的目录
RUN mkdir -p logs downloads backups templates static

# 创建数据卷
VOLUME ["/app/downloads", "/app/backups", "/app/logs"]

# 暴露Web端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=web_admin.py \
    TZ=Asia/Shanghai

# 启动Web管理系统（包含自动调度器）
CMD ["python3", "web_admin.py"]

