#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BT-Panel 版本检测脚本
功能：检测bt.cn官方是否发布新版本
"""

import requests
import json
import os
import sys
from datetime import datetime

# 加载配置
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)

def get_official_version():
    """从官方API获取最新版本信息"""
    try:
        url = config['bt_api_url']
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if isinstance(data, dict):
            version = data.get('version', '')
            download_url = data.get('download', '')
            update_msg = data.get('update_msg', '')
            release_date = data.get('addtime', '')
            
            return {
                'version': version,
                'download_url': download_url if download_url else f"{config['bt_download_base']}/LinuxPanel-{version}.zip",
                'update_msg': update_msg,
                'release_date': release_date,
                'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            # 如果返回的是字符串格式的版本号
            version = str(data).strip()
            return {
                'version': version,
                'download_url': f"{config['bt_download_base']}/LinuxPanel-{version}.zip",
                'update_msg': '',
                'release_date': '',
                'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    except Exception as e:
        print(f"❌ 获取官方版本失败: {e}")
        return None

def check_new_version():
    """检查是否有新版本"""
    print("=" * 60)
    print("BT-Panel 版本检测")
    print("=" * 60)
    
    current_version = config['current_version']
    print(f"当前版本: {current_version}")
    
    print("\n正在检查官方最新版本...")
    official_info = get_official_version()
    
    if not official_info:
        print("❌ 无法获取官方版本信息")
        return None
    
    official_version = official_info['version']
    print(f"官方最新版本: {official_version}")
    
    # 比较版本
    if official_version != current_version:
        print(f"\n🎉 发现新版本: {official_version}")
        print(f"   当前版本: {current_version}")
        print(f"   下载地址: {official_info['download_url']}")
        if official_info['update_msg']:
            print(f"   更新说明: {official_info['update_msg'][:100]}...")
        
        # 保存新版本信息
        result_file = os.path.join(os.path.dirname(__file__), 'new_version.json')
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(official_info, f, indent=4, ensure_ascii=False)
        
        print(f"\n✅ 新版本信息已保存到: {result_file}")
        return official_info
    else:
        print("\n✅ 当前已是最新版本")
        return None

if __name__ == '__main__':
    result = check_new_version()
    
    if result:
        print("\n" + "=" * 60)
        print("下一步：运行 2_download_and_check.py 下载并检测新版本")
        print("=" * 60)
        sys.exit(1)  # 有新版本
    else:
        sys.exit(0)  # 无新版本

