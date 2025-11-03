#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多源验证工具 - 对比官方和第三方源
Multi-Source Verification Tool
"""

import sys
import requests
import hashlib

def download_and_hash(url):
    """下载文件并计算哈希"""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            content = response.content
            md5 = hashlib.md5(content).hexdigest()
            sha256 = hashlib.sha256(content).hexdigest()
            return {
                'success': True,
                'size': len(content),
                'md5': md5,
                'sha256': sha256
            }
        else:
            return {'success': False, 'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def verify_multi_source(version):
    """验证多个源的文件一致性"""
    print("="*70)
    print(f"🔍 多源验证: {version}")
    print("="*70)
    
    sources = [
        ('官方源', f'https://download.bt.cn/install/update/LinuxPanel-{version}.zip'),
        ('第三方源', f'http://io.bt.sb/install/update/LinuxPanel-{version}.zip'),
        ('GitHub源', f'https://github.com/GSDPGIT/bt-panel-files/raw/main/LinuxPanel-{version}.zip')
    ]
    
    results = {}
    for name, url in sources:
        print(f"\n📥 {name}: {url}")
        result = download_and_hash(url)
        results[name] = result
        
        if result['success']:
            print(f"✅ 下载成功")
            print(f"   大小: {result['size'] // (2**20)} MB")
            print(f"   MD5: {result['md5']}")
        else:
            print(f"❌ 下载失败: {result['error']}")
    
    # 对比哈希
    print("\n" + "="*70)
    print("📊 一致性验证")
    print("="*70)
    
    successful = [name for name, r in results.items() if r['success']]
    if len(successful) < 2:
        print("⚠️  可用源不足，无法对比")
        return
    
    hashes = {name: results[name]['md5'] for name in successful}
    unique_hashes = set(hashes.values())
    
    if len(unique_hashes) == 1:
        print("✅ 所有源文件一致！")
        print(f"   统一MD5: {list(unique_hashes)[0]}")
    else:
        print("⚠️  警告：不同源的文件不一致！")
        for name, hash_val in hashes.items():
            print(f"   {name}: {hash_val}")

if __name__ == '__main__':
    version = sys.argv[1] if len(sys.argv) > 1 else '11.2.0'
    verify_multi_source(version)

