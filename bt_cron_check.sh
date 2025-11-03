#!/bin/bash
#================================================================
# BT-Panel 自动检测定时任务脚本
# 适用于宝塔面板计划任务
# 功能：每天自动检测BT面板新版本并进行安全分析
#================================================================

# 设置工作目录（请根据实际安装路径修改）
WORK_DIR="/root/BTAUTOCHECK"
LOG_DIR="${WORK_DIR}/logs"
LOG_FILE="${LOG_DIR}/auto_check_$(date +%Y%m%d).log"

# 创建日志目录
mkdir -p "${LOG_DIR}"

# 开始执行
echo "======================================================================" >> "${LOG_FILE}"
echo "BT-Panel 自动检测任务" >> "${LOG_FILE}"
echo "执行时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "${LOG_FILE}"
echo "======================================================================" >> "${LOG_FILE}"

# 切换到工作目录
cd "${WORK_DIR}" || {
    echo "❌ 错误：无法进入工作目录 ${WORK_DIR}" >> "${LOG_FILE}"
    exit 1
}

# 执行自动更新检测
echo "" >> "${LOG_FILE}"
echo "开始执行检测..." >> "${LOG_FILE}"
echo "" >> "${LOG_FILE}"

python3 auto_update.py >> "${LOG_FILE}" 2>&1
EXIT_CODE=$?

echo "" >> "${LOG_FILE}"
echo "======================================================================" >> "${LOG_FILE}"
echo "执行结果: $([ $EXIT_CODE -eq 0 ] && echo '✅ 成功' || echo '❌ 失败 (退出码: '$EXIT_CODE')')" >> "${LOG_FILE}"
echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "${LOG_FILE}"
echo "======================================================================" >> "${LOG_FILE}"
echo "" >> "${LOG_FILE}"

# 清理30天前的日志
find "${LOG_DIR}" -name "auto_check_*.log" -mtime +30 -delete 2>/dev/null

exit $EXIT_CODE

