@echo off
chcp 65001 >nul
echo ========================================
echo   BT-Panel 自动更新系统
echo ========================================
echo.

cd /d "%~dp0"

echo 正在检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到Python，请先安装Python 3.6+
    pause
    exit /b 1
)

echo 正在检查依赖...
pip show requests >nul 2>&1
if %errorlevel% neq 0 (
    echo 安装依赖...
    pip install -r requirements.txt
)

echo.
echo ========================================
echo   开始自动更新流程
echo ========================================
echo.

python auto_update.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   ✅ 自动更新完成
    echo ========================================
    echo.
    echo 请查看生成的检测报告
    echo 如果通过检测，请手动推送到GitHub：
    echo   cd ..\security_analysis
    echo   git push origin main
) else (
    echo.
    echo ========================================
    echo   ⚠️ 自动更新遇到问题
    echo ========================================
    echo.
    echo 请查看上方错误信息
)

echo.
pause

