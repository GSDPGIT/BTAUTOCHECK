@echo off
chcp 65001 >nul
REM BT-Panel 自动化系统完整流程测试脚本（Windows版本）

echo ======================================================================
echo  🧪 BTAUTOCHECK 完整流程测试
echo ======================================================================
echo.

REM 保存原始配置
echo 📦 备份原始配置...
copy config.json config.json.bak >nul

REM 修改当前版本为11.1.0（模拟旧版本）
echo 🔧 模拟旧版本环境（11.1.0 -^> 11.2.0）...
powershell -Command "(Get-Content config.json) -replace '\"current_version\": \"11.2.0\"', '\"current_version\": \"11.1.0\"' | Set-Content config.json"

echo.
echo ======================================================================
echo  🚀 开始测试完整流程...
echo ======================================================================
echo.

REM 运行自动更新
python auto_update.py

REM 保存退出码
set EXIT_CODE=%ERRORLEVEL%

echo.
echo ======================================================================
echo  🔄 恢复原始配置...
echo ======================================================================

REM 恢复原始配置
move /Y config.json.bak config.json >nul

echo.
echo ======================================================================
echo  📊 测试结果总结
echo ======================================================================
echo.

if %EXIT_CODE%==0 (
    echo ✅ 测试成功完成！
    echo.
    echo 📁 生成的文件：
    echo.
    
    REM 检查生成的文件
    if exist "new_version.json" echo   ✅ new_version.json - 版本信息
    if exist "downloads\LinuxPanel-11.2.0.zip" echo   ✅ LinuxPanel-11.2.0.zip - 下载的安装包
    if exist "reports\security_report_11.2.0.md" echo   ✅ security_report_11.2.0.md - 安全检测报告
    if exist "version.json" echo   ✅ version.json - 更新的版本配置
    
    echo.
    echo 📋 下一步操作：
    echo   1. 查看生成的安全检测报告
    echo   2. 如果检测通过，推送到GitHub：
    echo      git add .
    echo      git commit -m "Auto: Update to version 11.2.0"
    echo      git push origin main
) else (
    echo ❌ 测试过程中出现错误（退出码: %EXIT_CODE%）
    echo.
    echo 🔍 请检查：
    echo   - Gemini API Key是否配置正确
    echo   - 网络连接是否正常
    echo   - Python依赖是否安装完整
)

echo.
echo ======================================================================
pause

