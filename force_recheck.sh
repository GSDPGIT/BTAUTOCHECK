#!/bin/bash
# -*- coding: utf-8 -*-
# 强制重新检测当前版本（用于AI重新分析）

echo "========================================"
echo "🔄 强制重新检测当前版本"
echo "========================================"
echo ""

# 读取当前版本
current_version=$(python3 -c "import json; print(json.load(open('config.json'))['current_version'])")
echo "📌 当前版本: $current_version"

if [ -z "$current_version" ]; then
    echo "❌ 无法读取当前版本"
    exit 1
fi

# 检查AI配置
echo ""
echo "🤖 AI配置状态:"
python3 << 'EOF'
import json
with open('config.json', 'r') as f:
    config = json.load(f)
ai = config.get('ai_providers', {})
print(f"  总开关: {ai.get('enabled')}")
print(f"  主AI: {ai.get('primary_provider')}")
enabled_count = 0
for provider, cfg in ai.items():
    if provider in ['enabled', 'primary_provider', 'fallback_enabled']:
        continue
    if isinstance(cfg, dict) and cfg.get('enabled'):
        has_key = bool(cfg.get('api_key', ''))
        print(f"  ✅ {provider}: 已启用, 有密钥={has_key}")
        enabled_count += 1

if ai.get('enabled') and enabled_count == 0:
    print("  ⚠️  警告: AI总开关已开启，但没有启用任何AI提供商！")
elif not ai.get('enabled'):
    print("  ⚠️  AI总开关已关闭，将只进行静态分析")
EOF

echo ""
read -p "继续重新检测？(y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "❌ 已取消"
    exit 0
fi

echo ""
echo "========================================"
echo "🗑️  清理旧文件"
echo "========================================"

# 备份配置
cp config.json config.json.force_backup

# 删除旧的检测结果
echo "删除旧的检测结果..."
rm -f downloads/security_report_${current_version}.json
rm -f downloads/SECURITY_REPORT_${current_version}.md
rm -f downloads/extracted_${current_version}/.analyzed
echo "✅ 已清理"

echo ""
echo "========================================"
echo "📥 步骤1: 下载并基础检查"
echo "========================================"

# 创建临时version文件
cat > new_version.json << VEOF
{
    "version": "${current_version}",
    "download_url": "http://io.bt.sb/install/update/LinuxPanel-${current_version}.zip",
    "check_time": "$(date '+%Y-%m-%d %H:%M:%S')"
}
VEOF

# 检查是否已下载
if [ -f "downloads/LinuxPanel-${current_version}.zip" ]; then
    echo "✅ 安装包已存在，跳过下载"
else
    echo "正在下载..."
    python3 2_download_and_check.py
fi

echo ""
echo "========================================"
echo "🔍 步骤2: AI安全深度分析"
echo "========================================"
echo ""
echo "⏱️  这可能需要几分钟..."
echo ""

# 设置超时（10分钟）
timeout 600 python3 3_ai_security_check.py

exit_code=$?

if [ $exit_code -eq 124 ]; then
    echo ""
    echo "⚠️  AI分析超时（10分钟），可能网络问题或API调用失败"
    echo ""
    read -p "是否跳过AI，只生成静态分析报告？(y/n): " skip_ai
    if [ "$skip_ai" = "y" ]; then
        # 临时关闭AI
        python3 << 'EOF'
import json
with open('config.json', 'r') as f:
    config = json.load(f)
config['ai_providers']['enabled'] = False
with open('config.json', 'w') as f:
    json.dump(config, f, indent=4, ensure_ascii=False)
print("✅ 已临时关闭AI")
EOF
        # 重新运行静态分析
        python3 3_ai_security_check.py
        # 恢复AI配置
        mv config.json.force_backup config.json
    else
        echo "❌ 已取消"
        exit 1
    fi
elif [ $exit_code -ne 0 ]; then
    echo ""
    echo "❌ AI分析失败（退出码: $exit_code）"
    exit 1
fi

echo ""
echo "========================================"
echo "📄 步骤3: 生成Markdown报告"
echo "========================================"

python3 4_generate_report.py

echo ""
echo "========================================"
echo "✅ 重新检测完成！"
echo "========================================"
echo ""

# 显示报告摘要
if [ -f "downloads/SECURITY_REPORT_${current_version}.md" ]; then
    echo "📊 安全评分:"
    grep "安全评分" downloads/SECURITY_REPORT_${current_version}.md | head -1
    
    echo ""
    echo "🤖 AI分析结果:"
    grep -A 15 "## 🤖 AI深度分析" downloads/SECURITY_REPORT_${current_version}.md | head -20
    
    echo ""
    echo "----------------------------------------"
    echo "📄 完整报告："
    echo "  cat downloads/SECURITY_REPORT_${current_version}.md"
    echo ""
    echo "  或在Web界面查看: http://$(hostname -I | awk '{print $1}'):5000"
    echo "----------------------------------------"
else
    echo "❌ 报告生成失败"
    echo ""
    echo "查看日志排查问题:"
    echo "  python3 3_ai_security_check.py"
fi

# 清理备份
rm -f config.json.force_backup new_version.json

echo ""

