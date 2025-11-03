# 🚀 BTAUTOCHECK - BT面板自动检测系统

> **Version**: V2.0 Complete Edition  
> **Author**: Lee自用  
> **Purpose**: 企业级BT面板自动监控、安全检测与管理系统

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![Security](https://img.shields.io/badge/Security-Static_Analysis-green.svg)](https://github.com/GSDPGIT/BTAUTOCHECK)
[![Web](https://img.shields.io/badge/Web-Flask-orange.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 简介

BTAUTOCHECK 是一个功能完整的BT（宝塔）面板自动化管理系统，提供：

- 🔍 **自动版本监控** - 每日自动检测新版本
- 🛡️ **安全深度分析** - 3407个文件全量静态代码扫描
- 📨 **多渠道通知** - 邮件/微信/Telegram实时推送
- 💾 **智能备份回滚** - 升级前自动备份，失败自动恢复
- 🌐 **Web管理界面** - 完整的可视化管理系统
- 🔐 **安全加密存储** - API Key加密保护

---

## ✨ 核心功能（V2.0 Complete）

### 🎯 自动化功能
| 功能 | 说明 | 状态 |
|------|------|------|
| 版本监控 | 自动检测bt.sb官方新版本 | ✅ 完成 |
| 文件下载 | 自动下载升级包并验证MD5 | ✅ 完成 |
| 安全分析 | 静态代码分析，11类风险检测 | ✅ 完成 |
| 报告生成 | 详细Markdown格式报告 | ✅ 完成 |
| 定时任务 | 宝塔面板集成，每日自动运行 | ✅ 完成 |

### 📨 通知系统
| 渠道 | 说明 | 配置难度 |
|------|------|----------|
| 邮件 | SMTP邮件通知 | ⭐⭐⭐ |
| Webhook | 企业微信/钉钉/飞书 | ⭐⭐ |
| Server酱 | 微信推送（推荐） | ⭐ |
| Bark | iOS推送 | ⭐ |
| Telegram | Telegram Bot | ⭐⭐ |

### 💾 备份系统
- ✅ 升级前自动备份
- ✅ MD5完整性验证
- ✅ 失败自动回滚
- ✅ 保留最近N个备份
- ✅ 一键恢复任意版本

### 🌐 Web管理界面
- 📊 **仪表板** - 实时统计和快速操作
- ⚙️ **配置管理** - 可视化配置所有选项
- 💾 **备份管理** - 创建/恢复/删除备份
- 📋 **安全报告** - 在线查看所有检测报告
- 📝 **系统日志** - 实时日志查看器
- 🔐 **密码管理** - 修改管理员密码

### 🔧 高级功能
- 🔐 API Key加密存储
- 📊 版本对比分析
- 🔍 多源文件验证
- 🐳 Docker容器化
- 📚 白名单规则库

---

## 🚀 快速开始

### 方式1: 一键安装（推荐）

```bash
curl -sSL https://raw.githubusercontent.com/GSDPGIT/BTAUTOCHECK/main/install.sh | bash
```

### 方式2: 手动安装

```bash
# 1. 克隆项目
git clone https://github.com/GSDPGIT/BTAUTOCHECK.git
cd BTAUTOCHECK

# 2. 安装依赖
pip3 install -r requirements.txt

# 3. 配置
cp config.example.json config.json
nano config.json  # 编辑配置

# 4. 启动Web管理系统
bash start_web.sh
```

---

## 🌐 Web管理系统

### 启动服务

```bash
cd ~/BTAUTOCHECK
bash start_web.sh
```

### 访问地址

```
http://您的服务器IP:5000
```

### 默认账号

- **用户名**: `admin`
- **密码**: `admin123`

⚠️ **首次登录后请立即修改密码！**

### 开放端口（如需远程访问）

**宝塔面板**：安全 → 添加端口 `5000`

**命令行**：
```bash
# firewalld
firewall-cmd --permanent --add-port=5000/tcp
firewall-cmd --reload

# ufw
ufw allow 5000/tcp
```

---

## 📅 定时任务配置

### 在宝塔面板添加

1. 进入 **计划任务** → **添加任务**
2. 填写信息：
   - 任务类型：`Shell脚本`
   - 任务名称：`BT面板版本自动检测`
   - 执行周期：`每天`
   - 执行时间：`03:00`
   - 脚本内容：`/bin/bash /root/BTAUTOCHECK/bt_cron_check.sh`
3. 点击 **添加** 保存

详细说明：查看 `BT_CRON_SETUP.md`

---

## 📊 安全分析

### 检测规则（11类）

| 类别 | 检测内容 | 严重程度 |
|------|----------|----------|
| 后门代码 | eval用户输入、动态代码执行 | 🔴 严重 |
| 命令执行 | os.system、subprocess | 🟡 中等 |
| 远程连接 | socket、urllib异常访问 | 🟡 中等 |
| 代码混淆 | base64、hex编码 | 🟠 警告 |
| 追踪广告 | 统计代码、广告链接 | 🟢 轻微 |
| 数据泄露 | 未授权数据上传 | 🔴 严重 |
| 可疑域名 | 非官方API请求 | 🟠 警告 |
| 文件传输 | FTP、SFTP操作 | 🟢 轻微 |
| SQL注入 | SQL拼接风险 | 🟡 中等 |
| 权限提升 | 修改系统关键文件 | 🔴 严重 |
| 危险函数 | unserialize、extract等 | 🟡 中等 |

### 评分标准

- **80-100分**: ✅ 安全可用
- **60-79分**: ⚠️ 需人工审查
- **0-59分**: ❌ 不建议使用

### 当前评分

**LinuxPanel-11.2.0**: `77/100` (已通过)

---

## 📁 项目结构

```
BTAUTOCHECK/
├── 🎯 核心脚本
│   ├── auto_update.py              # 主控制程序
│   ├── 1_check_new_version.py      # 版本检测
│   ├── 2_download_and_check.py     # 文件下载
│   ├── 3_ai_security_check.py      # 静态安全分析
│   ├── 4_generate_report.py        # 报告生成
│   ├── 5_update_and_upload.py      # 更新上传
│   ├── 6_upgrade_panel.py          # 面板升级
│   ├── 7_version_diff.py           # 版本对比
│   └── 8_multi_source_verify.py    # 多源验证
│
├── 🛠️ 管理工具
│   ├── web_admin.py                # Web管理系统
│   ├── notification.py             # 通知管理器
│   ├── backup_manager.py           # 备份管理器
│   └── secure_config.py            # 加密配置管理
│
├── 📄 配置文件
│   ├── config.json                 # 主配置（需创建）
│   ├── config.example.json         # 配置示例
│   ├── whitelist.json              # 安全白名单
│   └── requirements.txt            # Python依赖
│
├── 🚀 启动脚本
│   ├── install.sh                  # 一键安装
│   ├── start_web.sh                # 启动Web管理
│   ├── bt_cron_check.sh            # 定时任务脚本
│   ├── test_full_flow.sh           # 完整流程测试
│   └── Dockerfile                  # Docker支持
│
├── 📖 文档
│   ├── README.md                   # 本文档
│   ├── NOTIFICATION_SETUP.md       # 通知配置指南
│   ├── BACKUP_GUIDE.md             # 备份使用指南
│   └── BT_CRON_SETUP.md            # 定时任务指南
│
└── 🌐 Web界面
    └── templates/                  # HTML模板
        ├── base.html               # 基础模板
        ├── login.html              # 登录页面
        ├── dashboard.html          # 仪表板
        ├── config.html             # 配置管理
        ├── backups.html            # 备份管理
        ├── reports.html            # 报告列表
        ├── logs.html               # 日志查看
        └── change_password.html    # 密码修改
```

---

## 🔧 配置说明

### 基础配置

```json
{
    "current_version": "11.2.0",        // 当前面板版本
    "security_threshold": 80,           // 安全评分阈值
    "notification_enabled": true,       // 启用通知
    "backup_enabled": true,             // 启用备份
    "backup_before_upgrade": true,      // 升级前备份
    "auto_rollback_on_failure": true,   // 失败自动回滚
    "keep_backups": 5                   // 保留备份数量
}
```

### 通知配置

详见 `NOTIFICATION_SETUP.md`

---

## 📊 使用场景

### 场景1: 个人用户

```bash
# 配置Server酱（微信通知）
# 每天自动检测，发现新版本微信通知
```

**推荐配置**：
- ✅ Server酱通知
- ✅ 自动备份
- ✅ 定时任务

### 场景2: 小团队

```bash
# 邮件 + Server酱双通道
# Web界面查看历史报告
```

**推荐配置**：
- ✅ 邮件 + Server酱
- ✅ 自动备份回滚
- ✅ Web管理界面

### 场景3: 企业用户

```bash
# 企业微信 + 邮件 + 备份
# Docker部署，多源验证
```

**推荐配置**：
- ✅ 企业微信Webhook
- ✅ 邮件通知团队
- ✅ 完整备份策略
- ✅ Docker容器化

---

## 🛠️ 常用命令

### 管理命令

```bash
# 启动Web管理
bash start_web.sh

# 手动检测
python3 auto_update.py

# 查看日志
cat logs/auto_check_$(date +%Y%m%d).log

# 创建备份
python3 backup_manager.py backup --version 11.2.0

# 恢复备份
python3 backup_manager.py restore --version 11.2.0

# 测试通知
python3 notification.py test

# 版本对比
python3 7_version_diff.py downloads/extracted_11.2.0 downloads/extracted_11.3.0

# 多源验证
python3 8_multi_source_verify.py 11.2.0
```

### Docker命令

```bash
# 构建镜像
docker build -t btautocheck .

# 运行容器
docker run -d -p 5000:5000 -v $(pwd)/config.json:/app/config.json btautocheck

# 查看日志
docker logs -f <container_id>
```

---

## 📈 更新日志

### V2.0 Complete (2025-11-03)

**新增功能**:
1. ✅ 多渠道通知系统（邮件/Webhook/Server酱/Bark/Telegram）
2. ✅ 完整备份和回滚机制
3. ✅ 一键安装部署脚本
4. ✅ API Key加密存储
5. ✅ 版本差异对比分析
6. ✅ Web可视化管理界面
7. ✅ 增量文件分析
8. ✅ 多源文件验证
9. ✅ Docker容器化支持
10. ✅ 白名单规则库
11. ✅ 历史版本管理

**代码统计**:
- 新增代码：**3932行**
- Python模块：**13个**
- Web界面：**9个页面**
- 配置文档：**4份**

### V1.0 (2025-11-02)

- ✅ 基础版本检测
- ✅ AI安全分析
- ✅ 报告生成

---

## 🔒 安全特性

### 数据安全
- ✅ API Key加密存储（Fernet）
- ✅ 密码哈希存储（SHA256）
- ✅ 敏感文件权限控制（600）
- ✅ 配置文件自动忽略（.gitignore）

### 分析深度
- ✅ 3407个文件全量扫描
- ✅ 11类恶意模式检测
- ✅ 0个高危后门（11.2.0版本）
- ✅ 详细检测报告

### 升级安全
- ✅ 升级前自动备份
- ✅ 失败自动回滚
- ✅ 面板状态验证
- ✅ 完整性MD5校验

---

## 📚 文档索引

| 文档 | 说明 |
|------|------|
| [NOTIFICATION_SETUP.md](NOTIFICATION_SETUP.md) | 通知功能配置指南 |
| [BACKUP_GUIDE.md](BACKUP_GUIDE.md) | 备份和回滚使用指南 |
| [BT_CRON_SETUP.md](BT_CRON_SETUP.md) | 宝塔定时任务设置 |

---

## 💡 最佳实践

### 1. 首次使用

```bash
# 1. 安装系统
curl -sSL https://raw.githubusercontent.com/GSDPGIT/BTAUTOCHECK/main/install.sh | bash

# 2. 配置Server酱（推荐）
nano config.json  # 填入SendKey

# 3. 测试通知
python3 notification.py test

# 4. 添加定时任务
# 在宝塔面板添加（参考BT_CRON_SETUP.md）

# 5. 启动Web管理
bash start_web.sh
```

### 2. 日常使用

- 🔔 **接收通知** - 自动推送到微信
- 🌐 **查看报告** - Web界面查看
- 📊 **监控状态** - 定期检查日志

### 3. 发现新版本时

- 📨 **收到通知** - 微信推送新版本
- 📋 **查看报告** - Web界面查看安全评分
- ✅ **决定升级** - 评分≥80分可升级
- 💾 **自动备份** - 系统自动创建备份
- 🔄 **安全回滚** - 失败自动恢复

---

## 🆘 故障排查

### Web界面无法访问

```bash
# 检查服务是否运行
ps aux | grep web_admin

# 检查端口是否开放
netstat -tuln | grep 5000

# 查看日志
tail -f web.log
```

### 通知发送失败

```bash
# 测试通知
python3 notification.py test

# 检查配置
grep -A 5 "serverchan" config.json
```

### 定时任务未运行

```bash
# 查看日志
cat logs/auto_check_$(date +%Y%m%d).log

# 手动测试
bash bt_cron_check.sh
```

---

## 🎯 系统要求

- **操作系统**: Linux (CentOS/Ubuntu/Debian)
- **Python**: 3.7+
- **依赖库**: requests, cryptography, flask
- **磁盘空间**: 至少5GB（用于备份）
- **网络**: 可访问GitHub和bt.sb

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## ⚖️ 免责声明

本项目仅供学习研究使用，请勿用于商业用途。使用本项目所产生的任何后果由使用者自行承担。

---

## 📞 联系方式

- **作者**: Lee自用
- **GitHub**: https://github.com/GSDPGIT/BTAUTOCHECK
- **用途**: 仅供学习测试

---

**Made with ❤️ by Lee**
