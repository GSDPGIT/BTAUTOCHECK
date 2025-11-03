#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
面板升级脚本（集成备份和回滚）
Panel Upgrade Script with Backup and Rollback
"""

import os
import sys
import json
import time
import shutil
import subprocess
from backup_manager import BackupManager
from notification import NotificationManager

def load_config():
    """加载配置"""
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def check_panel_status():
    """检查面板状态"""
    try:
        result = subprocess.run(['bt', 'status'], capture_output=True, text=True, timeout=10)
        return 'running' in result.stdout.lower()
    except subprocess.TimeoutExpired:
        print("⚠️ 检查面板状态超时")
        return False
    except Exception as e:
        print(f"⚠️ 检查面板状态失败: {e}")
        return False

def upgrade_panel(version_info):
    """
    升级面板
    
    Args:
        version_info: 版本信息字典
        
    Returns:
        成功返回True，失败返回False
    """
    print("=" * 70)
    print(f"🚀 升级BT-Panel到 {version_info['version']}")
    print("=" * 70)
    
    config = load_config()
    backup_manager = BackupManager()
    notif = NotificationManager()
    
    current_version = config.get('current_version', 'Unknown')
    new_version = version_info['version']
    upgrade_file = f"downloads/LinuxPanel-{new_version}.zip"
    
    backup_filepath = None
    
    try:
        # 1. 检查升级包是否存在
        if not os.path.exists(upgrade_file):
            print(f"❌ 升级包不存在: {upgrade_file}")
            return False
        
        print(f"✅ 升级包: {upgrade_file}")
        
        # 2. 创建备份（如果启用）
        if config.get('backup_before_upgrade', True):
            print("\n" + "=" * 70)
            print("步骤1: 创建备份")
            print("=" * 70)
            
            backup_filepath = backup_manager.create_backup(
                current_version,
                f"升级前备份 ({current_version} -> {new_version})"
            )
            
            if not backup_filepath:
                print("❌ 备份创建失败，终止升级")
                return False
            
            print(f"✅ 备份已创建: {backup_filepath}")
        
        # 3. 执行升级
        print("\n" + "=" * 70)
        print("步骤2: 执行升级")
        print("=" * 70)
        
        # 解压升级包
        print("📦 正在解压升级包...")
        shutil.unpack_archive(upgrade_file, '/tmp/bt_upgrade')
        
        # 运行升级脚本
        print("🔄 正在执行升级...")
        upgrade_script = '/tmp/bt_upgrade/install.sh'
        
        if os.path.exists(upgrade_script):
            result = subprocess.run(['bash', upgrade_script], 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise Exception(f"升级脚本执行失败: {result.stderr}")
        else:
            # 直接复制文件升级
            panel_path = '/www/server/panel'
            print(f"📁 正在更新文件到 {panel_path}...")
            
            for item in os.listdir('/tmp/bt_upgrade'):
                src = os.path.join('/tmp/bt_upgrade', item)
                dst = os.path.join(panel_path, item)
                
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
        
        # 清理临时文件
        shutil.rmtree('/tmp/bt_upgrade', ignore_errors=True)
        
        # 4. 重启面板
        print("\n" + "=" * 70)
        print("步骤3: 重启面板服务")
        print("=" * 70)
        
        print("🔄 正在重启面板...")
        os.system("bt restart")
        time.sleep(5)
        
        # 5. 验证升级是否成功
        print("\n" + "=" * 70)
        print("步骤4: 验证升级")
        print("=" * 70)
        
        print("🔍 检查面板状态...")
        if not check_panel_status():
            raise Exception("面板服务未正常运行")
        
        print("✅ 面板服务运行正常")
        
        # 6. 更新配置文件中的版本号
        config['current_version'] = new_version
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        print("\n" + "=" * 70)
        print(f"✅ 升级成功: {current_version} -> {new_version}")
        print("=" * 70)
        
        # 发送成功通知
        notif.notify_upgrade_success(new_version)
        
        return True
    
    except Exception as e:
        print(f"\n❌ 升级失败: {e}")
        
        # 自动回滚（如果启用）
        if config.get('auto_rollback_on_failure', True) and backup_filepath:
            print("\n" + "=" * 70)
            print("🔄 自动回滚")
            print("=" * 70)
            
            if backup_manager.restore_backup(backup_filepath):
                print("✅ 已回滚到升级前的版本")
                notif.notify_upgrade_failed(new_version, f"升级失败，已自动回滚: {str(e)}")
            else:
                print("❌ 回滚失败，请手动恢复")
                notif.notify_upgrade_failed(new_version, f"升级和回滚都失败: {str(e)}")
        else:
            notif.notify_upgrade_failed(new_version, str(e))
        
        return False

def main():
    """主函数"""
    # 读取版本信息
    if not os.path.exists('new_version.json'):
        print("❌ 未找到版本信息文件: new_version.json")
        print("   请先运行版本检测脚本")
        sys.exit(1)
    
    with open('new_version.json', 'r', encoding='utf-8') as f:
        version_info = json.load(f)
    
    success = upgrade_panel(version_info)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

