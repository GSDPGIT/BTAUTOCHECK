# 🚀 BTAUTOCHECK 快速开始

> 5分钟配置，立即使用

---

## 第1步: 获取Gemini API Key

1. 访问：https://aistudio.google.com/app/apikey
2. 使用Google账号登录
3. 点击 **"Create API Key"**
4. 复制生成的API密钥

---

## 第2步: 配置系统

```bash
# 复制配置文件
cp config.example.json config.json

# 编辑配置文件
vim config.json  # 或使用任何文本编辑器
```

**填入你的API Key**:

```json
{
    "gemini_api_key": "你的API Key粘贴到这里"
}
```

---

## 第3步: 安装依赖

```bash
pip install -r requirements.txt
```

---

## 第4步: 运行

### Windows用户
```
双击: run_auto_update.bat
```

### Linux/Mac用户
```bash
python auto_update.py
```

---

## 第5步: 查看结果

```bash
# 查看检测报告
cat downloads/SECURITY_REPORT_*.md

# 如果安全检测通过，推送到面板仓库
cd /path/to/bt-panel-files
git push origin main
```

---

## ✅ 就这么简单！

**总耗时**: 约5分钟

**下次使用**: 只需运行 `python auto_update.py`

---

## 🔧 测试API连接

```bash
python test_gemini.py
```

**预期输出**:
```
✅ API连接成功！
✅ Gemini API配置正确，可以使用！
```

---

## 💡 高级用法

### 定时自动检查（Linux）

```bash
# 编辑crontab
crontab -e

# 每天凌晨2点自动检查
0 2 * * * cd /path/to/BTAUTOCHECK && python3 auto_update.py >> auto.log 2>&1
```

### 定时自动检查（Windows）

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器：每天
4. 操作：运行 `run_auto_update.bat`

---

**开始使用BTAUTOCHECK，让版本管理变得简单！** 🚀

