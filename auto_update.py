#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BT-Panel 自动更新主控制脚本
功能：一键完成版本检测、下载、安全分析、报告生成、上传的全流程
"""

import subprocess
import sys
import os
from datetime import datetime

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
            return True
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
    
    # 步骤1: 检测新版本
    if not run_script('1_check_new_version.py', '检测新版本'):
        print("\n✅ 当前已是最新版本，无需更新")
        return True
    
    print("\n🎉 发现新版本，开始自动处理流程...")
    
    # 步骤2: 下载并基础检测
    if not run_script('2_download_and_check.py', '下载文件并基础检查'):
        print("\n❌ 下载或基础检查失败")
        return False
    
    # 步骤3: AI安全检测
    if not run_script('3_ai_security_check.py', 'AI安全分析'):
        print("\n⚠️  AI安全检测未完全通过，建议人工审查")
        print("   检测报告已生成，请查看后决定是否继续")
        
        # 询问是否继续
        print("\n是否继续生成报告？(y/n)")
        # 这里可以添加交互
        # return False
    
    # 步骤4: 生成检测报告
    if not run_script('4_generate_report.py', '生成安全检测报告'):
        print("\n❌ 报告生成失败")
        return False
    
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

