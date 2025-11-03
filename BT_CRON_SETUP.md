# 🕐 BT Panel Cron Task Setup Guide
# 宝塔面板定时任务设置指南

## 📋 Setup Steps / 设置步骤

### Step 1: Prepare Script / 准备脚本

```bash
cd ~/BTAUTOCHECK
chmod +x bt_cron_check.sh

# Test the script / 测试脚本
bash bt_cron_check.sh

# Check log / 查看日志
cat logs/auto_check_$(date +%Y%m%d).log
```

### Step 2: Add Cron Task in BT Panel / 在宝塔面板添加计划任务

1. **Open BT Panel** / 打开宝塔面板
2. **Click "Cron"** / 点击"计划任务"
3. **Click "Add Task"** / 点击"添加任务"

**Task Settings / 任务设置**:

| Field / 字段 | Value / 值 |
|-------------|-----------|
| Task Type / 任务类型 | Shell Script / Shell脚本 |
| Task Name / 任务名称 | BT Panel Auto Check / BT面板版本自动检测 |
| Period / 执行周期 | Daily / 每天 |
| Time / 执行时间 | 03:00 / 凌晨3点 |
| Script / 脚本内容 | `/bin/bash /root/BTAUTOCHECK/bt_cron_check.sh` |

4. **Click "Add"** / 点击"添加"

### Step 3: Test Immediately / 立即测试

In BT Panel / 在宝塔面板中：
- Find the task / 找到任务
- Click "Run" / 点击"执行"
- Click "Log" after 2 mins / 2分钟后点击"日志"

---

## 📊 View Results / 查看结果

### Method 1: BT Panel Logs / 宝塔面板日志

Navigate to: Cron → Task Logs
路径：计划任务 → 日志

### Method 2: SSH Command / SSH命令

```bash
# View today's log / 查看今天的日志
cat ~/BTAUTOCHECK/logs/auto_check_$(date +%Y%m%d).log

# View all logs / 查看所有日志
ls -lht ~/BTAUTOCHECK/logs/

# View security report / 查看安全报告
ls -lt ~/BTAUTOCHECK/downloads/SECURITY_REPORT_*.md
```

---

## 🔔 Expected Output / 预期输出

### No New Version / 无新版本

```
======================================================================
BT-Panel 自动检测任务
执行时间: 2025-11-03 03:00:00
======================================================================

开始执行检测...

✅ 当前已是最新版本，无需更新

======================================================================
执行结果: ✅ 成功
完成时间: 2025-11-03 03:00:05
======================================================================
```

### New Version Found / 发现新版本

```
🎉 发现新版本: 11.3.0
   当前版本: 11.2.0
   
步骤1: 下载文件... ✅
步骤2: 安全分析... ✅
  安全评分: 82/100
步骤3: 生成报告... ✅
步骤4: 更新配置... ✅

执行结果: ✅ 成功
```

---

## ⚙️ Advanced Settings / 高级设置

### Change Frequency / 调整频率

**Every 12 hours / 每12小时**:
- Period: N Hours / N小时
- N = 12

**Weekly / 每周**:
- Period: Weekly / 每周
- Day: Monday / 星期一

### Change Time / 修改时间

Modify in BT Panel task settings
在宝塔面板任务设置中修改执行时间

---

## 🧹 Log Management / 日志管理

Logs older than 30 days are auto-deleted
超过30天的日志会自动清理

To change retention period, edit `bt_cron_check.sh`:
修改保留期限，编辑脚本最后一行：

```bash
-mtime +30  # Change to +7 (7 days) or +90 (90 days)
```

---

**Setup complete! / 设置完成！** 🎉

