#!/bin/bash
#================================================================
# BTAUTOCHECK 一键安装脚本
# One-Click Installation Script for BTAUTOCHECK
#================================================================

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
INSTALL_DIR="/root/BTAUTOCHECK"
GITHUB_REPO="https://github.com/GSDPGIT/BTAUTOCHECK.git"
GITHUB_RAW="https://raw.githubusercontent.com/GSDPGIT/BTAUTOCHECK/main"

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [ "$(id -u)" != "0" ]; then
        print_error "此脚本需要root权限运行"
        print_info "请使用: sudo bash install.sh"
        exit 1
    fi
}

# 检测系统类型
detect_system() {
    if [ -f /etc/redhat-release ]; then
        SYSTEM="centos"
        PM="yum"
    elif [ -f /etc/lsb-release ]; then
        SYSTEM="ubuntu"
        PM="apt"
    elif [ -f /etc/debian_version ]; then
        SYSTEM="debian"
        PM="apt"
    else
        print_warning "无法识别系统类型，假定为Debian系"
        SYSTEM="debian"
        PM="apt"
    fi
    
    print_info "检测到系统: $SYSTEM"
}

# 安装依赖
install_dependencies() {
    print_info "正在安装依赖..."
    
    if [ "$PM" == "yum" ]; then
        yum update -y
        yum install -y git python3 python3-pip
    else
        apt update
        apt install -y git python3 python3-pip
    fi
    
    # 安装Python依赖
    print_info "正在安装Python依赖..."
    pip3 install --upgrade pip
    pip3 install requests
    
    print_success "依赖安装完成"
}

# 下载BTAUTOCHECK
download_btautocheck() {
    print_info "正在下载BTAUTOCHECK..."
    
    # 如果目录已存在，先备份
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "检测到已存在的安装目录"
        BACKUP_DIR="${INSTALL_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
        mv "$INSTALL_DIR" "$BACKUP_DIR"
        print_info "已备份到: $BACKUP_DIR"
    fi
    
    # 尝试使用git克隆
    if command -v git &> /dev/null; then
        if git clone "$GITHUB_REPO" "$INSTALL_DIR"; then
            print_success "使用Git克隆成功"
            return 0
        else
            print_warning "Git克隆失败，尝试使用wget下载..."
        fi
    fi
    
    # Git失败，使用wget下载核心文件
    print_info "正在下载核心文件..."
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR" || exit 1
    
    # 下载核心脚本
    local files=(
        "config.example.json"
        "auto_update.py"
        "1_check_new_version.py"
        "2_download_and_check.py"
        "3_ai_security_check.py"
        "4_generate_report.py"
        "5_update_and_upload.py"
        "6_upgrade_panel.py"
        "notification.py"
        "backup_manager.py"
        "bt_cron_check.sh"
        "requirements.txt"
        "README.md"
    )
    
    for file in "${files[@]}"; do
        wget -q "${GITHUB_RAW}/${file}" -O "$file"
        if [ $? -ne 0 ]; then
            print_warning "下载 $file 失败"
        fi
    done
    
    print_success "核心文件下载完成"
}

# 配置BTAUTOCHECK
configure_btautocheck() {
    print_info "正在配置BTAUTOCHECK..."
    
    cd "$INSTALL_DIR" || exit 1
    
    # 复制配置文件
    if [ ! -f "config.json" ]; then
        cp config.example.json config.json
        print_info "已创建配置文件: config.json"
    else
        print_warning "config.json已存在，跳过"
    fi
    
    # 创建必要的目录
    mkdir -p logs downloads backups
    
    # 设置权限
    chmod +x *.sh
    chmod +x *.py
    
    print_success "配置完成"
}

# 交互式配置
interactive_config() {
    print_info "开始交互式配置..."
    echo ""
    
    # GitHub用户名
    read -p "请输入您的GitHub用户名 [默认: GSDPGIT]: " github_username
    github_username=${github_username:-GSDPGIT}
    
    # 通知配置
    echo ""
    print_info "通知配置（可跳过，后续在config.json中配置）"
    read -p "是否配置Server酱通知？(y/n) [默认: n]: " use_serverchan
    
    if [ "$use_serverchan" == "y" ]; then
        read -p "请输入Server酱SendKey: " serverchan_key
        
        # 更新配置文件
        sed -i "s/\"github_username\": \".*\"/\"github_username\": \"$github_username\"/" config.json
        sed -i "s/\"enabled\": false/\"enabled\": true/" config.json
        sed -i "s/YOUR_SERVERCHAN_SENDKEY/$serverchan_key/" config.json
        
        print_success "Server酱配置已保存"
    else
        sed -i "s/\"github_username\": \".*\"/\"github_username\": \"$github_username\"/" config.json
    fi
    
    print_success "交互式配置完成"
}

# 测试运行
test_run() {
    print_info "正在测试运行..."
    
    cd "$INSTALL_DIR" || exit 1
    
    # 测试Python环境
    if ! python3 --version &> /dev/null; then
        print_error "Python3未正确安装"
        return 1
    fi
    
    # 测试依赖
    if ! python3 -c "import requests" &> /dev/null; then
        print_error "Python requests模块未安装"
        return 1
    fi
    
    # 运行测试
    print_info "执行版本检测测试..."
    python3 1_check_new_version.py
    
    if [ $? -eq 0 ]; then
        print_success "测试运行成功"
        return 0
    else
        print_warning "测试运行有警告，但可能正常（如API访问失败）"
        return 0
    fi
}

# 添加到宝塔定时任务
add_to_bt_cron() {
    print_info "是否添加到宝塔面板定时任务？"
    echo ""
    echo "  如果您使用宝塔面板，建议添加定时任务实现自动检测"
    echo "  任务将每天凌晨3点自动检测新版本"
    echo ""
    read -p "是否添加？(y/n) [默认: y]: " add_cron
    add_cron=${add_cron:-y}
    
    if [ "$add_cron" == "y" ]; then
        echo ""
        print_info "请在宝塔面板中手动添加计划任务："
        echo ""
        echo "  1. 登录宝塔面板"
        echo "  2. 进入 计划任务"
        echo "  3. 添加Shell脚本任务"
        echo "  4. 填写以下信息："
        echo ""
        echo "     任务名称: BT面板版本自动检测"
        echo "     执行周期: 每天"
        echo "     执行时间: 03:00"
        echo "     脚本内容: /bin/bash ${INSTALL_DIR}/bt_cron_check.sh"
        echo ""
        print_warning "添加后请点击'执行'测试是否正常运行"
    fi
}

# 显示完成信息
show_completion() {
    echo ""
    echo "======================================================================"
    print_success "BTAUTOCHECK 安装完成！"
    echo "======================================================================"
    echo ""
    echo "📁 安装目录: ${INSTALL_DIR}"
    echo ""
    echo "📋 后续步骤："
    echo ""
    echo "1. 配置通知（可选）"
    echo "   cd ${INSTALL_DIR}"
    echo "   nano config.json"
    echo ""
    echo "2. 测试通知功能"
    echo "   python3 notification.py test"
    echo ""
    echo "3. 手动测试检测"
    echo "   python3 auto_update.py"
    echo ""
    echo "4. 添加到宝塔定时任务（推荐）"
    echo "   - 任务类型: Shell脚本"
    echo "   - 执行周期: 每天 03:00"
    echo "   - 脚本内容: /bin/bash ${INSTALL_DIR}/bt_cron_check.sh"
    echo ""
    echo "📖 更多文档："
    echo "   - 通知配置: ${INSTALL_DIR}/NOTIFICATION_SETUP.md"
    echo "   - 备份指南: ${INSTALL_DIR}/BACKUP_GUIDE.md"
    echo "   - 定时任务: ${INSTALL_DIR}/BT_CRON_SETUP.md"
    echo ""
    echo "======================================================================"
}

# 主函数
main() {
    echo "======================================================================"
    echo "  BTAUTOCHECK 一键安装脚本"
    echo "  BT-Panel Auto-Check Installation Script"
    echo "======================================================================"
    echo ""
    
    # 检查root权限
    check_root
    
    # 检测系统
    detect_system
    
    # 安装依赖
    install_dependencies
    
    # 下载BTAUTOCHECK
    download_btautocheck
    
    # 配置
    configure_btautocheck
    
    # 交互式配置
    interactive_config
    
    # 测试运行
    test_run
    
    # 添加到宝塔定时任务
    add_to_bt_cron
    
    # 显示完成信息
    show_completion
}

# 运行主函数
main

