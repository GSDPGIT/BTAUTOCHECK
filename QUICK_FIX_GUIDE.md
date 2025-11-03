# ⚡ BTAUTOCHECK 快速修复指南

> **针对**: CODE_AUDIT_REPORT.md中发现的严重问题  
> **优先级**: 🔴 极高  
> **预计时间**: 2-3小时

---

## 🎯 本指南包含

1. ✅ 修复路径遍历漏洞
2. ✅ 修复弱密码哈希
3. ✅ 修复Session密钥问题
4. ✅ 清理裸except块

**完成后安全性从 6/10 提升到 8/10**

---

## 🔒 修复1: 路径遍历漏洞（最严重）

### 修复方案

编辑 `web_admin.py`，找到 `report_view` 和 `log_view` 函数，替换为：

```python
from werkzeug.security import safe_join
import re

@app.route('/report/view/<filename>')
@login_required
def report_view(filename):
    """查看报告（安全版本）"""
    # 严格验证文件名格式
    if not re.match(r'^[A-Z_a-z]+_REPORT_[\d.]+\.md$', filename, re.IGNORECASE):
        return "非法文件名", 400
    
    # 防止路径遍历
    if '..' in filename or '/' in filename or '\\' in filename:
        return "非法文件名", 400
    
    # 安全路径拼接
    try:
        filepath = safe_join('downloads', filename)
    except:
        return "非法路径", 400
    
    if filepath is None or not os.path.exists(filepath):
        return "报告不存在", 404
    
    # 限制文件大小（防DoS）
    max_size = 10 * 1024 * 1024  # 10MB
    if os.path.getsize(filepath) > max_size:
        return "文件过大", 413
    
    # 确保文件在downloads目录内
    if not os.path.abspath(filepath).startswith(os.path.abspath('downloads')):
        return "非法访问", 403
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return render_template('report_view.html', filename=filename, content=content)


@app.route('/logs/view/<filename>')
@login_required
def log_view(filename):
    """查看日志（安全版本）"""
    # 严格验证文件名格式
    if not re.match(r'^auto_check_\d{8}\.log$', filename):
        return jsonify({'success': False, 'message': '非法文件名'}), 400
    
    # 防止路径遍历
    if '..' in filename or '/' in filename or '\\' in filename:
        return jsonify({'success': False, 'message': '非法文件名'}), 400
    
    # 安全路径拼接
    try:
        filepath = safe_join('logs', filename)
    except:
        return jsonify({'success': False, 'message': '非法路径'}), 400
    
    if filepath is None or not os.path.exists(filepath):
        return jsonify({'success': False, 'message': '日志不存在'}), 404
    
    # 限制文件大小
    max_size = 5 * 1024 * 1024  # 5MB
    if os.path.getsize(filepath) > max_size:
        return jsonify({'success': False, 'message': '日志文件过大'}), 413
    
    # 确保文件在logs目录内
    if not os.path.abspath(filepath).startswith(os.path.abspath('logs')):
        return jsonify({'success': False, 'message': '非法访问'}), 403
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return jsonify({'success': True, 'content': content})
```

**添加导入**（在文件顶部）:
```python
from werkzeug.security import safe_join
import re
```

---

## 🔐 修复2: 弱密码哈希

### 修复方案

编辑 `web_admin.py`，替换密码相关函数：

```python
import bcrypt

ADMIN_PASSWORD_FILE = '.admin_password'

def get_admin_password_hash():
    """获取管理员密码哈希（bcrypt版本）"""
    if os.path.exists(ADMIN_PASSWORD_FILE):
        try:
            with open(ADMIN_PASSWORD_FILE, 'rb') as f:  # 注意：二进制模式
                return f.read()
        except Exception as e:
            print(f"读取密码文件失败: {e}")
            pass
    
    # 默认密码：admin123
    default_hash = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt())
    
    # 保存默认密码
    try:
        with open(ADMIN_PASSWORD_FILE, 'wb') as f:
            f.write(default_hash)
        os.chmod(ADMIN_PASSWORD_FILE, 0o600)
    except:
        pass
    
    return default_hash


@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面（bcrypt版本）"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('login.html', error='请输入用户名和密码')
        
        stored_hash = get_admin_password_hash()
        
        try:
            if username == ADMIN_USERNAME and bcrypt.checkpw(password.encode(), stored_hash):
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error='用户名或密码错误')
        except Exception as e:
            print(f"密码验证失败: {e}")
            return render_template('login.html', error='登录失败，请重试')
    
    return render_template('login.html')


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码（bcrypt版本）"""
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not old_password or not new_password or not confirm_password:
            return render_template('change_password.html', error='所有字段都必须填写')
        
        # 验证旧密码
        stored_hash = get_admin_password_hash()
        try:
            if not bcrypt.checkpw(old_password.encode(), stored_hash):
                return render_template('change_password.html', error='旧密码错误')
        except Exception as e:
            return render_template('change_password.html', error='密码验证失败')
        
        # 验证新密码
        if len(new_password) < 8:  # 提高最小长度
            return render_template('change_password.html', error='新密码长度至少8位')
        
        if new_password != confirm_password:
            return render_template('change_password.html', error='两次输入的新密码不一致')
        
        # 生成新密码哈希
        try:
            new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
            
            # 保存到密码文件
            with open(ADMIN_PASSWORD_FILE, 'wb') as f:  # 二进制模式
                f.write(new_hash)
            
            os.chmod(ADMIN_PASSWORD_FILE, 0o600)
            
            return render_template('change_password.html', success='密码修改成功！请重新登录。', logout=True)
        except Exception as e:
            print(f"密码保存失败: {e}")
            return render_template('change_password.html', error=f'密码修改失败，请重试')
    
    return render_template('change_password.html')
```

**注意**: bcrypt已在requirements.txt中，无需额外安装

---

## 🔑 修复3: Session密钥持久化

### 修复方案

在 `web_admin.py` 开头添加：

```python
SECRET_KEY_FILE = '.secret_key'

def get_secret_key():
    """获取或生成持久化的secret key"""
    if os.path.exists(SECRET_KEY_FILE):
        try:
            with open(SECRET_KEY_FILE, 'rb') as f:
                return f.read()
        except:
            pass
    
    # 生成新密钥
    key = os.urandom(24)
    try:
        with open(SECRET_KEY_FILE, 'wb') as f:
            f.write(key)
        os.chmod(SECRET_KEY_FILE, 0o600)
    except:
        pass
    
    return key

# 使用
app.secret_key = get_secret_key()  # 替换 app.secret_key = os.urandom(24)
```

**同时更新 `.gitignore`**:
```
.secret_key
.admin_password
.config.key
```

---

## 🧹 修复4: 清理裸except块

### 修复示例

**修改前**:
```python
try:
    with open(file, 'r') as f:
        return f.read()
except:  # ❌ 捕获所有异常
    pass
```

**修改后**:
```python
try:
    with open(file, 'r') as f:
        return f.read()
except (IOError, OSError) as e:  # ✅ 明确异常类型
    print(f"文件读取失败 {file}: {e}")
    return None
except Exception as e:  # 捕获其他异常并记录
    print(f"未预期错误: {e}")
    return None
```

**需要修改的文件**:
- `web_admin.py` - 1处
- `3_ai_security_check.py` - 1处
- `6_upgrade_panel.py` - 1处
- `backup_manager.py` - 3处
- `7_version_diff.py` - 1处
- `1_check_new_version.py` - 1处

---

## 📝 快速修复脚本

创建 `quick_fix.sh`:

```bash
#!/bin/bash
# 快速安全修复脚本

echo "========================================"
echo "🔒 BTAUTOCHECK 安全快速修复"
echo "========================================"
echo ""

cd ~/BTAUTOCHECK

# 备份
echo "📦 备份原文件..."
cp web_admin.py web_admin.py.before_fix
cp .gitignore .gitignore.before_fix

# 修复.gitignore
echo "🔧 修复 .gitignore..."
if ! grep -q ".secret_key" .gitignore; then
    echo ".secret_key" >> .gitignore
    echo "✅ 已添加 .secret_key 到 .gitignore"
fi

# 生成secret_key
echo "🔑 生成持久化 secret_key..."
python3 << 'EOF'
import os
SECRET_KEY_FILE = '.secret_key'
if not os.path.exists(SECRET_KEY_FILE):
    key = os.urandom(24)
    with open(SECRET_KEY_FILE, 'wb') as f:
        f.write(key)
    os.chmod(SECRET_KEY_FILE, 0o600)
    print("✅ secret_key 已生成")
else:
    print("ℹ️  secret_key 已存在")
EOF

# 转换现有密码为bcrypt
echo "🔐 转换密码哈希为bcrypt..."
python3 << 'EOF'
import bcrypt
import hashlib
import os

ADMIN_PASSWORD_FILE = '.admin_password'

# 如果存在旧的SHA256密码
if os.path.exists(ADMIN_PASSWORD_FILE):
    with open(ADMIN_PASSWORD_FILE, 'r') as f:
        old_hash = f.read().strip()
    
    # 检查是否是SHA256格式（64个十六进制字符）
    if len(old_hash) == 64 and all(c in '0123456789abcdef' for c in old_hash.lower()):
        print("⚠️  检测到旧的SHA256密码哈希")
        print("   由于无法反向计算，将重置为默认密码: admin123")
        print("   ⚠️  登录后请立即修改密码！")
        
        # 使用默认密码生成bcrypt哈希
        new_hash = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt())
        with open(ADMIN_PASSWORD_FILE, 'wb') as f:
            f.write(new_hash)
        os.chmod(ADMIN_PASSWORD_FILE, 0o600)
        print("✅ 密码已重置为默认密码（bcrypt）")
    else:
        print("ℹ️  密码已是bcrypt格式或不存在")
else:
    # 生成默认密码
    default_hash = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt())
    with open(ADMIN_PASSWORD_FILE, 'wb') as f:
        f.write(default_hash)
    os.chmod(ADMIN_PASSWORD_FILE, 0o600)
    print("✅ 默认密码已生成（bcrypt）")
EOF

echo ""
echo "========================================"
echo "✅ 快速修复完成！"
echo "========================================"
echo ""
echo "⚠️  重要提示:"
echo "1. 密码已重置为默认密码: admin123"
echo "2. 登录后请立即修改密码！"
echo "3. 从GitHub拉取完整修复代码："
echo "   git pull origin main"
echo ""
echo "4. 重启Web服务："
echo "   pkill -f web_admin.py"
echo "   nohup python3 web_admin.py > web.log 2>&1 &"
echo ""
```

---

## 🚀 执行修复

在**Linux服务器**执行：

```bash
cd ~/BTAUTOCHECK

# 1. 拉取最新代码（包含审计报告）
git stash
git pull origin main
git stash pop

# 2. 运行快速修复（生成密钥文件）
chmod +x quick_fix.sh
bash quick_fix.sh

# 3. 重启Web服务
pkill -f web_admin.py
sleep 1
nohup python3 web_admin.py > web.log 2>&1 &

# 4. 验证
tail -20 web.log
```

---

## ⚠️ 重要说明

### 密码重置

由于SHA256到bcrypt无法直接转换，你的密码会被重置为默认值：

- **默认密码**: `admin123`
- **⚠️ 登录后立即修改！**

### 配置迁移

如果你的`config.json`没有以下字段，系统会自动添加默认值：

```json
{
  "scheduler": {
    "enabled": true,
    "interval_hours": 1
  },
  "github_username": "",
  "github_repo": "",
  "github_token": "",
  "auto_upload": false
}
```

---

## 📋 修复清单

完成以下步骤确保修复成功：

- [ ] 代码已从GitHub拉取最新版本
- [ ] 运行了quick_fix.sh（如果需要）
- [ ] Web服务已重启
- [ ] 能正常访问配置管理页面
- [ ] 能正常查看报告（测试路径遍历修复）
- [ ] 使用默认密码`admin123`能登录
- [ ] 修改密码功能正常
- [ ] Session在重启后仍然有效

---

## 🔍 验证修复效果

### 测试1: 路径遍历防护

尝试访问（应该被拒绝）:
```
http://你的IP:5000/report/view/../../../etc/passwd
http://你的IP:5000/report/view/..%2f..%2f..%2fetc%2fpasswd
```

应该返回 "非法文件名" 或 400错误。

### 测试2: 密码安全性

1. 查看密码文件：
```bash
cat .admin_password
# 应该看到乱码（bcrypt哈希）
# 而非64位十六进制（SHA256）
```

2. 修改密码后，`.admin_password`内容应该完全变化

### 测试3: Session持久化

1. 登录Web界面
2. 重启Web服务：`pkill -f web_admin.py && nohup python3 web_admin.py > web.log 2>&1 &`
3. 刷新浏览器
4. 应该仍然保持登录状态（不被踢出）

---

## 📞 遇到问题？

### 问题1: 密码重置后无法登录

**解决**: 
1. 确认使用默认密码 `admin123`
2. 检查 `.admin_password` 文件权限：`ls -la .admin_password`
3. 重新生成：`rm .admin_password && bash quick_fix.sh`

### 问题2: 配置管理仍然报错

**解决**:
1. 检查Web日志：`tail -50 web.log`
2. 确认代码已更新：`grep -n "确保所有必需的字段都存在" web_admin.py`
3. 强制更新：`git reset --hard origin/main`

### 问题3: Session仍然在重启后失效

**解决**:
1. 确认 `.secret_key` 文件存在：`ls -la .secret_key`
2. 确认代码使用了持久化密钥：`grep "get_secret_key" web_admin.py`

---

## 🎉 修复完成后

你的系统将获得：

✅ **防路径遍历** - 无法访问任意文件  
✅ **强密码哈希** - bcrypt加密，防暴力破解  
✅ **持久Session** - 重启不掉线  
✅ **更好的错误处理** - 明确的异常类型  

**安全性从 6/10 提升到 8/10！**

---

**下一步**: 查看 `CODE_AUDIT_REPORT.md` 了解更多优化建议

