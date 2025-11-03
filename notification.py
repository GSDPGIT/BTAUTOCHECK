#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知模块 - 支持多种通知方式
Notification Module - Multi-channel notification support
"""

import json
import os
import sys
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class NotificationManager:
    """通知管理器"""
    
    def __init__(self, config_file='config.json'):
        """初始化通知管理器"""
        self.config_file = config_file
        self.config = self.load_config()
        self.notification_config = self.config.get('notifications', {})
        
    def load_config(self):
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            print(f"❌ 配置文件不存在: {self.config_file}")
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载配置失败: {e}")
            return {}
    
    def send_all(self, title, message, level="info"):
        """
        发送通知到所有启用的渠道
        
        Args:
            title: 通知标题
            message: 通知内容
            level: 通知级别 (info/warning/error/success)
        """
        if not self.config.get('notification_enabled', False):
            print("ℹ️  通知功能已禁用")
            return
        
        success_count = 0
        fail_count = 0
        
        # 邮件通知
        if self.notification_config.get('email', {}).get('enabled'):
            if self.send_email(title, message):
                success_count += 1
            else:
                fail_count += 1
        
        # Webhook通知
        if self.notification_config.get('webhook', {}).get('enabled'):
            if self.send_webhook(title, message, level):
                success_count += 1
            else:
                fail_count += 1
        
        # Server酱通知
        if self.notification_config.get('serverchan', {}).get('enabled'):
            if self.send_serverchan(title, message):
                success_count += 1
            else:
                fail_count += 1
        
        # Bark通知
        if self.notification_config.get('bark', {}).get('enabled'):
            if self.send_bark(title, message):
                success_count += 1
            else:
                fail_count += 1
        
        # Telegram通知
        if self.notification_config.get('telegram', {}).get('enabled'):
            if self.send_telegram(title, message):
                success_count += 1
            else:
                fail_count += 1
        
        print(f"📨 通知发送完成: {success_count} 成功, {fail_count} 失败")
    
    def send_email(self, title, message):
        """发送邮件通知"""
        try:
            email_config = self.notification_config.get('email', {})
            
            msg = MIMEMultipart()
            msg['From'] = email_config.get('from_addr')
            msg['To'] = ', '.join(email_config.get('to_addrs', []))
            msg['Subject'] = f"[BTAUTOCHECK] {title}"
            
            body = f"""
<html>
<body>
<h2>{title}</h2>
<p>时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<hr>
<pre>{message}</pre>
<hr>
<p><small>此邮件由 BTAUTOCHECK 自动发送</small></p>
</body>
</html>
"""
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # 连接SMTP服务器
            if email_config.get('use_tls'):
                server = smtplib.SMTP(email_config.get('smtp_server'), 
                                     email_config.get('smtp_port', 587))
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(email_config.get('smtp_server'), 
                                         email_config.get('smtp_port', 465))
            
            server.login(email_config.get('smtp_user'), 
                        email_config.get('smtp_password'))
            server.send_message(msg)
            server.quit()
            
            print("✅ 邮件通知发送成功")
            return True
            
        except Exception as e:
            print(f"❌ 邮件通知发送失败: {e}")
            return False
    
    def send_webhook(self, title, message, level="info"):
        """发送Webhook通知"""
        try:
            webhook_config = self.notification_config.get('webhook', {})
            url = webhook_config.get('url')
            method = webhook_config.get('method', 'POST').upper()
            headers = webhook_config.get('headers', {'Content-Type': 'application/json'})
            
            # 构建通用格式
            data = {
                "title": title,
                "message": message,
                "level": level,
                "timestamp": datetime.now().isoformat(),
                "source": "BTAUTOCHECK"
            }
            
            if method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'GET':
                response = requests.get(url, params=data, headers=headers, timeout=10)
            else:
                print(f"❌ 不支持的HTTP方法: {method}")
                return False
            
            if response.status_code == 200:
                print("✅ Webhook通知发送成功")
                return True
            else:
                print(f"❌ Webhook通知失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Webhook通知发送失败: {e}")
            return False
    
    def send_serverchan(self, title, message):
        """发送Server酱通知"""
        try:
            sc_config = self.notification_config.get('serverchan', {})
            sendkey = sc_config.get('sendkey')
            
            if not sendkey:
                print("❌ Server酱 SendKey未配置")
                return False
            
            url = f"https://sctapi.ftqq.com/{sendkey}.send"
            data = {
                "title": f"[BTAUTOCHECK] {title}",
                "desp": message
            }
            
            response = requests.post(url, data=data, timeout=10)
            result = response.json()
            
            if result.get('code') == 0:
                print("✅ Server酱通知发送成功")
                return True
            else:
                print(f"❌ Server酱通知失败: {result.get('message')}")
                return False
                
        except Exception as e:
            print(f"❌ Server酱通知发送失败: {e}")
            return False
    
    def send_bark(self, title, message):
        """发送Bark通知"""
        try:
            bark_config = self.notification_config.get('bark', {})
            server = bark_config.get('server', 'https://api.day.app')
            device_key = bark_config.get('device_key')
            
            if not device_key:
                print("❌ Bark Device Key未配置")
                return False
            
            url = f"{server}/{device_key}/{title}/{message}"
            response = requests.get(url, timeout=10)
            result = response.json()
            
            if result.get('code') == 200:
                print("✅ Bark通知发送成功")
                return True
            else:
                print(f"❌ Bark通知失败: {result.get('message')}")
                return False
                
        except Exception as e:
            print(f"❌ Bark通知发送失败: {e}")
            return False
    
    def send_telegram(self, title, message):
        """发送Telegram通知"""
        try:
            tg_config = self.notification_config.get('telegram', {})
            bot_token = tg_config.get('bot_token')
            chat_id = tg_config.get('chat_id')
            
            if not bot_token or not chat_id:
                print("❌ Telegram配置不完整")
                return False
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            text = f"<b>{title}</b>\n\n{message}\n\n<i>来自 BTAUTOCHECK</i>"
            
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                print("✅ Telegram通知发送成功")
                return True
            else:
                print(f"❌ Telegram通知失败: {result.get('description')}")
                return False
                
        except Exception as e:
            print(f"❌ Telegram通知发送失败: {e}")
            return False
    
    def notify_new_version(self, old_version, new_version, download_url):
        """新版本发现通知"""
        title = f"🎉 发现新版本: {new_version}"
        message = f"""
发现BT-Panel新版本！

当前版本: {old_version}
最新版本: {new_version}
下载地址: {download_url}

系统将自动进行安全检测，请稍后查看检测报告。
"""
        self.send_all(title, message, level="info")
    
    def notify_security_check(self, version, score, is_safe):
        """安全检测完成通知"""
        if is_safe:
            title = f"✅ 安全检测通过: {version}"
            level = "success"
            message = f"""
版本 {version} 安全检测已完成

安全评分: {score}/100
检测结果: ✅ 通过
状态: 可安全使用

详细报告已生成，请查看 SECURITY_REPORT_{version}.md
"""
        else:
            title = f"⚠️ 安全警告: {version}"
            level = "warning"
            message = f"""
版本 {version} 安全检测已完成

安全评分: {score}/100
检测结果: ⚠️ 未通过
状态: 需要人工审查

建议：请仔细查看安全报告后再决定是否升级！
详细报告: SECURITY_REPORT_{version}.md
"""
        
        self.send_all(title, message, level=level)
    
    def notify_check_failed(self, error_msg):
        """检测失败通知"""
        title = "❌ 检测失败"
        message = f"""
BTAUTOCHECK 自动检测失败

错误信息: {error_msg}

请检查：
1. 网络连接是否正常
2. API配置是否正确
3. 查看日志文件获取详细信息
"""
        self.send_all(title, message, level="error")
    
    def notify_upgrade_success(self, version):
        """升级成功通知"""
        title = f"✅ 升级成功: {version}"
        message = f"""
BT-Panel 已成功升级到 {version}

升级时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
状态: 运行正常

系统已自动备份旧版本，如有问题可回滚。
"""
        self.send_all(title, message, level="success")
    
    def notify_upgrade_failed(self, version, error_msg):
        """升级失败通知"""
        title = f"❌ 升级失败: {version}"
        message = f"""
BT-Panel 升级到 {version} 失败

错误信息: {error_msg}

系统已自动回滚到之前的版本，面板运行正常。
"""
        self.send_all(title, message, level="error")


# 测试函数
def test_notification():
    """测试通知功能"""
    print("=" * 60)
    print("📨 通知功能测试")
    print("=" * 60)
    
    notif = NotificationManager()
    
    # 测试通知
    title = "测试通知"
    message = """
这是一条测试通知

如果您收到此通知，说明通知功能配置成功！

时间: {}
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    notif.send_all(title, message, level="info")
    
    print("=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_notification()
    else:
        print("用法: python3 notification.py test")

