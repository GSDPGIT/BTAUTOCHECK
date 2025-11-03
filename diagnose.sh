#!/bin/bash
# -*- coding: utf-8 -*-
# 诊断检测卡住问题

echo "========================================"
echo "🔍 BTAUTOCHECK 诊断工具"
echo "========================================"
echo ""

# 检查进程
echo "📊 检查运行中的进程..."
ps aux | grep -E "auto_update|ai_security_check|download_and_check" | grep -v grep
if [ $? -eq 0 ]; then
    echo "⚠️  发现运行中的进程（可能卡住了）"
    echo ""
    read -p "是否杀死这些进程？(y/n): " kill_process
    if [ "$kill_process" = "y" ]; then
        pkill -f auto_update
        pkill -f ai_security_check
        pkill -f download_and_check
        echo "✅ 已杀死进程"
    fi
else
    echo "✅ 没有运行中的进程"
fi

echo ""
echo "========================================"
echo "📁 检查最新日志"
echo "========================================"
echo ""

# 查找最新的日志文件
latest_log=$(ls -t auto_check_*.log 2>/dev/null | head -1)

if [ -n "$latest_log" ]; then
    echo "📄 最新日志: $latest_log"
    echo ""
    echo "最后20行:"
    tail -20 "$latest_log"
    echo ""
    echo "----------------------------------------"
    echo "🔍 检查是否卡在AI分析..."
    grep -A 5 "AI深度安全分析" "$latest_log" | tail -10
else
    echo "❌ 没有找到日志文件"
fi

echo ""
echo "========================================"
echo "📂 检查下载文件"
echo "========================================"
ls -lh downloads/*.zip 2>/dev/null
ls -lh downloads/*.json 2>/dev/null

echo ""
echo "========================================"
echo "🔧 检查配置"
echo "========================================"
echo ""

# 检查AI配置
echo "AI配置状态:"
python3 << 'EOF'
import json
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    ai_config = config.get('ai_providers', {})
    print(f"AI总开关: {ai_config.get('enabled', False)}")
    print(f"主要提供商: {ai_config.get('primary_provider', 'N/A')}")
    print(f"备用启用: {ai_config.get('fallback_enabled', False)}")
    print("")
    
    for provider in ['gemini', 'openai', 'claude', 'qianwen', 'wenxin', 'zhipu', 'deepseek', 'kimi', 'grok', 'xunfei']:
        if provider in ai_config:
            enabled = ai_config[provider].get('enabled', False)
            has_key = bool(ai_config[provider].get('api_key', ''))
            print(f"  {provider}: {'✅' if enabled else '⭕'} 启用={enabled}, 有密钥={has_key}")
except Exception as e:
    print(f"❌ 读取配置出错: {e}")
EOF

echo ""
echo "========================================"
echo "💡 建议操作"
echo "========================================"
echo ""
echo "1. 如果进程卡住 → 重新运行本脚本选择杀死进程"
echo "2. 如果AI配置有问题 → 访问 Web界面 http://你的IP:5000"
echo "3. 手动重新检测:"
echo "   python3 auto_update.py"
echo ""
echo "4. 不使用AI，只用静态分析:"
echo "   # 临时关闭AI"
echo "   python3 << 'PYEOF'"
echo "import json"
echo "with open('config.json', 'r') as f:"
echo "    config = json.load(f)"
echo "config['ai_providers']['enabled'] = False"
echo "with open('config.json', 'w') as f:"
echo "    json.dump(config, f, indent=4)"
echo "print('✅ 已关闭AI')"
echo "PYEOF"
echo "   python3 auto_update.py"
echo ""
echo "========================================"

