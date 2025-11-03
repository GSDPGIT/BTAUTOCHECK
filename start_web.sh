#!/bin/bash
# BTAUTOCHECK Web管理系统启动脚本

echo "======================================================================"
echo "🌐 启动 BTAUTOCHECK Web管理系统"
echo "======================================================================"

# 进入项目目录
cd "$(dirname "$0")"

# 检查Flask是否安装
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 安装Flask依赖..."
    pip3 install flask
fi

# 启动Web服务器
echo ""
echo "正在启动Web服务器..."
echo ""

python3 web_admin.py


