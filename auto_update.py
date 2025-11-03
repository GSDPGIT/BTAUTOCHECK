#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BT-Panel 自动更新主控制脚本
功能：一键完成版本检测、下载、安全分析、报告生成、上传的全流程
"""

import subprocess
import sys
import os
import json
from datetime import datetime
from notification import NotificationManager

def run_script(script_name, description):
    """运行子脚本"""
    print("\n" + "=" * 70)
    print(f"步骤: {description}")
    print("=" * 70)
    
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - 完成")
            return True
        elif result.returncode == 1 and script_name == '1_check_new_version.py':
            # 检测到新版本（exit code 1表示有新版本）
            print(f"🎉 发现新版本！")
            return 'new_version'  # 返回特殊标记表示有新版本
        else:
            print(f"❌ {description} - 失败")
            return False
    
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 70)
    print(" BT-Panel 自动更新系统")
    print(" Automated Update & Security Check System")
    print("=" * 70)
    print(f" 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 初始化通知管理器
    notif = NotificationManager()
    
    # 步骤1: 检测新版本
    check_result = run_script('1_check_new_version.py', '检测新版本')
    if check_result == True:
        print("\n✅ 当前已是最新版本，无需更新")
        return True
    elif check_result == 'new_version':
        print("\n🎉 发现新版本，开始自动处理流程...")
        
        # 读取新版本信息并发送通知
        try:
            with open('new_version.json', 'r', encoding='utf-8') as f:
                version_info = json.load(f)
                old_version = version_info.get('current_version', 'Unknown')
                new_version = version_info.get('version', 'Unknown')
                download_url = version_info.get('download_url', 'Unknown')
                notif.notify_new_version(old_version, new_version, download_url)
        except Exception as e:
            print(f"⚠️  发送新版本通知失败: {e}")
    else:
        print("\n❌ 版本检测失败")
        notif.notify_check_failed("版本检测API返回错误")
        return False
    
    # 步骤2: 下载并基础检测
    if not run_script('2_download_and_check.py', '下载文件并基础检查'):
        print("\n❌ 下载或基础检查失败")
        notif.notify_check_failed("文件下载或基础检查失败")
        return False
    
    # 步骤3: AI安全检测
    security_check_passed = run_script('3_ai_security_check.py', 'AI安全分析')
    
    # 步骤4: 生成检测报告
    if not run_script('4_generate_report.py', '生成安全检测报告'):
        print("\n❌ 报告生成失败")
        notif.notify_check_failed("安全报告生成失败")
        return False
    
    # 读取安全检测结果并发送通知
    try:
        # 查找最新的检测报告
        import glob
        report_files = glob.glob('downloads/security_report_*.json')
        if report_files:
            latest_report = sorted(report_files)[-1]
            with open(latest_report, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
                version = report_data.get('version', 'Unknown')
                score = report_data.get('static_analysis', {}).get('security_score', 0)
                is_safe = report_data.get('static_analysis', {}).get('is_safe', False)
                notif.notify_security_check(version, score, is_safe)
    except Exception as e:
        print(f"⚠️  发送安全检测通知失败: {e}")
    
    if not security_check_passed:
        print("\n⚠️  安全检测未完全通过，建议人工审查")
        print("   检测报告已生成，请查看后决定是否继续")
    
    # 步骤5: 更新并上传
    if not run_script('5_update_and_upload.py', '更新version.json并准备上传'):
        print("\n❌ 更新失败")
        return False
    
    # 完成
    print("\n" + "=" * 70)
    print(" ✅ 自动更新流程完成")
    print("=" * 70)
    print(f" 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    print("\n📋 后续步骤：")
    print("1. 查看生成的检测报告")
    print("2. 如果安全检测通过，推送到GitHub：")
    print("   cd v1.0/security_analysis")
    print("   git push origin main")
    print("3. 在服务器上测试新版本")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

