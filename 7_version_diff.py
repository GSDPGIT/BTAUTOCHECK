#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本对比分析工具
Version Diff Analysis Tool
"""

import os
import sys
import json
import difflib
import hashlib
from pathlib import Path

def compare_versions(old_dir, new_dir):
    """对比两个版本的差异"""
    print("="*70)
    print("📊 版本对比分析")
    print("="*70)
    
    old_files = {}
    new_files = {}
    
    # 扫描旧版本
    for root, dirs, files in os.walk(old_dir):
        for file in files:
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, old_dir)
            old_files[rel_path] = filepath
    
    # 扫描新版本
    for root, dirs, files in os.walk(new_dir):
        for file in files:
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, new_dir)
            new_files[rel_path] = filepath
    
    # 分析差异
    added = set(new_files.keys()) - set(old_files.keys())
    removed = set(old_files.keys()) - set(new_files.keys())
    common = set(old_files.keys()) & set(new_files.keys())
    
    modified = []
    for file in common:
        if _file_changed(old_files[file], new_files[file]):
            modified.append(file)
    
    # 生成报告
    report = {
        "added": list(added),
        "removed": list(removed),
        "modified": modified,
        "total_changes": len(added) + len(removed) + len(modified)
    }
    
    # 输出报告
    print(f"\n📁 新增文件: {len(added)}")
    for f in sorted(added)[:10]:
        print(f"  + {f}")
    if len(added) > 10:
        print(f"  ... ({len(added)-10} more)")
    
    print(f"\n🗑️  删除文件: {len(removed)}")
    for f in sorted(removed)[:10]:
        print(f"  - {f}")
    if len(removed) > 10:
        print(f"  ... ({len(removed)-10} more)")
    
    print(f"\n✏️  修改文件: {len(modified)}")
    for f in sorted(modified)[:10]:
        print(f"  ~ {f}")
    if len(modified) > 10:
        print(f"  ... ({len(modified)-10} more)")
    
    print(f"\n📊 总变更: {report['total_changes']} 个文件")
    
    return report

def _file_changed(file1, file2):
    """检查文件是否改变"""
    try:
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
            return hashlib.md5(f1.read()).hexdigest() != hashlib.md5(f2.read()).hexdigest()
    except FileNotFoundError:
        return True  # 文件不存在，视为改变
    except IOError as e:
        print(f"⚠️ 文件读取失败: {e}")
        return True
    except Exception as e:
        print(f"⚠️ 文件比较异常: {e}")
        return True

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python3 7_version_diff.py <old_version_dir> <new_version_dir>")
        sys.exit(1)
    
    report = compare_versions(sys.argv[1], sys.argv[2])
    
    # 保存报告
    with open('version_diff_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 报告已保存: version_diff_report.json")

