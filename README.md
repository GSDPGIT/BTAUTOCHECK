# BTAUTOCHECK - BT-Panel 自动检测系统

> **Version**: V1.0  
> **Author**: Lee  
> **Purpose**: Automated BT-Panel version monitoring, security check & update system

[![Python](https://img.shields.io/badge/Python-3.6+-blue)]()
[![Gemini AI](https://img.shields.io/badge/AI-Gemini-orange)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

---

## 📖 简介

BTAUTOCHECK 是一个完全自动化的BT（宝塔）面板版本管理系统，集成AI安全分析能力。

### 🎯 核心功能

- 🔍 **自动版本检测** - 监控官方API，实时发现新版本
- 📥 **自动下载文件** - 从官方源下载升级包，计算MD5
- 🤖 **AI安全分析** - 使用Gemini AI进行深度代码审计
- 📝 **自动生成报告** - 生成专业的Markdown检测报告
- 📤 **自动更新上传** - 更新version.json并推送到GitHub
- ✅ **完整工作流** - 一键完成全流程

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/GSDPGIT/BTAUTOCHECK.git
cd BTAUTOCHECK
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置API Key

```bash
# 复制配置文件
cp config.example.json config.json

# 编辑config.json，填入你的Gemini API Key
vim config.json
```

**获取Gemini API Key**: https://aistudio.google.com/app/apikey

### 4. 测试运行（推荐首次使用）

```bash
# Linux服务器
bash test_full_flow.sh

# Windows
test_full_flow.bat
```

**测试脚本会**：
- ✅ 自动备份当前配置
- ✅ 模拟发现新版本11.2.0的完整流程
- ✅ 运行所有检测步骤（版本检测→下载→AI分析→生成报告）
- ✅ 自动恢复原始配置
- ✅ 显示生成的文件列表和测试结果

### 5. 正式运行

```bash
# 方式1: 一键运行全流程
python auto_update.py

# 方式2: Windows双击运行
run_auto_update.bat

# 方式3: 分步运行（调试用）
python 1_check_new_version.py
python 2_download_and_check.py
python 3_ai_security_check.py
python 4_generate_report.py
python 5_update_and_upload.py
```

---

## 📁 项目结构

```
BTAUTOCHECK/
├── auto_update.py              # 🎯 主控制脚本
├── 1_check_new_version.py      # 版本检测
├── 2_download_and_check.py     # 下载与检查
├── 3_ai_security_check.py      # AI安全分析
├── 4_generate_report.py        # 报告生成
├── 5_update_and_upload.py      # 更新上传
├── test_gemini.py              # API测试工具
├── test_full_flow.sh           # 🧪 完整流程测试（Linux）
├── test_full_flow.bat          # 🧪 完整流程测试（Windows）
├── config.json                 # 配置文件（需自己创建）
├── config.example.json         # 配置示例
├── requirements.txt            # Python依赖
├── run_auto_update.bat         # Windows快捷启动
├── .gitignore                  # Git忽略规则
├── README.md                   # 本文档
├── 快速开始.md                  # 快速入门指南
└── downloads/                  # 下载目录（自动生成）
```

---

## 🔧 配置说明

### config.json

```json
{
    "gemini_api_key": "YOUR_GEMINI_API_KEY_HERE",    // 必填：Gemini API密钥
    "github_username": "GSDPGIT",                     // GitHub用户名
    "github_repo": "bt-panel-files",                  // 面板文件仓库名
    "current_version": "11.2.0",                      // 当前版本
    "auto_upload": false,                             // 是否自动推送（建议false）
    "security_threshold": 95                          // 安全评分阈值
}
```

**重要参数**:

- `gemini_api_key`: **必填** - 从 https://aistudio.google.com/app/apikey 获取
- `auto_upload`: 建议设为 `false`，手动审查后再推送
- `security_threshold`: 低于此分数的版本需人工审查

---

## 🔍 工作流程

```
开始
  ↓
【步骤1】检测新版本
  - 调用官方API
  - 对比当前版本
  - 保存新版本信息
  ↓
【步骤2】下载并检查
  - 下载升级包
  - 计算MD5哈希
  - 验证ZIP完整性
  - 检查可疑文件
  ↓
【步骤3】AI安全分析
  - 解压文件
  - 提取关键代码
  - Gemini AI审计
  - 生成安全评分
  ↓
【步骤4】生成报告
  - Markdown格式
  - 包含所有检测结果
  ↓
【步骤5】更新上传
  - 更新version.json
  - 复制文件到仓库
  - Git提交
  - (可选)推送
  ↓
完成
```

---

## 🤖 AI安全检查

### 检查项目

使用Gemini AI检测：

- 🛡️ **后门风险** - 远程连接、命令执行、数据上传
- 🦠 **恶意代码** - 病毒、木马、挖矿程序
- 🔐 **隐私泄露** - 未授权的数据收集和上报
- 📢 **广告追踪** - 广告展示、用户行为追踪
- 🔓 **安全漏洞** - SQL注入、命令注入等

### 输出结果

- 安全评分（0-100分）
- 主要发现列表
- 使用建议
- 需要移除的内容
- 详细分析报告

---

## 📊 生成的文件

### 下载目录

```
downloads/
├── LinuxPanel-11.x.x.zip              # 下载的升级包
├── extracted_11.x.x/                  # 解压后的文件
├── new_version.json                   # 新版本信息
├── security_report_11.x.x.json        # JSON格式检测结果
└── SECURITY_REPORT_11.x.x.md          # Markdown检测报告
```

### 输出到面板仓库

自动复制到你的 `bt-panel-files` 仓库：
- `LinuxPanel-11.x.x.zip` - 升级包
- `version.json` - 更新后的版本信息
- `SECURITY_REPORT_11.x.x.md` - 检测报告

---

## ⚙️ 系统要求

- Python 3.6+
- requests库
- Gemini API Key（免费获取）
- 可访问Google AI和官方bt.cn

---

## 🛠️ 常见问题

### Q: 如何获取Gemini API Key？

**A**: 
1. 访问 https://aistudio.google.com/app/apikey
2. 使用Google账号登录
3. 点击"Create API Key"
4. 复制密钥到config.json

### Q: 是否会自动推送到GitHub？

**A**: 默认不会（`auto_upload: false`）。系统会：
1. 自动下载和检测
2. 生成报告
3. 更新文件
4. 等待你手动审查后推送

### Q: AI分析需要多长时间？

**A**: 
- 版本检测：5秒
- 下载文件：1-3分钟
- AI分析：10-30秒
- 总计：约2-5分钟

### Q: Gemini API是否免费？

**A**: 是的！Gemini提供免费的API配额，对于版本检测完全够用。

---

## 📝 使用示例

### 示例1: 手动检查更新

```bash
cd BTAUTOCHECK
python auto_update.py
```

### 示例2: 定时自动检查（Linux）

```bash
# 添加到crontab
crontab -e

# 每天凌晨2点检查
0 2 * * * cd /path/to/BTAUTOCHECK && python3 auto_update.py >> auto.log 2>&1
```

### 示例3: 仅测试API连接

```bash
python test_gemini.py
```

---

## 🔒 安全说明

### API Key安全

- ✅ `config.json` 已在 `.gitignore` 中
- ✅ API Key不会被上传到GitHub
- ✅ 使用 `config.example.json` 作为模板

### 数据隐私

- ✅ 所有检测在本地进行
- ✅ 仅检测结果发送给Gemini
- ✅ 不收集或上报用户数据

---

## 📚 相关资源

- **Gemini API**: https://ai.google.dev/docs
- **BT Panel官方**: https://www.bt.cn
- **面板纯净版**: https://github.com/GSDPGIT/bt-panel-files

---

## 📝 更新日志

### V1.0 (2025-11-02)

- ✅ 自动版本检测
- ✅ 自动下载文件
- ✅ AI安全分析（Gemini集成）
- ✅ 自动报告生成
- ✅ 自动更新上传
- ✅ 完整工作流

---

## 🙏 致谢

- **Google Gemini AI** - 提供免费的AI分析能力
- **BT Panel** - 优秀的服务器管理面板

---

## ⚖️ 免责声明

本项目仅供学习研究使用，请勿用于商业用途。使用本项目所产生的任何后果由使用者自行承担。

---

## 📞 联系方式

- **作者**: Lee
- **用途**: 仅供学习测试
- **License**: MIT

---

**Made with ❤️ and 🤖 AI**
