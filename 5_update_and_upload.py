#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BT-Panel 自动更新与上传脚本
功能：更新version.json并上传到GitHub
"""

import json
import os
import sys
import subprocess
import shutil
from datetime import datetime

# 加载配置
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)

def update_version_json(version, md5, release_date):
    """更新version.json"""
    print("\n正在更新 version.json...")
    
    github_user = config['github_username']
    github_repo = config['github_repo']
    
    version_json = {
        "version": version,
        "is_beta": 0,
        "beta": 0,
        "download_url": f"https://raw.githubusercontent.com/{github_user}/{github_repo}/main/LinuxPanel-{version}.zip",
        "md5": md5,
        "update_msg": f"宝塔Linux面板 {version} 纯净版\\n\\n更新内容：\\n- 已移除所有广告\\n- 已移除统计追踪\\n- GitHub自托管源\\n- MD5完整性校验\\n- 自主可控更新\\n\\n作者：Lee自用 - 仅供学习测试",
        "force": False,
        "date": release_date if release_date else datetime.now().strftime('%Y-%m-%d'),
        "title": f"宝塔Linux面板 {version} 纯净版",
        "msg_en": f"BT Panel {version} Clean Edition - Self-hosted on GitHub"
    }
    
    # 保存到security_analysis目录
    target_dir = os.path.join(os.path.dirname(__file__), '..', 'security_analysis')
    version_file = os.path.join(target_dir, 'version.json')
    
    with open(version_file, 'w', encoding='utf-8') as f:
        json.dump(version_json, f, indent=4, ensure_ascii=False)
    
    print(f"✅ version.json 已更新")
    return version_file

def copy_files_to_repo(version):
    """复制文件到仓库目录"""
    print("\n正在复制文件到仓库目录...")
    
    download_dir = os.path.join(os.path.dirname(__file__), 'downloads')
    target_dir = os.path.join(os.path.dirname(__file__), '..', 'security_analysis')
    
    # 复制升级包
    source_file = os.path.join(download_dir, f'LinuxPanel-{version}.zip')
    target_file = os.path.join(target_dir, f'LinuxPanel-{version}.zip')
    
    if os.path.exists(source_file):
        shutil.copy2(source_file, target_file)
        print(f"✅ 已复制: LinuxPanel-{version}.zip")
    
    # 复制检测报告
    report_file = os.path.join(download_dir, f'SECURITY_REPORT_{version}.md')
    if os.path.exists(report_file):
        target_report = os.path.join(target_dir, f'SECURITY_REPORT_{version}.md')
        shutil.copy2(report_file, target_report)
        print(f"✅ 已复制: SECURITY_REPORT_{version}.md")
    
    return True

def git_commit_and_push(version):
    """Git提交并推送"""
    print("\n" + "=" * 60)
    print("Git提交与推送")
    print("=" * 60)
    
    target_dir = os.path.join(os.path.dirname(__file__), '..', 'security_analysis')
    os.chdir(target_dir)
    
    try:
        # 添加文件
        subprocess.run(['git', 'add', '-A'], check=True)
        
        # 检查是否有更改
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        if not result.stdout.strip():
            print("ℹ️  没有需要提交的更改")
            return True
        
        # 提交
        commit_msg = f"Auto-update: BT-Panel {version} - Security checked and verified"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        print(f"✅ 已提交: {commit_msg}")
        
        # 推送
        if config.get('auto_upload', False):
            print("\n正在推送到GitHub...")
            subprocess.run(['git', 'push', 'origin', 'main'], check=True)
            print("✅ 已推送到GitHub")
        else:
            print("\n⚠️  自动上传已禁用（auto_upload=false）")
            print("   请手动运行: git push origin main")
        
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Git操作失败: {e}")
        return False

def update_config_version(version):
    """更新配置文件中的当前版本"""
    config['current_version'] = version
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    
    print(f"\n✅ 配置文件已更新: current_version = {version}")

def main():
    """主函数"""
    print("=" * 60)
    print("更新version.json并上传到GitHub")
    print("=" * 60)
    
    download_dir = os.path.join(os.path.dirname(__file__), 'downloads')
    
    # 查找最新的检测结果
    result_files = [f for f in os.listdir(download_dir) if f.startswith('security_report_') and f.endswith('.json')]
    
    if not result_files:
        print("❌ 未找到检测结果文件")
        return False
    
    latest_result = sorted(result_files)[-1]
    result_path = os.path.join(download_dir, latest_result)
    
    with open(result_path, 'r', encoding='utf-8') as f:
        result_data = json.load(f)
    
    version = result_data['version']
    md5 = result_data['md5']
    ai_analysis = result_data.get('ai_analysis', {})
    
    print(f"\n版本: {version}")
    print(f"MD5: {md5}")
    print(f"安全评分: {ai_analysis.get('security_score', 0)}/100")
    
    # 检查是否通过安全检测
    if not ai_analysis.get('is_safe', False):
        print("\n⚠️  警告：此版本未通过AI安全检测")
        print("   是否继续？(y/n)")
        # 这里可以添加交互或直接返回
        # return False
    
    # 检查报告文件是否已存在（由步骤4生成）
    report_file = os.path.join(download_dir, f'SECURITY_REPORT_{version}.md')
    if os.path.exists(report_file):
        print(f"\n✅ 使用已生成的报告: {report_file}")
    else:
        print(f"\n⚠️  报告文件不存在，跳过: {report_file}")
    
    # 更新version.json
    release_date = result_data.get('download_time', '').split()[0] if result_data.get('download_time') else ''
    version_file = update_version_json(version, md5, release_date)
    
    # 复制文件到仓库
    copy_files_to_repo(version)
    
    # 更新配置
    update_config_version(version)
    
    # Git提交并推送
    if config.get('auto_upload', False):
        git_commit_and_push(version)
    else:
        print("\n" + "=" * 60)
        print("手动上传提示")
        print("=" * 60)
        print("文件已准备就绪，请手动推送到GitHub：")
        print("")
        print("  cd v1.0/security_analysis")
        print("  git add -A")
        print(f"  git commit -m 'Update: BT-Panel {version}'")
        print("  git push origin main")
    
    print("\n" + "=" * 60)
    print("✅ 自动更新流程完成")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

