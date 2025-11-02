# 配置Gemini API Key到config.json

## 方法1: 使用sed命令（最简单）

```bash
cd ~/BTAUTOCHECK

# 一键替换API Key
sed -i 's/YOUR_GEMINI_API_KEY_HERE/AIzaSyAs1KJHmt69ZyXJKUdMKIxb0h0WFbaM0Dk/g' config.json

# 验证
cat config.json | grep gemini_api_key
```

## 方法2: 使用vim编辑器

```bash
vim config.json

# 找到这行:
#   "gemini_api_key": "YOUR_GEMINI_API_KEY_HERE",
# 
# 按 i 进入编辑模式
# 替换为:
#   "gemini_api_key": "AIzaSyAs1KJHmt69ZyXJKUdMKIxb0h0WFbaM0Dk",
#
# 按 ESC，然后输入 :wq 保存退出
```

## 方法3: 使用nano编辑器

```bash
nano config.json

# 找到并修改gemini_api_key那行
# Ctrl+X 保存退出
```

---

## 验证配置

```bash
cat config.json | grep gemini_api_key
```

**应该显示**:
```
    "gemini_api_key": "AIzaSyAs1KJHmt69ZyXJKUdMKIxb0h0WFbaM0Dk",
```

---

## 下一步: 安装依赖并运行

```bash
pip3 install -r requirements.txt
python3 auto_update.py
```

