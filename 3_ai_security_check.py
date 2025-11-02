#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BT-Panel 静态安全检测脚本
功能：使用规则引擎对下载的文件进行严格安全分析
"""

import json
import os
import zipfile
import sys
import hashlib
import re
from datetime import datetime

# 加载配置
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
VERSION_FILE = os.path.join(os.path.dirname(__file__), 'new_version.json')

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 恶意模式特征库（严格模式）
MALICIOUS_PATTERNS = {
    # 后门特征
    'backdoor': [
        r'eval\s*\(',
        r'exec\s*\(',
        r'system\s*\(',
        r'passthru\s*\(',
        r'shell_exec\s*\(',
        r'popen\s*\(',
        r'proc_open\s*\(',
        r'base64_decode\s*\(',
        r'gzinflate\s*\(',
        r'str_rot13\s*\(',
        r'assert\s*\(',
        r'preg_replace.*\/e',
        r'create_function',
        r'\$\{[^\}]*\}',  # 变量变量
    ],
    # 远程连接
    'remote_connection': [
        r'curl_exec',
        r'fsockopen',
        r'pfsockopen',
        r'stream_socket_client',
        r'socket_create',
        r'ftp_connect',
        r'ssh2_connect',
    ],
    # 文件操作风险
    'file_operation': [
        r'file_put_contents',
        r'fwrite',
        r'fputs',
        r'file_get_contents.*http',
        r'readfile',
        r'unlink',
        r'rmdir',
    ],
    # 数据库操作
    'database': [
        r'mysql_query.*\$',
        r'mysqli_query.*\$',
        r'pg_query.*\$',
        r'sqlite_query.*\$',
        r'->query\(.*\$',
    ],
    # 加密/混淆
    'obfuscation': [
        r'[\x00-\x08\x0b-\x0c\x0e-\x1f]',  # 控制字符
        r'\\x[0-9a-fA-F]{2}',  # 十六进制编码
        r'chr\(\d+\)',  # 字符编码
    ],
    # 上传/下载
    'upload_download': [
        r'move_uploaded_file',
        r'copy\s*\(.*http',
        r'file_get_contents\s*\(.*\$',
    ],
    # 广告/统计
    'tracking': [
        r'google-analytics\.com',
        r'baidu\.com/tongji',
        r'cnzz\.com',
        r'umeng\.com',
        r'bt\.cn/Api',
        r'bt\.cn/api',
        r'api\.bt\.cn',
    ]
}

def calculate_md5(file_path):
    """计算文件MD5"""
    md5_hash = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

def basic_security_check(zip_path):
    """基础安全检查"""
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
    else:
        return checks
    
    # 2. ZIP完整性
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            checks['is_valid_zip'] = True
            checks['file_count'] = len(file_list)
            
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
    except:
        pass
    
    return checks

def extract_and_analyze_files(zip_path, extract_dir):
    """解压并分析文件"""
    print("\n正在解压文件...")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        print(f"✅ 解压完成: {extract_dir}")
        
        # 收集需要分析的文件
        files_to_check = []
        
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, extract_dir)
                
                # 只检查shell脚本和Python文件
                if file.endswith(('.sh', '.py', '.php')):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        files_to_check.append({
                            'path': rel_path,
                            'size': len(content),
                            'content': content[:10000] if len(content) > 10000 else content  # 限制长度
                        })
                    except:
                        pass
        
        print(f"✅ 收集到 {len(files_to_check)} 个脚本文件待分析")
        return files_to_check
    
    except Exception as e:
        print(f"❌ 解压失败: {e}")
        return []

def static_code_analysis(files_info, version):
    """静态代码安全分析（规则引擎 - 严格模式）"""
    print("\n" + "=" * 60)
    print("静态安全分析（规则引擎 - 严格模式）")
    print("=" * 60)
    
    print(f"分析文件数量: {len(files_info)}")
    
    # 分析结果
    findings = {
        'backdoor': [],
        'remote_connection': [],
        'file_operation': [],
        'database': [],
        'obfuscation': [],
        'upload_download': [],
        'tracking': []
    }
    
    risky_files = set()
    total_issues = 0
    
    # 遍历所有文件进行检测
    for file_info in files_info:
        file_path = file_info['path']
        content = file_info['content']
        
        # 对每个文件检测所有恶意模式
        for category, patterns in MALICIOUS_PATTERNS.items():
            for pattern in patterns:
                try:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        finding = {
                            'file': file_path,
                            'pattern': pattern,
                            'matches': len(matches),
                            'samples': matches[:3]  # 只保留前3个样本
                        }
                        findings[category].append(finding)
                        risky_files.add(file_path)
                        total_issues += len(matches)
                except:
                    pass
    
    # 打印详细发现
    print("\n" + "=" * 60)
    print("检测结果详情")
    print("=" * 60)
    
    for category, items in findings.items():
        if items:
            print(f"\n⚠️  [{category.upper()}] 发现 {len(items)} 处可疑代码:")
            for item in items[:5]:  # 只显示前5个
                print(f"   - {item['file']}: {item['matches']} 处匹配")
    
    # 计算安全评分
    base_score = 100
    
    # 扣分规则（严格模式）
    deductions = {
        'backdoor': 30,           # 后门特征：严重
        'remote_connection': 20,  # 远程连接：严重
        'obfuscation': 25,       # 代码混淆：严重
        'upload_download': 15,    # 上传下载：中等
        'file_operation': 10,     # 文件操作：中等
        'database': 10,           # 数据库操作：中等
        'tracking': 20            # 广告统计：严重
    }
    
    for category, items in findings.items():
        if items:
            base_score -= deductions.get(category, 5)
    
    # 如果有大量问题，进一步降低评分
    if total_issues > 100:
        base_score -= 20
    elif total_issues > 50:
        base_score -= 10
    
    security_score = max(0, base_score)
    
    # 判断是否安全
    is_safe = security_score >= config.get('security_threshold', 95)
    
    # 生成建议
    recommendations = []
    files_to_remove = []
    
    if findings['backdoor']:
        recommendations.append("发现后门特征，强烈建议人工审查")
        files_to_remove.extend([f['file'] for f in findings['backdoor']])
    
    if findings['tracking']:
        recommendations.append("发现广告/统计代码，建议移除")
        files_to_remove.extend([f['file'] for f in findings['tracking']])
    
    if findings['obfuscation']:
        recommendations.append("发现代码混淆，存在安全风险")
    
    if findings['remote_connection']:
        recommendations.append("发现远程连接功能，需谨慎使用")
    
    # 生成总结
    if security_score >= 95:
        summary = "代码质量良好，未发现严重安全问题"
    elif security_score >= 80:
        summary = "存在少量可疑代码，建议人工审查"
    elif security_score >= 60:
        summary = "存在多处安全风险，需要仔细审查"
    else:
        summary = "发现大量安全问题，不建议直接使用"
    
    print(f"\n" + "=" * 60)
    print(f"📊 安全评分: {security_score}/100")
    print(f"🔍 风险文件数: {len(risky_files)}/{len(files_info)}")
    print(f"⚠️  问题总数: {total_issues}")
    print(f"💡 总结: {summary}")
    print("=" * 60)
    
    return {
        'status': 'completed',
        'security_score': security_score,
        'is_safe': is_safe,
        'total_issues': total_issues,
        'risky_files': len(risky_files),
        'findings': findings,
        'recommendations': recommendations,
        'files_to_remove': list(set(files_to_remove)),
        'summary': summary
    }

def main():
    """主函数"""
    print("=" * 60)
    print("BT-Panel 静态安全检测（规则引擎）")
    print("=" * 60)
    
    # 读取版本信息
    if not os.path.exists(VERSION_FILE):
        print("❌ 未找到版本信息文件")
        return False
    
    with open(VERSION_FILE, 'r', encoding='utf-8') as f:
        version_info = json.load(f)
    
    version = version_info['version']
    download_url = version_info['download_url']
    
    # 创建目录
    download_dir = os.path.join(os.path.dirname(__file__), 'downloads')
    extract_dir = os.path.join(download_dir, f'extracted_{version}')
    os.makedirs(download_dir, exist_ok=True)
    
    # 检查文件是否存在
    filename = f"LinuxPanel-{version}.zip"
    file_path = os.path.join(download_dir, filename)
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        print("   请先运行 2_download_and_check.py")
        return False
    else:
        print(f"文件已存在: {file_path}")
    
    # 计算MD5
    print("\n正在计算MD5...")
    md5 = calculate_md5(file_path)
    print(f"MD5: {md5}")
    
    # 基础安全检查
    basic_check = basic_security_check(file_path)
    
    # 解压并收集文件
    files_info = extract_and_analyze_files(file_path, extract_dir)
    
    # 静态安全分析
    static_result = static_code_analysis(files_info, version)
    
    # 保存完整结果
    final_result = {
        'version': version,
        'filename': filename,
        'md5': md5,
        'download_url': download_url,
        'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'basic_check': basic_check,
        'static_analysis': static_result,
        'files_analyzed': len(files_info)
    }
    
    result_file = os.path.join(download_dir, f'security_report_{version}.json')
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, indent=4, ensure_ascii=False)
    
    print(f"\n✅ 完整检测报告已保存: {result_file}")
    
    # 判断是否安全
    if static_result.get('is_safe', False) and static_result.get('security_score', 0) >= config['security_threshold']:
        print(f"\n🎉 安全检测通过！(评分: {static_result.get('security_score')}/100)")
        print("\n下一步：运行 4_generate_report.py 生成检测报告")
        return True
    else:
        print(f"\n⚠️  安全检测未通过或需要人工审查")
        print(f"   评分: {static_result.get('security_score', 0)}/100")
        print(f"   阈值: {config['security_threshold']}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

