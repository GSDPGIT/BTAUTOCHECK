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
import re
import logging
from datetime import datetime
from secure_config import SecureConfig
from backup_manager import BackupManager
from notification import NotificationManager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from werkzeug.security import safe_join
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import bcrypt
import atexit

app = Flask(__name__)

# 配置
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_FILE = '.admin_password'
SECRET_KEY_FILE = '.secret_key'
AUDIT_LOG_FILE = 'logs/audit.log'

# ========================================
# 安全配置
# ========================================

def get_secret_key():
    """获取或生成持久化的secret key"""
    if os.path.exists(SECRET_KEY_FILE):
        try:
            with open(SECRET_KEY_FILE, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"读取secret key失败: {e}")
    
    # 生成新密钥
    key = os.urandom(24)
    try:
        with open(SECRET_KEY_FILE, 'wb') as f:
            f.write(key)
        os.chmod(SECRET_KEY_FILE, 0o600)
        print(f"✅ 已生成新的secret key")
    except Exception as e:
        print(f"保存secret key失败: {e}")
    
    return key

app.secret_key = get_secret_key()

# 初始化CSRF保护
csrf = CSRFProtect(app)

# 初始化速率限制
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)

# 初始化审计日志
os.makedirs('logs', exist_ok=True)
audit_logger = logging.getLogger('audit')
audit_handler = logging.FileHandler(AUDIT_LOG_FILE)
audit_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)

# 初始化调度器
scheduler = BackgroundScheduler(daemon=True)
scheduler.start()

# 确保程序退出时关闭调度器
atexit.register(lambda: scheduler.shutdown())

# ========================================
# 密码管理（bcrypt）
# ========================================

def get_admin_password_hash():
    """获取管理员密码哈希（bcrypt版本）"""
    if os.path.exists(ADMIN_PASSWORD_FILE):
        try:
            with open(ADMIN_PASSWORD_FILE, 'rb') as f:  # 二进制模式
                return f.read()
        except Exception as e:
            print(f"读取密码文件失败: {e}")
    
    # 默认密码：admin123（bcrypt哈希）
    default_hash = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt())
    
    # 保存默认密码
    try:
        with open(ADMIN_PASSWORD_FILE, 'wb') as f:
            f.write(default_hash)
        os.chmod(ADMIN_PASSWORD_FILE, 0o600)
        print(f"✅ 已生成默认密码（bcrypt）")
    except Exception as e:
        print(f"保存默认密码失败: {e}")
    
    return default_hash

def audit_log(action):
    """审计日志装饰器"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            username = session.get('username', 'anonymous')
            ip = request.remote_addr
            audit_logger.info(f"User:{username} IP:{ip} Action:{action}")
            return f(*args, **kwargs)
        return wrapped
    return decorator

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # 登录速率限制：每分钟最多10次
def login():
    """登录页面（bcrypt版本）"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            audit_logger.warning(f"IP:{request.remote_addr} 登录失败 - 缺少用户名或密码")
            return render_template('login.html', error='请输入用户名和密码')
        
        stored_hash = get_admin_password_hash()
        
        try:
            if username == ADMIN_USERNAME and bcrypt.checkpw(password.encode(), stored_hash):
                session['logged_in'] = True
                session['username'] = username
                audit_logger.info(f"User:{username} IP:{request.remote_addr} 登录成功")
                return redirect(url_for('dashboard'))
            else:
                audit_logger.warning(f"IP:{request.remote_addr} 登录失败 - 用户名或密码错误 (User:{username})")
                return render_template('login.html', error='用户名或密码错误')
        except Exception as e:
            audit_logger.error(f"IP:{request.remote_addr} 登录异常: {e}")
            return render_template('login.html', error='登录失败，请重试')
    
    return render_template('login.html')

@app.route('/logout')
@audit_log('登出')
def logout():
    """登出"""
    username = session.get('username', 'unknown')
    session.clear()
    audit_logger.info(f"User:{username} IP:{request.remote_addr} 登出")
    return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
@audit_log('修改密码')
def change_password():
    """修改密码（bcrypt版本）"""
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not old_password or not new_password or not confirm_password:
            return render_template('change_password.html', error='所有字段都必须填写')
        
        # 验证旧密码（bcrypt）
        stored_hash = get_admin_password_hash()
        try:
            if not bcrypt.checkpw(old_password.encode(), stored_hash):
                audit_logger.warning(f"User:{session.get('username')} IP:{request.remote_addr} 修改密码失败 - 旧密码错误")
                return render_template('change_password.html', error='旧密码错误')
        except Exception as e:
            audit_logger.error(f"密码验证异常: {e}")
            return render_template('change_password.html', error='密码验证失败')
        
        # 验证新密码强度
        if len(new_password) < 8:
            return render_template('change_password.html', error='新密码长度至少8位')
        
        if new_password != confirm_password:
            return render_template('change_password.html', error='两次输入的新密码不一致')
        
        # 生成新密码哈希（bcrypt）
        try:
            new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
            
            # 保存到密码文件（二进制模式）
            with open(ADMIN_PASSWORD_FILE, 'wb') as f:
                f.write(new_hash)
            
            os.chmod(ADMIN_PASSWORD_FILE, 0o600)
            
            audit_logger.info(f"User:{session.get('username')} IP:{request.remote_addr} 密码修改成功")
            return render_template('change_password.html', success='密码修改成功！请重新登录。', logout=True)
        
        except Exception as e:
            audit_logger.error(f"密码保存失败: {e}")
            return render_template('change_password.html', error='密码修改失败，请重试')
    
    return render_template('change_password.html')

@app.route('/')
@login_required
def dashboard():
    """仪表板"""
    # 读取配置
    secure_config = SecureConfig()
    config = secure_config.load_config()
    
    # 确保scheduler字段存在
    if 'scheduler' not in config:
        config['scheduler'] = {'enabled': True, 'interval_hours': 1}
    
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
@audit_log('配置管理')
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
        
        # 更新调度器配置
        if 'scheduler' not in config:
            config['scheduler'] = {}
        config['scheduler']['enabled'] = request.form.get('scheduler_enabled') == 'on'
        config['scheduler']['interval_hours'] = int(request.form.get('scheduler_interval', 1))
        
        # 更新GitHub配置
        config['auto_upload'] = request.form.get('auto_upload') == 'on'
        config['github_username'] = request.form.get('github_username', '')
        config['github_repo'] = request.form.get('github_repo', '')
        github_token = request.form.get('github_token', '')
        if github_token:
            config['github_token'] = github_token
        
        # 更新AI配置
        if 'ai_providers' not in config:
            config['ai_providers'] = {}
        
        config['ai_providers']['enabled'] = request.form.get('ai_enabled') == 'on'
        config['ai_providers']['primary_provider'] = request.form.get('primary_provider', 'gemini')
        config['ai_providers']['fallback_enabled'] = request.form.get('fallback_enabled') == 'on'
        
        # 更新各AI的配置
        ai_providers = ['gemini', 'openai', 'claude', 'qianwen', 'grok', 'wenxin', 'zhipu', 'deepseek', 'kimi', 'xunfei']
        for provider in ai_providers:
            if provider not in config['ai_providers']:
                config['ai_providers'][provider] = {}
            
            enabled_key = f'{provider}_enabled'
            apikey_key = f'{provider}_api_key'
            
            # 修复：复选框未勾选时也要保存false状态
            config['ai_providers'][provider]['enabled'] = request.form.get(enabled_key) == 'on'
            
            # 处理API Key
            apikey_value = request.form.get(apikey_key, '')
            if apikey_value and apikey_value.strip():
                config['ai_providers'][provider]['api_key'] = apikey_value.strip()
            
            # 特殊处理文心一言的secret_key
            if provider == 'wenxin':
                secret_key_value = request.form.get('wenxin_secret_key', '')
                if secret_key_value and secret_key_value.strip():
                    config['ai_providers']['wenxin']['secret_key'] = secret_key_value.strip()
            
            # 特殊处理讯飞星火的多个字段
            if provider == 'xunfei':
                app_id_value = request.form.get('xunfei_app_id', '')
                if app_id_value and app_id_value.strip():
                    config['ai_providers']['xunfei']['app_id'] = app_id_value.strip()
                
                api_secret_value = request.form.get('xunfei_api_secret', '')
                if api_secret_value and api_secret_value.strip():
                    config['ai_providers']['xunfei']['api_secret'] = api_secret_value.strip()
        
        # 更新通知配置
        if 'serverchan_enabled' in request.form:
            config['notifications']['serverchan']['enabled'] = request.form.get('serverchan_enabled') == 'on'
            sendkey = request.form.get('serverchan_sendkey', '')
            if sendkey:
                config['notifications']['serverchan']['sendkey'] = sendkey
        
        # 保存配置
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        # 如果调度器配置有变化，重新初始化
        init_scheduler()
        
        return jsonify({'success': True, 'message': '配置已保存，调度器已更新'})
    
    config = secure_config.load_config()
    
    # 确保所有必需的字段都存在（避免模板渲染错误）
    if 'scheduler' not in config:
        config['scheduler'] = {'enabled': True, 'interval_hours': 1}
    
    if 'github_username' not in config:
        config['github_username'] = ''
    
    if 'github_repo' not in config:
        config['github_repo'] = ''
    
    if 'github_token' not in config:
        config['github_token'] = ''
    
    if 'auto_upload' not in config:
        config['auto_upload'] = False
    
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
@limiter.limit("10 per hour")
@audit_log('创建备份')
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
@limiter.limit("5 per hour")
@audit_log('恢复备份')
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
@audit_log('查看报告')
def report_view(filename):
    """查看报告（安全版本）"""
    # 严格验证文件名格式
    if not re.match(r'^[A-Z_a-z]+_REPORT_[\d.]+\.md$', filename, re.IGNORECASE):
        audit_logger.warning(f"User:{session.get('username')} IP:{request.remote_addr} 尝试访问非法报告文件: {filename}")
        return "非法文件名", 400
    
    # 防止路径遍历
    if '..' in filename or '/' in filename or '\\' in filename:
        audit_logger.warning(f"User:{session.get('username')} IP:{request.remote_addr} 路径遍历尝试: {filename}")
        return "非法文件名", 400
    
    # 安全路径拼接
    try:
        filepath = safe_join('downloads', filename)
    except Exception as e:
        audit_logger.error(f"路径拼接失败: {e}")
        return "非法路径", 400
    
    if filepath is None or not os.path.exists(filepath):
        return "报告不存在", 404
    
    # 限制文件大小（防DoS）
    max_size = 10 * 1024 * 1024  # 10MB
    try:
        file_size = os.path.getsize(filepath)
        if file_size > max_size:
            audit_logger.warning(f"文件过大: {filepath} ({file_size} bytes)")
            return "文件过大", 413
    except Exception as e:
        audit_logger.error(f"获取文件大小失败: {e}")
        return "文件读取失败", 500
    
    # 确保文件在downloads目录内（双重检查）
    if not os.path.abspath(filepath).startswith(os.path.abspath('downloads')):
        audit_logger.critical(f"User:{session.get('username')} IP:{request.remote_addr} 尝试访问downloads外的文件: {filepath}")
        return "非法访问", 403
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return render_template('report_view.html', filename=filename, content=content)
    except Exception as e:
        audit_logger.error(f"读取报告失败 {filepath}: {e}")
        return "报告读取失败", 500

@app.route('/logs')
@login_required
def log_viewer():
    """日志查看器"""
    logs = get_all_logs()
    return render_template('logs.html', logs=logs)

@app.route('/logs/view/<filename>')
@login_required
@audit_log('查看日志')
def log_view(filename):
    """查看日志（安全版本）"""
    # 严格验证文件名格式（只允许auto_check_*.log和audit.log）
    if not re.match(r'^(auto_check_\d{8}\.log|audit\.log)$', filename):
        audit_logger.warning(f"User:{session.get('username')} IP:{request.remote_addr} 尝试访问非法日志文件: {filename}")
        return jsonify({'success': False, 'message': '非法文件名'}), 400
    
    # 防止路径遍历
    if '..' in filename or '/' in filename or '\\' in filename:
        audit_logger.warning(f"User:{session.get('username')} IP:{request.remote_addr} 日志路径遍历尝试: {filename}")
        return jsonify({'success': False, 'message': '非法文件名'}), 400
    
    # 安全路径拼接
    try:
        filepath = safe_join('logs', filename)
    except Exception as e:
        audit_logger.error(f"路径拼接失败: {e}")
        return jsonify({'success': False, 'message': '非法路径'}), 400
    
    if filepath is None or not os.path.exists(filepath):
        return jsonify({'success': False, 'message': '日志不存在'}), 404
    
    # 限制文件大小
    max_size = 5 * 1024 * 1024  # 5MB
    try:
        file_size = os.path.getsize(filepath)
        if file_size > max_size:
            audit_logger.warning(f"日志文件过大: {filepath} ({file_size} bytes)")
            return jsonify({'success': False, 'message': '日志文件过大'}), 413
    except Exception as e:
        audit_logger.error(f"获取文件大小失败: {e}")
        return jsonify({'success': False, 'message': '文件读取失败'}), 500
    
    # 确保文件在logs目录内
    if not os.path.abspath(filepath).startswith(os.path.abspath('logs')):
        audit_logger.critical(f"User:{session.get('username')} IP:{request.remote_addr} 尝试访问logs外的文件: {filepath}")
        return jsonify({'success': False, 'message': '非法访问'}), 403
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        audit_logger.error(f"读取日志失败 {filepath}: {e}")
        return jsonify({'success': False, 'message': '日志读取失败'}), 500

@app.route('/check/run', methods=['POST'])
@login_required
@limiter.limit("5 per hour")  # 速率限制：每小时最多5次
@audit_log('手动触发检测')
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
@limiter.limit("20 per hour")
@audit_log('测试通知')
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

@app.route('/ai/test', methods=['POST'])
@login_required
@limiter.limit("20 per hour")  # AI调用限制
@audit_log('测试AI')
def test_ai():
    """测试AI连接"""
    try:
        from ai_analyzer import AIAnalyzer
        
        analyzer = AIAnalyzer()
        
        # 测试代码
        test_code = """
def process_user_input(data):
    # 这是一个测试函数
    result = eval(data)
    return result
"""
        
        # 调用AI分析
        result = analyzer.analyze_code(test_code, "test.py")
        
        if result:
            provider = result.get('ai_provider', 'unknown')
            score = result.get('security_score', 0)
            findings = len(result.get('findings', []))
            
            message = f"✅ AI测试成功！\n\n"
            message += f"使用模型: {provider.upper()}\n"
            message += f"安全评分: {score}/100\n"
            message += f"发现问题: {findings}个\n\n"
            message += f"AI连接正常，可以使用！"
            
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': 'AI未返回结果，请检查配置和网络连接'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'AI测试失败: {str(e)}'})

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
    # 复用get_all_reports并限制数量
    all_reports = get_all_reports()
    return all_reports[:limit]

def get_all_reports():
    """获取所有报告"""
    reports = []
    # 使用不区分大小写的模式匹配
    patterns = [
        'downloads/SECURITY_REPORT_*.md',
        'downloads/Security_Report_*.md',
        'downloads/security_report_*.md'
    ]
    
    files_set = set()
    for pattern in patterns:
        files_set.update(glob.glob(pattern))
    
    files = list(files_set)
    files.sort(key=os.path.getmtime, reverse=True)
    
    for filepath in files:
        filename = os.path.basename(filepath)
        version = filename.replace('SECURITY_REPORT_', '').replace('Security_Report_', '').replace('security_report_', '').replace('.md', '')
        reports.append({
            'filename': filename,
            'version': version,
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

# ========================================
# 自动检测调度器功能
# ========================================

def run_auto_check():
    """执行自动检测任务"""
    try:
        print(f"\n{'='*70}")
        print(f"🔍 定时自动检测开始")
        print(f"⏰ 触发时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        # 运行auto_update.py
        result = subprocess.run(
            ['python3', 'auto_update.py'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__) or '.'
        )
        
        print(f"\n{'='*70}")
        print(f"✅ 定时自动检测完成")
        print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 退出码: {result.returncode}")
        print(f"{'='*70}\n")
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 定时检测失败: {e}")
        return False

def init_scheduler():
    """初始化调度器"""
    try:
        secure_config = SecureConfig()
        config = secure_config.load_config()
        
        scheduler_config = config.get('scheduler', {})
        enabled = scheduler_config.get('enabled', True)
        interval_hours = scheduler_config.get('interval_hours', 1)
        
        # 清除所有现有任务
        scheduler.remove_all_jobs()
        
        if enabled and interval_hours > 0:
            # 添加定时任务
            scheduler.add_job(
                func=run_auto_check,
                trigger=IntervalTrigger(hours=interval_hours),
                id='auto_check_job',
                name='自动版本检测任务',
                replace_existing=True
            )
            print(f"✅ 自动检测调度器已启动")
            print(f"⏰ 检测间隔: {interval_hours} 小时")
        else:
            print(f"⚠️  自动检测调度器已禁用")
            
    except Exception as e:
        print(f"❌ 调度器初始化失败: {e}")

@app.route('/scheduler/status')
@login_required
def scheduler_status():
    """获取调度器状态"""
    try:
        secure_config = SecureConfig()
        config = secure_config.load_config()
        scheduler_config = config.get('scheduler', {})
        
        jobs = []
        for job in scheduler.get_jobs():
            next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'N/A'
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': next_run,
                'trigger': str(job.trigger)
            })
        
        return jsonify({
            'success': True,
            'enabled': scheduler_config.get('enabled', True),
            'interval_hours': scheduler_config.get('interval_hours', 1),
            'jobs': jobs,
            'scheduler_running': scheduler.running
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/scheduler/toggle', methods=['POST'])
@login_required
@limiter.limit("30 per hour")
@audit_log('切换调度器')
def scheduler_toggle():
    """启用/禁用调度器"""
    try:
        enabled = request.json.get('enabled', True)
        interval_hours = request.json.get('interval_hours', 1)
        
        secure_config = SecureConfig()
        config = secure_config.load_config()
        
        if 'scheduler' not in config:
            config['scheduler'] = {}
        
        config['scheduler']['enabled'] = enabled
        config['scheduler']['interval_hours'] = interval_hours
        
        secure_config.save_config(config)
        
        # 重新初始化调度器
        init_scheduler()
        
        return jsonify({'success': True, 'message': '调度器配置已更新'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/scheduler/run_now', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
@audit_log('立即执行检测')
def scheduler_run_now():
    """立即执行检测"""
    try:
        # 在后台线程中执行
        import threading
        thread = threading.Thread(target=run_auto_check)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'message': '检测任务已启动，请稍后查看报告和日志'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/upload_to_github', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
@audit_log('上传到GitHub')
def upload_to_github():
    """手动上传报告到GitHub"""
    try:
        secure_config = SecureConfig()
        config = secure_config.load_config()
        
        # 检查GitHub配置
        if not config.get('github_username') or not config.get('github_repo') or not config.get('github_token'):
            return jsonify({'success': False, 'message': '请先配置GitHub信息（用户名、仓库名、Token）'})
        
        # 运行5_update_and_upload.py
        print(f"\n{'='*70}")
        print(f"📤 手动上传到GitHub")
        print(f"⏰ 触发时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        result = subprocess.run(
            ['python3', '5_update_and_upload.py'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__) or '.'
        )
        
        if result.returncode == 0:
            print(f"\n✅ 上传成功")
            return jsonify({'success': True, 'message': '✅ 报告已上传到GitHub'})
        else:
            print(f"\n❌ 上传失败: {result.stderr}")
            return jsonify({'success': False, 'message': f'上传失败: {result.stderr[:200]}'})
            
    except Exception as e:
        print(f"❌ 上传异常: {e}")
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    # 确保必要的目录存在
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('downloads', exist_ok=True)
    os.makedirs('backups', exist_ok=True)
    
    # 初始化调度器
    init_scheduler()
    
    # 启动Web服务器
    print("=" * 70)
    print("🌐 BTAUTOCHECK Web管理系统 V2.1 (Production)")
    print("=" * 70)
    print(f"🔐 安全特性:")
    print(f"   ✅ bcrypt密码加密")
    print(f"   ✅ CSRF保护")
    print(f"   ✅ 速率限制")
    print(f"   ✅ 路径遍历防护")
    print(f"   ✅ 操作审计日志")
    print(f"   ✅ Session持久化")
    print("=" * 70)
    print(f"📍 访问地址: http://0.0.0.0:5000")
    print(f"👤 默认账号: {ADMIN_USERNAME}")
    print(f"🔑 默认密码: admin123")
    print(f"")
    print(f"⚠️  首次登录后请立即修改密码（最少8位）！")
    print(f"📝 审计日志: {AUDIT_LOG_FILE}")
    print("=" * 70)
    
    # 使用Waitress生产服务器
    try:
        from waitress import serve
        print(f"🚀 使用Waitress生产服务器启动...")
        print(f"⏰ 自动检测调度器已启动")
        print("=" * 70)
        serve(app, host='0.0.0.0', port=5000, threads=6, channel_timeout=300)
    except ImportError:
        print(f"⚠️  Waitress未安装，使用Flask开发服务器（不推荐）")
        print(f"   建议: pip install waitress")
        print("=" * 70)
        app.run(host='0.0.0.0', port=5000, debug=False)

