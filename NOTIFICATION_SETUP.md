# 📨 通知功能配置指南

BTAUTOCHECK 支持多种通知方式，让您第一时间了解新版本和安全检测结果。

---

## 📋 支持的通知方式

| 方式 | 说明 | 推荐场景 |
|------|------|----------|
| ✉️ 邮件 | SMTP邮件通知 | 企业用户、需要详细报告 |
| 🔗 Webhook | HTTP POST/GET请求 | 对接企业系统、自定义处理 |
| 📱 Server酱 | 微信推送（国内） | 个人用户、便捷查看 |
| 🔔 Bark | iOS推送 | iOS用户、即时通知 |
| 💬 Telegram | Telegram Bot推送 | 国际用户、隐私保护 |

---

## ⚙️ 配置方法

### 1️⃣ 邮件通知配置

```json
"email": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "your_email@gmail.com",
    "smtp_password": "your_app_password",
    "from_addr": "your_email@gmail.com",
    "to_addrs": ["admin@example.com", "team@example.com"],
    "use_tls": true
}
```

#### Gmail配置示例
1. 开启Gmail的"两步验证"
2. 生成"应用专用密码"：https://myaccount.google.com/apppasswords
3. 使用生成的密码填入`smtp_password`

#### QQ邮箱配置示例
```json
"smtp_server": "smtp.qq.com",
"smtp_port": 587,
"smtp_user": "your_qq@qq.com",
"smtp_password": "授权码",  // 从QQ邮箱获取授权码
"use_tls": true
```

#### 163邮箱配置示例
```json
"smtp_server": "smtp.163.com",
"smtp_port": 465,
"smtp_user": "your_email@163.com",
"smtp_password": "授权码",  // 从163邮箱获取授权码
"use_tls": false
```

---

### 2️⃣ Webhook通知配置

```json
"webhook": {
    "enabled": true,
    "url": "https://your-webhook-url.com/hook",
    "method": "POST",
    "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_TOKEN"
    }
}
```

#### 企业微信机器人
1. 在企业微信群聊中添加"群机器人"
2. 获取Webhook地址
3. 配置：
```json
"url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY",
"method": "POST"
```

#### 钉钉机器人
1. 在钉钉群聊中添加"自定义机器人"
2. 获取Webhook地址
3. 配置：
```json
"url": "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN",
"method": "POST"
```

#### 飞书机器人
1. 在飞书群聊中添加"自定义机器人"
2. 获取Webhook地址
3. 配置：
```json
"url": "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_TOKEN",
"method": "POST"
```

---

### 3️⃣ Server酱配置

```json
"serverchan": {
    "enabled": true,
    "sendkey": "YOUR_SERVERCHAN_SENDKEY"
}
```

#### 获取SendKey
1. 访问：https://sct.ftqq.com/
2. 使用微信登录
3. 在"SendKey"页面获取您的SendKey
4. 填入`sendkey`字段

**优点**：
- ✅ 免费使用
- ✅ 直接推送到微信
- ✅ 配置简单

---

### 4️⃣ Bark配置（iOS）

```json
"bark": {
    "enabled": true,
    "server": "https://api.day.app",
    "device_key": "YOUR_BARK_KEY"
}
```

#### 获取Device Key
1. App Store下载"Bark"应用
2. 打开应用，自动生成Device Key
3. 复制Key填入`device_key`字段

**优点**：
- ✅ iOS原生推送
- ✅ 即时送达
- ✅ 可自建服务器

---

### 5️⃣ Telegram配置

```json
"telegram": {
    "enabled": true,
    "bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
    "chat_id": "123456789"
}
```

#### 创建Telegram Bot
1. 在Telegram搜索 `@BotFather`
2. 发送 `/newbot` 创建机器人
3. 获取`bot_token`
4. 搜索 `@userinfobot` 获取您的`chat_id`
5. 填入配置

**优点**：
- ✅ 国际化
- ✅ 隐私保护
- ✅ 支持富文本

---

## 🧪 测试通知

配置完成后，运行测试命令：

```bash
cd ~/BTAUTOCHECK
python3 notification.py test
```

您将收到一条测试通知，确认配置正确。

---

## 📬 通知内容

### 新版本发现通知
```
🎉 发现新版本: 11.3.0

当前版本: 11.2.0
最新版本: 11.3.0
下载地址: https://...

系统将自动进行安全检测，请稍后查看检测报告。
```

### 安全检测通过通知
```
✅ 安全检测通过: 11.3.0

安全评分: 85/100
检测结果: ✅ 通过
状态: 可安全使用

详细报告已生成，请查看 SECURITY_REPORT_11.3.0.md
```

### 安全警告通知
```
⚠️ 安全警告: 11.3.0

安全评分: 65/100
检测结果: ⚠️ 未通过
状态: 需要人工审查

建议：请仔细查看安全报告后再决定是否升级！
详细报告: SECURITY_REPORT_11.3.0.md
```

### 检测失败通知
```
❌ 检测失败

错误信息: 网络连接超时

请检查：
1. 网络连接是否正常
2. API配置是否正确
3. 查看日志文件获取详细信息
```

---

## 🎯 推荐配置

### 方案一：轻量级（个人用户）
只启用Server酱，微信接收通知：
```json
"notifications": {
    "serverchan": {
        "enabled": true,
        "sendkey": "YOUR_KEY"
    }
}
```

### 方案二：标准版（小团队）
启用邮件+Server酱：
```json
"notifications": {
    "email": {
        "enabled": true,
        // ... 邮件配置
    },
    "serverchan": {
        "enabled": true,
        "sendkey": "YOUR_KEY"
    }
}
```

### 方案三：企业版（大团队）
启用邮件+Webhook+多渠道：
```json
"notifications": {
    "email": {
        "enabled": true,
        // ... 邮件配置
    },
    "webhook": {
        "enabled": true,
        // ... 企业微信/钉钉配置
    },
    "serverchan": {
        "enabled": true,
        "sendkey": "YOUR_KEY"
    }
}
```

---

## 🔧 高级配置

### 1. 仅在重要事件通知

修改`config.json`：
```json
"notification_enabled": true,  // 全局开关
```

修改`notification.py`，注释掉不需要的通知类型。

### 2. 自定义通知内容

编辑`notification.py`，修改通知模板：
```python
def notify_new_version(self, old_version, new_version, download_url):
    title = f"🎉 发现新版本: {new_version}"
    message = f"..."  # 自定义内容
```

### 3. 添加更多通知渠道

在`notification.py`中添加新的发送方法：
```python
def send_your_channel(self, title, message):
    # 实现您的通知逻辑
    pass
```

---

## ❓ 常见问题

### Q1: 邮件通知发送失败？
**A**: 
1. 检查SMTP服务器和端口是否正确
2. 确认使用"应用专用密码"而非登录密码
3. 检查防火墙是否拦截SMTP端口
4. 尝试切换TLS开关

### Q2: Server酱没有收到通知？
**A**: 
1. 确认SendKey正确无误
2. 检查Server酱配额（免费版有限制）
3. 访问Server酱网站查看发送日志

### Q3: 如何禁用所有通知？
**A**: 
在`config.json`中设置：
```json
"notification_enabled": false
```

### Q4: 可以只接收失败通知吗？
**A**: 
修改`notification.py`，在不需要的通知函数中添加：
```python
if level != "error":
    return
```

---

## ✅ 配置完成检查清单

- [ ] 已选择至少一种通知方式
- [ ] 已填写正确的配置信息
- [ ] 已运行测试命令验证
- [ ] 已收到测试通知
- [ ] 已了解通知内容格式
- [ ] 已设置宝塔定时任务

---

**配置完成！** 🎉

现在BTAUTOCHECK会在发现新版本或检测完成后自动通知您！

