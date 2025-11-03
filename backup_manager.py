#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份和回滚管理器
Backup and Rollback Manager
"""

import os
import sys
import shutil
import json
import tarfile
import hashlib
from datetime import datetime
from pathlib import Path

class BackupManager:
    """备份管理器"""
    
    def __init__(self, panel_path='/www/server/panel', backup_path='backups'):
        """
        初始化备份管理器
        
        Args:
            panel_path: BT面板安装路径
            backup_path: 备份存储路径
        """
        self.panel_path = panel_path
        self.backup_path = backup_path
        self.backup_info_file = os.path.join(backup_path, 'backup_info.json')
        
        # 创建备份目录
        os.makedirs(backup_path, exist_ok=True)
    
    def create_backup(self, version, description=""):
        """
        创建面板备份
        
        Args:
            version: 当前面板版本
            description: 备份描述
            
        Returns:
            备份文件路径，失败返回None
        """
        print("=" * 70)
        print("📦 创建备份")
        print("=" * 70)
        
        if not os.path.exists(self.panel_path):
            print(f"❌ 面板路径不存在: {self.panel_path}")
            return None
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"panel_backup_{version}_{timestamp}.tar.gz"
        backup_filepath = os.path.join(self.backup_path, backup_filename)
        
        try:
            print(f"📁 备份目标: {self.panel_path}")
            print(f"💾 备份文件: {backup_filename}")
            
            # 计算备份前的磁盘空间
            total, used, free = shutil.disk_usage("/")
            print(f"💿 可用空间: {free // (2**30)} GB")
            
            # 创建tar.gz压缩备份
            print("🔄 正在压缩备份...")
            with tarfile.open(backup_filepath, "w:gz") as tar:
                tar.add(self.panel_path, arcname=os.path.basename(self.panel_path))
            
            # 计算备份文件大小和MD5
            backup_size = os.path.getsize(backup_filepath)
            backup_md5 = self._calculate_md5(backup_filepath)
            
            print(f"✅ 备份创建成功")
            print(f"📊 备份大小: {backup_size // (2**20)} MB")
            print(f"🔐 MD5校验: {backup_md5}")
            
            # 保存备份信息
            backup_info = {
                "version": version,
                "filename": backup_filename,
                "filepath": backup_filepath,
                "size": backup_size,
                "md5": backup_md5,
                "timestamp": timestamp,
                "description": description,
                "panel_path": self.panel_path,
                "created_at": datetime.now().isoformat()
            }
            
            self._save_backup_info(backup_info)
            
            # 清理旧备份（保留最近5个）
            self._cleanup_old_backups(keep=5)
            
            return backup_filepath
            
        except Exception as e:
            print(f"❌ 备份创建失败: {e}")
            if os.path.exists(backup_filepath):
                os.remove(backup_filepath)
            return None
    
    def restore_backup(self, backup_filepath=None, backup_version=None):
        """
        恢复备份
        
        Args:
            backup_filepath: 备份文件路径（优先）
            backup_version: 备份版本号（次选）
            
        Returns:
            成功返回True，失败返回False
        """
        print("=" * 70)
        print("📥 恢复备份")
        print("=" * 70)
        
        # 如果没有指定文件，尝试查找最新备份
        if not backup_filepath:
            if backup_version:
                backup_filepath = self._find_backup_by_version(backup_version)
            else:
                backup_filepath = self._get_latest_backup()
        
        if not backup_filepath or not os.path.exists(backup_filepath):
            print(f"❌ 备份文件不存在: {backup_filepath}")
            return False
        
        print(f"📁 备份文件: {backup_filepath}")
        
        try:
            # 验证备份文件完整性
            print("🔍 验证备份完整性...")
            if not self._verify_backup(backup_filepath):
                print("❌ 备份文件校验失败")
                return False
            
            # 创建当前面板的临时备份（以防万一）
            print("🔄 创建安全快照...")
            temp_backup = self.panel_path + "_temp_backup_" + datetime.now().strftime('%H%M%S')
            if os.path.exists(self.panel_path):
                shutil.move(self.panel_path, temp_backup)
            
            # 解压备份文件
            print("📦 正在恢复备份...")
            with tarfile.open(backup_filepath, "r:gz") as tar:
                tar.extractall(path=os.path.dirname(self.panel_path))
            
            print("✅ 备份恢复成功")
            
            # 删除临时备份
            if os.path.exists(temp_backup):
                shutil.rmtree(temp_backup)
                print("🧹 已清理临时文件")
            
            # 重启面板服务
            print("🔄 正在重启面板服务...")
            os.system("bt restart")
            
            print("=" * 70)
            print("✅ 回滚完成")
            print("=" * 70)
            
            return True
            
        except Exception as e:
            print(f"❌ 备份恢复失败: {e}")
            
            # 尝试恢复临时备份
            if 'temp_backup' in locals() and os.path.exists(temp_backup):
                print("🔄 正在恢复临时快照...")
                if os.path.exists(self.panel_path):
                    shutil.rmtree(self.panel_path)
                shutil.move(temp_backup, self.panel_path)
                print("✅ 已恢复到原始状态")
            
            return False
    
    def list_backups(self):
        """
        列出所有备份
        
        Returns:
            备份信息列表
        """
        if not os.path.exists(self.backup_info_file):
            return []
        
        try:
            with open(self.backup_info_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('backups', [])
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as e:
            print(f"⚠️ 备份信息文件格式错误: {e}")
            return []
        except Exception as e:
            print(f"⚠️ 读取备份信息失败: {e}")
            return []
    
    def _calculate_md5(self, filepath):
        """计算文件MD5"""
        md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        return md5.hexdigest()
    
    def _verify_backup(self, backup_filepath):
        """验证备份文件完整性"""
        try:
            # 验证文件可以正常打开
            with tarfile.open(backup_filepath, "r:gz") as tar:
                tar.getmembers()
            
            # 验证MD5（如果有记录）
            backups = self.list_backups()
            for backup in backups:
                if backup['filepath'] == backup_filepath:
                    saved_md5 = backup.get('md5')
                    if saved_md5:
                        current_md5 = self._calculate_md5(backup_filepath)
                        if current_md5 != saved_md5:
                            print(f"❌ MD5校验失败")
                            print(f"   期望: {saved_md5}")
                            print(f"   实际: {current_md5}")
                            return False
            
            return True
        except Exception as e:
            print(f"❌ 备份文件验证失败: {e}")
            return False
    
    def _save_backup_info(self, backup_info):
        """保存备份信息"""
        backups = []
        if os.path.exists(self.backup_info_file):
            try:
                with open(self.backup_info_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    backups = data.get('backups', [])
            except Exception as e:
                print(f"⚠️ 读取备份信息失败: {e}")
        
        backups.append(backup_info)
        
        with open(self.backup_info_file, 'w', encoding='utf-8') as f:
            json.dump({'backups': backups}, f, indent=2, ensure_ascii=False)
    
    def _get_latest_backup(self):
        """获取最新备份文件路径"""
        backups = self.list_backups()
        if not backups:
            return None
        
        # 按时间排序，返回最新的
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        return backups[0]['filepath']
    
    def _find_backup_by_version(self, version):
        """根据版本号查找备份"""
        backups = self.list_backups()
        for backup in backups:
            if backup['version'] == version:
                return backup['filepath']
        return None
    
    def _cleanup_old_backups(self, keep=5):
        """清理旧备份"""
        backups = self.list_backups()
        if len(backups) <= keep:
            return
        
        # 按时间排序
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        # 删除旧备份
        to_delete = backups[keep:]
        for backup in to_delete:
            try:
                if os.path.exists(backup['filepath']):
                    os.remove(backup['filepath'])
                    print(f"🧹 已删除旧备份: {backup['filename']}")
            except OSError as e:
                print(f"⚠️ 删除备份文件失败 {backup['filename']}: {e}")
            except Exception as e:
                print(f"⚠️ 删除备份异常: {e}")
        
        # 更新备份信息文件
        kept_backups = backups[:keep]
        with open(self.backup_info_file, 'w', encoding='utf-8') as f:
            json.dump({'backups': kept_backups}, f, indent=2, ensure_ascii=False)


def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='BT-Panel 备份和回滚工具')
    parser.add_argument('action', choices=['backup', 'restore', 'list'],
                       help='操作: backup(备份), restore(恢复), list(列表)')
    parser.add_argument('--version', help='面板版本号')
    parser.add_argument('--file', help='备份文件路径')
    parser.add_argument('--desc', default='', help='备份描述')
    
    args = parser.parse_args()
    
    manager = BackupManager()
    
    if args.action == 'backup':
        if not args.version:
            print("❌ 请指定版本号: --version 11.2.0")
            sys.exit(1)
        
        result = manager.create_backup(args.version, args.desc)
        sys.exit(0 if result else 1)
    
    elif args.action == 'restore':
        result = manager.restore_backup(args.file, args.version)
        sys.exit(0 if result else 1)
    
    elif args.action == 'list':
        print("=" * 70)
        print("📋 备份列表")
        print("=" * 70)
        
        backups = manager.list_backups()
        if not backups:
            print("暂无备份")
        else:
            for i, backup in enumerate(backups, 1):
                print(f"\n[{i}] {backup['filename']}")
                print(f"    版本: {backup['version']}")
                print(f"    大小: {backup['size'] // (2**20)} MB")
                print(f"    时间: {backup['created_at']}")
                if backup.get('description'):
                    print(f"    说明: {backup['description']}")
        
        print("=" * 70)


if __name__ == '__main__':
    main()

