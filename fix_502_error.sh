#!/bin/bash
# 502错误诊断和修复脚本

echo "======================================"
echo "🔍 502错误诊断"
echo "======================================"
echo ""

cd ~/BTAUTOCHECK

# 1. 检查服务状态
echo "1️⃣ 检查服务状态..."
ps aux | grep web_admin.py | grep -v grep
if [ $? -eq 0 ]; then
    echo "⚠️  服务进程存在但可能有问题"
else
    echo "❌ 服务未运行"
fi
echo ""

# 2. 停止所有相关进程
echo "2️⃣ 停止旧进程..."
pkill -9 -f web_admin.py
sleep 2
echo "✅ 已清理"
echo ""

# 3. 检查端口占用
echo "3️⃣ 检查端口5000..."
netstat -tunlp | grep 5000
if [ $? -eq 0 ]; then
    echo "⚠️  端口5000被占用，尝试释放..."
    lsof -ti:5000 | xargs kill -9 2>/dev/null
    sleep 1
fi
echo "✅ 端口检查完成"
echo ""

# 4. 测试Python语法
echo "4️⃣ 测试Python代码..."
python3 -m py_compile web_admin.py
if [ $? -ne 0 ]; then
    echo "❌ web_admin.py有语法错误！"
    echo ""
    echo "尝试修复："
    python3 web_admin.py 2>&1 | head -20
    exit 1
fi
echo "✅ Python语法正确"
echo ""

# 5. 检查依赖
echo "5️⃣ 检查依赖模块..."
python3 << 'EOF'
import sys
try:
    from flask import Flask
    from analytics import AnalyticsEngine
    from alert_rules import AlertRulesEngine
    from ai_consensus import AIConsensusAnalyzer
    print("✅ 所有依赖正常")
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  模块导入有问题，查看详细错误："
    python3 web_admin.py 2>&1 | head -30
    exit 1
fi
echo ""

# 6. 查看最近的错误日志
echo "6️⃣ 查看错误日志（如果有）..."
if [ -f web.log ]; then
    echo "--- 最近的日志 ---"
    tail -30 web.log
    echo ""
fi

# 7. 重新启动服务
echo "7️⃣ 重新启动服务..."
nohup python3 web_admin.py > web.log 2>&1 &
sleep 3

# 8. 检查启动状态
echo "8️⃣ 检查启动状态..."
if ps aux | grep -v grep | grep web_admin.py > /dev/null; then
    echo "✅ 服务已启动"
    
    # 查看启动日志
    echo ""
    echo "--- 启动日志 ---"
    tail -20 web.log
    
    echo ""
    echo "======================================"
    echo "✅ 修复完成！"
    echo "======================================"
    echo ""
    echo "🌐 访问: http://$(hostname -I | awk '{print $1}'):5000"
    echo ""
    echo "💡 如果还是502，请运行："
    echo "   tail -50 web.log"
    echo ""
else
    echo "❌ 启动失败！"
    echo ""
    echo "请查看详细错误："
    echo "======================================"
    cat web.log
    echo "======================================"
fi


