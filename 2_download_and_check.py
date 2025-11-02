#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BT-Panel 下载与安全检测脚本
功能：下载新版本并进行基础安全检查
"""

import requests
import json
import os
import hashlib
import zipfile
import subprocess
from datetime import datetime

# 加载配置
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
VERSION_FILE = os.path.join(os.path.dirname(__file__), 'new_version.json')

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)

def download_file(url, save_path):
    """下载文件"""
    print(f"正在下载: {url}")
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r下载进度: {percent:.1f}% ({downloaded}/{total_size})", end='')
        
        print(f"\n✅ 下载完成: {save_path}")
        return True
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        return False

def calculate_md5(file_path):
    """计算文件MD5"""
    md5_hash = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

def basic_security_check(zip_path):
    """基础安全检查"""
    print("\n" + "=" * 60)
    print("基础安全检查")
    print("=" * 60)
    
    checks = {
        'file_exists': False,
        'is_valid_zip': False,
        'file_count': 0,
        'suspicious_files': [],
        'size_mb': 0
    }
    
    # 1. 文件存在性
    if os.path.exists(zip_path):
        checks['file_exists'] = True
        checks['size_mb'] = round(os.path.getsize(zip_path) / 1024 / 1024, 2)
        print(f"✅ 文件存在: {checks['size_mb']} MB")
    else:
        print(f"❌ 文件不存在")
        return checks
    
    # 2. ZIP完整性
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            checks['is_valid_zip'] = True
            checks['file_count'] = len(file_list)
            print(f"✅ ZIP文件有效，包含 {checks['file_count']} 个文件")
            
            # 3. 检查可疑文件
            suspicious_patterns = [
                '.exe', '.dll', '.bat', '.cmd', '.vbs', 
                'backdoor', 'trojan', 'malware', 'hack'
            ]
            
            for file in file_list:
                file_lower = file.lower()
                for pattern in suspicious_patterns:
                    if pattern in file_lower:
                        checks['suspicious_files'].append(file)
                        break
            
            if checks['suspicious_files']:
                print(f"⚠️  发现 {len(checks['suspicious_files'])} 个可疑文件:")
                for f in checks['suspicious_files'][:10]:
                    print(f"   - {f}")
            else:
                print(f"✅ 无明显可疑文件")
    
    except Exception as e:
        print(f"❌ ZIP文件损坏: {e}")
        checks['is_valid_zip'] = False
    
    return checks

def main():
    """主函数"""
    print("=" * 60)
    print("BT-Panel 下载与检测")
    print("=" * 60)
    
    # 读取新版本信息
    if not os.path.exists(VERSION_FILE):
        print("❌ 未找到新版本信息文件")
        print("   请先运行 1_check_new_version.py")
        return False
    
    with open(VERSION_FILE, 'r', encoding='utf-8') as f:
        version_info = json.load(f)
    
    version = version_info['version']
    download_url = version_info['download_url']
    
    print(f"\n版本: {version}")
    print(f"下载地址: {download_url}")
    
    # 创建下载目录
    download_dir = os.path.join(os.path.dirname(__file__), 'downloads')
    os.makedirs(download_dir, exist_ok=True)
    
    # 下载文件
    filename = f"LinuxPanel-{version}.zip"
    file_path = os.path.join(download_dir, filename)
    
    if not download_file(download_url, file_path):
        return False
    
    # 计算MD5
    print("\n正在计算MD5...")
    md5 = calculate_md5(file_path)
    print(f"MD5: {md5}")
    
    # 基础安全检查
    security_check = basic_security_check(file_path)
    
    # 保存检测结果
    result = {
        'version': version,
        'filename': filename,
        'file_path': file_path,
        'md5': md5,
        'download_url': download_url,
        'download_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'basic_check': security_check,
        'ai_check_pending': True
    }
    
    result_file = os.path.join(download_dir, f'check_result_{version}.json')
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    
    print(f"\n✅ 检测结果已保存: {result_file}")
    print("\n" + "=" * 60)
    print("下一步：运行 3_ai_security_check.py 进行AI安全分析")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

