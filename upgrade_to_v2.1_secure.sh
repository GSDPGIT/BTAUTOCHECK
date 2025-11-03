#!/bin/bash
# ========================================
# BTAUTOCHECK V2.1 安全加固版 升级脚本
# ========================================

echo "========================================"
echo "🔒 BTAUTOCHECK V2.1 安全加固版升级"
echo "========================================"
echo ""
echo "本次升级包含以下安全修复："
echo "  ✅ 路径遍历漏洞修复"
echo "  ✅ bcrypt密码加密（替代SHA256）"
echo "  ✅ CSRF保护"
echo "  ✅ 速率限制（防暴力破解）"
echo "  ✅ 操作审计日志"
echo "  ✅ Session持久化"
echo "  ✅ Waitress生产服务器"
echo "  ✅ 异常处理完善"
echo ""
echo "⚠️  重要提示:"
echo "  1. 密码将被重置为默认密码（bcrypt加密）"
echo "  2. 登录后请立即修改密码（最少8位）"
echo "  3. 所有API Key和配置会保留"
echo ""

read -p "继续升级？(y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "❌ 已取消升级"
    exit 0
fi

# ========================================
# 步骤1: 备份
# ========================================
echo ""
echo "📦 步骤1: 备份当前版本..."

# 创建备份目录
BACKUP_DIR="backup_before_v2.1_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 备份关键文件
cp config.json "$BACKUP_DIR/" 2>/dev/null || echo "  ⚠️ config.json不存在"
cp .admin_password "$BACKUP_DIR/" 2>/dev/null || echo "  ℹ️ .admin_password不存在（将生成新的）"
cp .config.key "$BACKUP_DIR/" 2>/dev/null || echo "  ℹ️ .config.key不存在"
cp web_admin.py "$BACKUP_DIR/" 2>/dev/null || echo "  ⚠️ web_admin.py不存在"

echo "✅ 备份完成: $BACKUP_DIR"

# ========================================
# 步骤2: 停止服务
# ========================================
echo ""
echo "🛑 步骤2: 停止Web服务..."
pkill -f web_admin.py
sleep 2
echo "✅ 服务已停止"

# ========================================
# 步骤3: 更新代码
# ========================================
echo ""
echo "📥 步骤3: 从GitHub拉取最新代码..."

# 保存config.json
if [ -f config.json ]; then
    cp config.json config.json.upgrade_temp
fi

# 拉取代码
git fetch origin
git reset --hard origin/main

# 恢复config.json
if [ -f config.json.upgrade_temp ]; then
    cp config.json.upgrade_temp config.json
    rm config.json.upgrade_temp
fi

echo "✅ 代码已更新"

# ========================================
# 步骤4: 安装新依赖
# ========================================
echo ""
echo "📦 步骤4: 安装新依赖..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ 依赖安装成功"
else
    echo "❌ 依赖安装失败，请手动执行:"
    echo "   pip3 install -r requirements.txt"
    exit 1
fi

# ========================================
# 步骤5: 迁移密码到bcrypt
# ========================================
echo ""
echo "🔐 步骤5: 迁移密码到bcrypt格式..."

# 删除旧的SHA256密码（如果存在）
if [ -f .admin_password ]; then
    # 检查是否是SHA256格式（64个字符）
    password_hash=$(cat .admin_password)
    if [ ${#password_hash} -eq 64 ]; then
        echo "  ⚠️  检测到旧的SHA256密码"
        echo "  🔄 删除旧密码，将使用bcrypt重新生成"
        rm .admin_password
    else
        echo "  ℹ️  密码已是bcrypt格式，保留"
    fi
fi

# Python脚本会在启动时自动生成bcrypt默认密码

# ========================================
# 步骤6: 生成密钥文件
# ========================================
echo ""
echo "🔑 步骤6: 生成持久化密钥..."

python3 << 'EOF'
import os

# 生成secret_key
SECRET_KEY_FILE = '.secret_key'
if not os.path.exists(SECRET_KEY_FILE):
    key = os.urandom(24)
    with open(SECRET_KEY_FILE, 'wb') as f:
        f.write(key)
    os.chmod(SECRET_KEY_FILE, 0o600)
    print("✅ Session密钥已生成")
else:
    print("ℹ️  Session密钥已存在")

# 检查.config.key（API加密密钥）
if os.path.exists('.config.key'):
    print("ℹ️  API加密密钥已存在")
else:
    print("ℹ️  API加密密钥将在首次使用时生成")

print("✅ 密钥文件准备完成")
EOF

# ========================================
# 步骤7: 更新配置
# ========================================
echo ""
echo "⚙️ 步骤7: 更新配置文件..."

python3 << 'EOF'
import json

try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # 确保scheduler配置存在
    if 'scheduler' not in config:
        config['scheduler'] = {
            'enabled': True,
            'interval_hours': 1
        }
        print("✅ 已添加调度器配置（默认每1小时）")
    
    # 确保GitHub配置存在
    if 'github_username' not in config:
        config['github_username'] = ''
    if 'github_repo' not in config:
        config['github_repo'] = ''
    if 'github_token' not in config:
        config['github_token'] = ''
    if 'auto_upload' not in config:
        config['auto_upload'] = False
    
    # 保存更新后的配置
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    
    print("✅ 配置文件已更新")
    print(f"   调度器: {'启用' if config['scheduler']['enabled'] else '禁用'}")
    print(f"   检测间隔: {config['scheduler']['interval_hours']} 小时")
    
except Exception as e:
    print(f"⚠️ 配置更新失败: {e}")
    print("   请手动检查config.json")
EOF

# ========================================
# 步骤8: 启动新版本
# ========================================
echo ""
echo "🚀 步骤8: 启动Web服务..."
nohup python3 web_admin.py > web.log 2>&1 &
sleep 3

# 检查启动状态
if pgrep -f web_admin.py > /dev/null; then
    echo "✅ Web服务启动成功"
else
    echo "❌ Web服务启动失败"
    echo "   查看日志: tail -50 web.log"
    exit 1
fi

# ========================================
# 步骤9: 显示启动日志
# ========================================
echo ""
echo "📋 步骤9: 启动日志..."
echo "--------------------"
tail -20 web.log
echo "--------------------"

# ========================================
# 步骤10: 验证功能
# ========================================
echo ""
echo "========================================"
echo "✅ 升级完成！"
echo "========================================"
echo ""
echo "🌐 访问地址: http://$(hostname -I | awk '{print $1}'):5000"
echo "👤 默认账号: admin"
echo "🔑 默认密码: admin123"
echo ""
echo "⚠️  重要提示:"
echo "  1. 登录后立即修改密码（最少8位）"
echo "  2. 查看审计日志: cat logs/audit.log"
echo "  3. 配置GitHub上传: 配置管理 → GitHub上传配置"
echo "  4. 调整检测频率: 配置管理 → 自动检测调度器"
echo ""
echo "🔒 新增安全特性:"
echo "  ✅ bcrypt密码加密（防暴力破解）"
echo "  ✅ CSRF保护（防跨站请求伪造）"
echo "  ✅ 速率限制（防API滥用）"
echo "  ✅ 路径遍历防护（防文件泄露）"
echo "  ✅ 操作审计日志（logs/audit.log）"
echo "  ✅ Session持久化（重启不掉线）"
echo "  ✅ Waitress生产服务器（性能提升）"
echo ""
echo "📚 查看文档:"
echo "  cat CODE_AUDIT_REPORT.md  # 完整审计报告"
echo "  cat QUICK_FIX_GUIDE.md     # 快速修复指南"
echo ""
echo "🆘 遇到问题？"
echo "  1. 查看Web日志: tail -f web.log"
echo "  2. 查看审计日志: tail -f logs/audit.log"
echo "  3. 重新升级: bash upgrade_to_v2.1_secure.sh"
echo ""
echo "========================================"

