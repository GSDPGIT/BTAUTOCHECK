#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BTAUTOCHECK Web管理系统
完整的Web管理界面
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from functools import wraps
import os
import json
import hashlib
import subprocess
import glob
from datetime import datetime
from secure_config import SecureConfig
from backup_manager import BackupManager
from notification import NotificationManager

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 配置
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = hashlib.sha256('admin123'.encode()).hexdigest()  # 默认密码：admin123

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if username == ADMIN_USERNAME and password_hash == ADMIN_PASSWORD_HASH:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """登出"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码"""
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证旧密码
        old_password_hash = hashlib.sha256(old_password.encode()).hexdigest()
        if old_password_hash != ADMIN_PASSWORD_HASH:
            return render_template('change_password.html', error='旧密码错误')
        
        # 验证新密码
        if len(new_password) < 6:
            return render_template('change_password.html', error='新密码长度至少6位')
        
        if new_password != confirm_password:
            return render_template('change_password.html', error='两次输入的新密码不一致')
        
        # 更新密码（写入配置文件）
        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        
        # 更新web_admin.py文件中的密码
        try:
            with open('web_admin.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换密码哈希
            content = content.replace(
                f"ADMIN_PASSWORD_HASH = '{ADMIN_PASSWORD_HASH}'",
                f"ADMIN_PASSWORD_HASH = '{new_password_hash}'"
            )
            
            with open('web_admin.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 同时保存到配置文件
            with open('.admin_password', 'w') as f:
                f.write(new_password_hash)
            
            return render_template('change_password.html', success='密码修改成功！请重新登录。', logout=True)
        
        except Exception as e:
            return render_template('change_password.html', error=f'密码修改失败: {str(e)}')
    
    return render_template('change_password.html')

@app.route('/')
@login_required
def dashboard():
    """仪表板"""
    # 读取配置
    secure_config = SecureConfig()
    config = secure_config.load_config()
    
    # 统计信息
    stats = {
        'current_version': config.get('current_version', 'Unknown'),
        'security_threshold': config.get('security_threshold', 80),
        'backup_count': len(BackupManager().list_backups()),
        'notification_enabled': config.get('notification_enabled', False)
    }
    
    # 最近的报告
    reports = get_recent_reports(5)
    
    # 最近的日志
    logs = get_recent_logs(10)
    
    return render_template('dashboard.html', stats=stats, reports=reports, logs=logs)

@app.route('/config', methods=['GET', 'POST'])
@login_required
def config_management():
    """配置管理"""
    secure_config = SecureConfig()
    
    if request.method == 'POST':
        # 更新配置
        config = secure_config.load_config()
        
        # 更新基础配置
        config['security_threshold'] = int(request.form.get('security_threshold', 80))
        config['notification_enabled'] = request.form.get('notification_enabled') == 'on'
        config['backup_enabled'] = request.form.get('backup_enabled') == 'on'
        config['backup_before_upgrade'] = request.form.get('backup_before_upgrade') == 'on'
        config['auto_rollback_on_failure'] = request.form.get('auto_rollback_on_failure') == 'on'
        config['keep_backups'] = int(request.form.get('keep_backups', 5))
        
        # 更新通知配置
        if 'serverchan_enabled' in request.form:
            config['notifications']['serverchan']['enabled'] = request.form.get('serverchan_enabled') == 'on'
            sendkey = request.form.get('serverchan_sendkey', '')
            if sendkey:
                config['notifications']['serverchan']['sendkey'] = sendkey
        
        # 保存配置
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        return jsonify({'success': True, 'message': '配置已保存'})
    
    config = secure_config.load_config()
    return render_template('config.html', config=config)

@app.route('/backups')
@login_required
def backup_list():
    """备份列表"""
    manager = BackupManager()
    backups = manager.list_backups()
    return render_template('backups.html', backups=backups)

@app.route('/backup/create', methods=['POST'])
@login_required
def backup_create():
    """创建备份"""
    version = request.form.get('version', 'manual')
    description = request.form.get('description', '手动备份')
    
    manager = BackupManager()
    result = manager.create_backup(version, description)
    
    if result:
        return jsonify({'success': True, 'message': '备份创建成功'})
    else:
        return jsonify({'success': False, 'message': '备份创建失败'})

@app.route('/backup/restore/<path:filepath>', methods=['POST'])
@login_required
def backup_restore(filepath):
    """恢复备份"""
    manager = BackupManager()
    result = manager.restore_backup(filepath)
    
    if result:
        return jsonify({'success': True, 'message': '备份恢复成功'})
    else:
        return jsonify({'success': False, 'message': '备份恢复失败'})

@app.route('/reports')
@login_required
def report_list():
    """报告列表"""
    reports = get_all_reports()
    return render_template('reports.html', reports=reports)

@app.route('/report/view/<filename>')
@login_required
def report_view(filename):
    """查看报告"""
    filepath = os.path.join('downloads', filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return render_template('report_view.html', filename=filename, content=content)
    else:
        return "报告不存在", 404

@app.route('/logs')
@login_required
def log_viewer():
    """日志查看器"""
    logs = get_all_logs()
    return render_template('logs.html', logs=logs)

@app.route('/logs/view/<filename>')
@login_required
def log_view(filename):
    """查看日志"""
    filepath = os.path.join('logs', filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'success': True, 'content': content})
    else:
        return jsonify({'success': False, 'message': '日志不存在'})

@app.route('/check/run', methods=['POST'])
@login_required
def run_check():
    """手动触发检测"""
    try:
        # 在后台运行检测
        subprocess.Popen(['python3', 'auto_update.py'], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE)
        return jsonify({'success': True, 'message': '检测已开始，请稍后查看结果'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'启动失败: {str(e)}'})

@app.route('/notification/test', methods=['POST'])
@login_required
def test_notification():
    """测试通知"""
    try:
        notif = NotificationManager()
        notif.send_all(
            "测试通知",
            "这是来自BTAUTOCHECK Web管理系统的测试通知。\n\n如果您收到此消息，说明通知功能配置正确！",
            level="info"
        )
        return jsonify({'success': True, 'message': '测试通知已发送'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'发送失败: {str(e)}'})

@app.route('/api/stats')
@login_required
def api_stats():
    """API：统计数据"""
    secure_config = SecureConfig()
    config = secure_config.load_config()
    
    # 获取检测历史
    reports = get_all_reports()
    
    # 构建统计数据
    stats = {
        'current_version': config.get('current_version', 'Unknown'),
        'total_reports': len(reports),
        'total_backups': len(BackupManager().list_backups()),
        'last_check': get_last_check_time(),
        'security_threshold': config.get('security_threshold', 80)
    }
    
    return jsonify(stats)

# 辅助函数

def get_recent_reports(limit=5):
    """获取最近的报告"""
    reports = []
    pattern = 'downloads/SECURITY_REPORT_*.md'
    files = glob.glob(pattern)
    files.sort(key=os.path.getmtime, reverse=True)
    
    for filepath in files[:limit]:
        filename = os.path.basename(filepath)
        reports.append({
            'filename': filename,
            'size': os.path.getsize(filepath),
            'mtime': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return reports

def get_all_reports():
    """获取所有报告"""
    reports = []
    pattern = 'downloads/SECURITY_REPORT_*.md'
    files = glob.glob(pattern)
    files.sort(key=os.path.getmtime, reverse=True)
    
    for filepath in files:
        filename = os.path.basename(filepath)
        reports.append({
            'filename': filename,
            'size': os.path.getsize(filepath),
            'mtime': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return reports

def get_recent_logs(limit=10):
    """获取最近的日志行"""
    logs = []
    today = datetime.now().strftime('%Y%m%d')
    log_file = f'logs/auto_check_{today}.log'
    
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            logs = [line.strip() for line in lines[-limit:]]
    
    return logs

def get_all_logs():
    """获取所有日志文件"""
    logs = []
    pattern = 'logs/auto_check_*.log'
    files = glob.glob(pattern)
    files.sort(key=os.path.getmtime, reverse=True)
    
    for filepath in files:
        filename = os.path.basename(filepath)
        logs.append({
            'filename': filename,
            'size': os.path.getsize(filepath),
            'mtime': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return logs

def get_last_check_time():
    """获取最后检测时间"""
    logs = get_all_logs()
    if logs:
        return logs[0]['mtime']
    return 'Never'

if __name__ == '__main__':
    # 确保必要的目录存在
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # 启动Web服务器
    print("=" * 70)
    print("🌐 BTAUTOCHECK Web管理系统")
    print("=" * 70)
    print(f"访问地址: http://0.0.0.0:5000")
    print(f"默认账号: {ADMIN_USERNAME}")
    print(f"默认密码: admin123")
    print(f"")
    print(f"⚠️  首次登录后请立即修改密码！")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=5000, debug=False)

