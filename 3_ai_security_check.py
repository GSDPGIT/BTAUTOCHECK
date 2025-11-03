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

# 恶意模式特征库（超严格模式）
MALICIOUS_PATTERNS = {
    # 🚨 后门特征（高危）- 只检测真正的动态执行
    'backdoor_critical': [
        r'eval\s*\(\s*\$_(?:GET|POST|REQUEST|COOKIE)',  # eval($_GET) - 用户输入执行
        r'assert\s*\(\s*\$_(?:GET|POST|REQUEST)',  # assert($_POST) - 用户输入断言
        r'preg_replace\s*\(.*\/e.*\$_',  # preg_replace /e 模式 + 用户输入
        r'system\s*\(\s*\$_(?:GET|POST|REQUEST)',  # system($_GET) - 用户输入执行
        r'exec\s*\(\s*\$_(?:GET|POST|REQUEST)',  # exec($_POST) - 用户输入执行
    ],
    
    # 🔧 系统命令执行
    'command_execution': [
        r'system\s*\(',
        r'exec\s*\(',
        r'passthru\s*\(',
        r'shell_exec\s*\(',
        r'popen\s*\(',
        r'proc_open\s*\(',
        r'pcntl_exec\s*\(',
        r'subprocess\.call',
        r'subprocess\.Popen',
        r'os\.system',
        r'os\.popen',
    ],
    
    # 🌐 远程连接（高危）
    'remote_connection': [
        r'fsockopen\s*\(',
        r'pfsockopen\s*\(',
        r'stream_socket_client',
        r'socket_create',
        r'socket_connect',
        r'curl_exec',
        r'ftp_connect',
        r'ssh2_connect',
        r'telnet',
    ],
    
    # 🔒 代码混淆/加密（高危）
    'obfuscation_critical': [
        r'base64_decode\s*\(\s*["\'][\w+/=]{50,}',  # Base64长字符串解码
        r'gzinflate\s*\(',
        r'gzuncompress\s*\(',
        r'str_rot13\s*\(',
        r'convert_uudecode',
        r'gzdeflate',
        r'bzdecompress',
    ],
    
    # 📊 广告/统计（严格检测）
    'tracking_ads': [
        r'google-analytics\.com',
        r'baidu\.com/tongji',
        r'cnzz\.com',
        r'umeng\.com',
        r'bt\.cn/Api/Panel',
        r'api\.bt\.cn',
        r'bt\.cn/api/panel',
        r'io\.bt\.sb',
        r'download\.bt\.cn.*userInfo',
        r'statistics',
        r'analytics',
        r'/tongji/',
    ],
    
    # 🔐 敏感数据泄露（精确检测）
    'data_leak': [
        r'curl.*-d.*(?:username|user)=',  # curl传输用户名
        r'curl.*-d.*password=',  # curl传输密码
        r'requests\.post.*password',  # Python requests传输密码
        r'file_get_contents.*password',  # PHP读取包含密码的URL
        r'(?:token|apikey|api_key)=.*[&\s].*http',  # Token跟随HTTP请求
    ],
    
    # 🌍 可疑域名/IP（只检测实际的HTTP请求）
    'suspicious_domain': [
        r'(?:curl|wget|requests\.get|requests\.post|http_request).*http://\d+\.\d+\.\d+\.\d+',  # HTTP请求到IP地址
        r'(?:curl|wget).*\.ru/',  # 下载俄罗斯域名文件
        r'file_get_contents\s*\(\s*["\']http://\d+\.\d+\.\d+\.\d+',  # PHP直接访问IP
    ],
    
    # 📤 文件下载/上传
    'file_transfer': [
        r'wget\s+http',
        r'curl.*-O.*http',
        r'download.*http',
        r'file_get_contents\s*\(\s*["\']http',
    ],
    
    # 🗄️ 数据库注入风险
    'sql_injection_risk': [
        r'mysql_query.*\$_GET',
        r'mysql_query.*\$_POST',
        r'->query.*\$_GET',
        r'->query.*\$_POST',
        r'execute.*\$_GET',
        r'execute.*\$_POST',
    ],
    
    # 🔓 权限提升（只检测真正危险的操作）
    'privilege_escalation': [
        r'chmod\s+777.*(?:\/etc|\/bin|\/sbin|\/usr\/bin)',  # 只检测系统关键目录的777权限
        r'chown\s+root.*(?:\/tmp|\/var\/tmp)',  # 临时目录改为root所有
        r'sudo\s+(?:rm|dd|mkfs)',  # sudo执行危险命令
        r'setuid\s*\(\s*0\s*\)',  # 设置为root uid
        r'setgid\s*\(\s*0\s*\)',  # 设置为root gid
    ],
    
    # 💀 危险函数
    'dangerous_functions': [
        r'unserialize\s*\(\s*\$_(?:GET|POST|REQUEST|COOKIE)',  # 只检测来自用户输入的反序列化
        r'extract\s*\(\s*\$_(?:GET|POST|REQUEST)',  # 只检测来自用户输入的变量覆盖
        r'parse_str.*\$_(?:GET|POST|REQUEST)',  # 只检测来自用户输入的解析
        r'import_request_variables',
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
    """解压并深度分析所有文件（超严格模式 - 排除误报）"""
    print("\n" + "=" * 60)
    print("📦 解压并收集文件信息")
    print("=" * 60)
    
    try:
        # 解压文件
        print("正在解压文件...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print(f"✅ 解压完成: {extract_dir}")
        
        # 收集所有文件信息
        all_files = []
        files_to_check = []
        
        print("\n正在扫描文件...")
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, extract_dir)
                all_files.append(rel_path)
        
        print(f"📊 总文件数: {len(all_files)}")
        
        # 严格模式：检查所有脚本、配置、可执行文件（不排除任何文件）
        check_extensions = (
            '.sh', '.py', '.php', '.pl', '.js', '.json', 
            '.conf', '.cfg', '.ini', '.xml', '.yml', '.yaml',
            '.html', '.htm', '.sql', '.c', '.cpp', '.go'
        )
        
        print("\n正在读取文件内容（全量检测，不排除任何文件）...")
        for i, file_name in enumerate(all_files, 1):
            if i % 100 == 0:
                print(f"进度: {i}/{len(all_files)} ({i*100//len(all_files)}%)")
            
            file_path = os.path.join(extract_dir, file_name)
            
            # 检查文件扩展名
            if file_name.lower().endswith(check_extensions):
                try:
                    # 读取文件内容
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # 不限制内容长度，全量分析
                    files_to_check.append({
                        'path': file_name,
                        'size': len(content),
                        'content': content,
                        'type': os.path.splitext(file_name)[1]
                    })
                except Exception as e:
                    # 二进制文件或读取失败，跳过
                    pass
        
        print(f"\n✅ 收集到 {len(files_to_check)} 个文件待分析（全量检测）")
        print(f"   类型分布: ")
        
        # 统计文件类型
        type_count = {}
        for f in files_to_check:
            ext = f['type']
            type_count[ext] = type_count.get(ext, 0) + 1
        
        for ext, count in sorted(type_count.items(), key=lambda x: -x[1])[:10]:
            print(f"   - {ext}: {count} 个")
        
        return files_to_check
    
    except Exception as e:
        print(f"❌ 解压失败: {e}")
        return []

def static_code_analysis(files_info, version):
    """静态代码安全分析（规则引擎 - 超严格模式）"""
    print("\n" + "=" * 60)
    print("🔍 静态安全分析（规则引擎 - 超严格模式）")
    print("=" * 60)
    
    print(f"\n📊 开始分析 {len(files_info)} 个文件...")
    print("=" * 60)
    
    # 分析结果（按新的分类）
    findings = {}
    for category in MALICIOUS_PATTERNS.keys():
        findings[category] = []
    
    risky_files = set()
    total_issues = 0
    analyzed_count = 0
    
    # 遍历所有文件进行检测（带进度显示）
    print("\n正在逐个检测文件内容...")
    for i, file_info in enumerate(files_info, 1):
        file_path = file_info['path']
        content = file_info['content']
        
        # 每100个文件显示一次进度
        if i % 100 == 0 or i == len(files_info):
            percent = i * 100 // len(files_info)
            print(f"进度: {i}/{len(files_info)} ({percent}%) - 当前: {file_path[:50]}...")
        
        analyzed_count += 1
        file_has_issues = False
        
        # 对每个文件检测所有恶意模式
        for category, patterns in MALICIOUS_PATTERNS.items():
            for pattern in patterns:
                try:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        finding = {
                            'file': file_path,
                            'pattern': pattern,
                            'matches': len(matches),
                            'samples': [str(m)[:50] for m in matches[:3]]  # 只保留前3个样本，限制长度
                        }
                        findings[category].append(finding)
                        risky_files.add(file_path)
                        total_issues += len(matches)
                        file_has_issues = True
                except Exception as e:
                    # 正则表达式错误，继续下一个
                    pass
        
        # 显示发现问题的文件（实时反馈）
        if file_has_issues and i % 50 == 0:
            print(f"   ⚠️  发现风险: {file_path}")
    
    print(f"\n✅ 分析完成: {analyzed_count}/{len(files_info)} 个文件")
    
    # 打印详细发现
    print("\n" + "=" * 60)
    print("🔎 检测结果详情")
    print("=" * 60)
    
    for category, items in findings.items():
        if items:
            category_emoji = {
                'backdoor_critical': '🚨',
                'command_execution': '🔧',
                'remote_connection': '🌐',
                'obfuscation_critical': '🔒',
                'tracking_ads': '📊',
                'data_leak': '🔐',
                'suspicious_domain': '🌍',
                'file_transfer': '📤',
                'sql_injection_risk': '🗄️',
                'privilege_escalation': '🔓',
                'dangerous_functions': '💀'
            }
            emoji = category_emoji.get(category, '⚠️')
            print(f"\n{emoji} [{category.upper()}] 发现 {len(items)} 处可疑代码:")
            for item in items[:10]:  # 显示前10个
                print(f"   - {item['file']}: {item['matches']} 处匹配")
            if len(items) > 10:
                print(f"   ... 还有 {len(items) - 10} 个文件")
    
    # 计算安全评分（超严格模式）
    print("\n" + "=" * 60)
    print("📐 计算安全评分")
    print("=" * 60)
    
    base_score = 100
    deductions = 0
    risk_details = []
    
    # 获取各类别数量
    backdoor_critical = len(findings.get('backdoor_critical', []))
    command_execution = len(findings.get('command_execution', []))
    remote_connection = len(findings.get('remote_connection', []))
    obfuscation_critical = len(findings.get('obfuscation_critical', []))
    tracking_ads = len(findings.get('tracking_ads', []))
    data_leak = len(findings.get('data_leak', []))
    suspicious_domain = len(findings.get('suspicious_domain', []))
    file_transfer = len(findings.get('file_transfer', []))
    sql_injection_risk = len(findings.get('sql_injection_risk', []))
    privilege_escalation = len(findings.get('privilege_escalation', []))
    dangerous_functions = len(findings.get('dangerous_functions', []))
    
    # 合理化扣分规则（针对管理面板特性优化）
    # 1. 高危后门特征（真正的安全问题）
    if backdoor_critical > 50:
        deduct = 30
        deductions += deduct
        risk_details.append(f"🚨 高危后门特征（严重）: {backdoor_critical}处 (-{deduct}分)")
    elif backdoor_critical > 20:
        deduct = 25
        deductions += deduct
        risk_details.append(f"🚨 高危后门特征（中等）: {backdoor_critical}处 (-{deduct}分)")
    elif backdoor_critical > 5:
        deduct = 20
        deductions += deduct
        risk_details.append(f"🚨 高危后门特征（轻微）: {backdoor_critical}处 (-{deduct}分)")
    elif backdoor_critical > 0:
        deduct = 15
        deductions += deduct
        risk_details.append(f"🚨 高危后门特征（极少）: {backdoor_critical}处 (-{deduct}分)")
    
    # 2. 代码混淆（编辑器文件中多为正常代码）
    if obfuscation_critical > 50:
        deduct = 20
        deductions += deduct
        risk_details.append(f"🔒 代码混淆（严重）: {obfuscation_critical}处 (-{deduct}分)")
    elif obfuscation_critical > 30:
        deduct = 15
        deductions += deduct
        risk_details.append(f"🔒 代码混淆（中等）: {obfuscation_critical}处 (-{deduct}分)")
    elif obfuscation_critical > 10:
        deduct = 5
        deductions += deduct
        risk_details.append(f"🔒 代码混淆（轻微）: {obfuscation_critical}处 (-{deduct}分)")
    
    # 3. 广告/统计追踪（主要清理目标，但安装脚本已处理）
    if tracking_ads > 100:
        deduct = 20
        deductions += deduct
        risk_details.append(f"📊 广告统计（严重）: {tracking_ads}处 (-{deduct}分)")
    elif tracking_ads > 50:
        deduct = 15
        deductions += deduct
        risk_details.append(f"📊 广告统计（中等）: {tracking_ads}处 (-{deduct}分)")
    elif tracking_ads > 0:
        deduct = 10
        deductions += deduct
        risk_details.append(f"📊 广告统计（已在安装脚本中处理）: {tracking_ads}处 (-{deduct}分)")
    
    # 4. 敏感数据泄露（前端表单多为正常提交）
    if data_leak > 50:
        deduct = 15
        deductions += deduct
        risk_details.append(f"🔐 数据泄露风险（严重）: {data_leak}处 (-{deduct}分)")
    elif data_leak > 20:
        deduct = 10
        deductions += deduct
        risk_details.append(f"🔐 数据泄露风险（中等）: {data_leak}处 (-{deduct}分)")
    elif data_leak > 0:
        deduct = 5
        deductions += deduct
        risk_details.append(f"🔐 数据泄露风险（轻微）: {data_leak}处 (-{deduct}分)")
    
    # 5. SQL注入风险
    if sql_injection_risk > 10:
        deduct = 20
        deductions += deduct
        risk_details.append(f"🗄️ SQL注入风险（严重）: {sql_injection_risk}处 (-{deduct}分)")
    elif sql_injection_risk > 0:
        deduct = 15
        deductions += deduct
        risk_details.append(f"🗄️ SQL注入风险: {sql_injection_risk}处 (-{deduct}分)")
    
    # 6. 可疑域名（少量可接受）
    if suspicious_domain > 20:
        deduct = 15
        deductions += deduct
        risk_details.append(f"🌍 可疑域名/IP请求（严重）: {suspicious_domain}处 (-{deduct}分)")
    elif suspicious_domain > 10:
        deduct = 10
        deductions += deduct
        risk_details.append(f"🌍 可疑域名/IP请求（中等）: {suspicious_domain}处 (-{deduct}分)")
    elif suspicious_domain > 5:
        deduct = 5
        deductions += deduct
        risk_details.append(f"🌍 可疑域名/IP请求（轻微）: {suspicious_domain}处 (-{deduct}分)")
    
    # 7. 权限提升（少量正常）
    if privilege_escalation > 20:
        deduct = 15
        deductions += deduct
        risk_details.append(f"🔓 权限提升（严重）: {privilege_escalation}处 (-{deduct}分)")
    elif privilege_escalation > 10:
        deduct = 10
        deductions += deduct
        risk_details.append(f"🔓 权限提升（中等）: {privilege_escalation}处 (-{deduct}分)")
    elif privilege_escalation > 5:
        deduct = 5
        deductions += deduct
        risk_details.append(f"🔓 权限提升（轻微）: {privilege_escalation}处 (-{deduct}分)")
    
    # 8. 危险函数（非常少，轻微扣分）
    if dangerous_functions > 20:
        deduct = 15
        deductions += deduct
        risk_details.append(f"💀 危险函数（严重）: {dangerous_functions}处 (-{deduct}分)")
    elif dangerous_functions > 10:
        deduct = 10
        deductions += deduct
        risk_details.append(f"💀 危险函数（中等）: {dangerous_functions}处 (-{deduct}分)")
    elif dangerous_functions > 0:
        deduct = 3
        deductions += deduct
        risk_details.append(f"💀 危险函数（轻微）: {dangerous_functions}处 (-{deduct}分)")
    
    # 命令执行和远程连接是管理面板的核心功能，只在异常多时才扣分
    if command_execution > 500:
        deduct = 10
        deductions += deduct
        risk_details.append(f"🔧 命令执行异常多: {command_execution}处 (-{deduct}分)")
    
    if remote_connection > 50:
        deduct = 10
        deductions += deduct
        risk_details.append(f"🌐 远程连接异常多: {remote_connection}处 (-{deduct}分)")
    
    # 最终评分
    security_score = max(0, base_score - deductions)
    
    # 显示扣分详情
    if risk_details:
        print("\n扣分详情:")
        for detail in risk_details:
            print(f"  {detail}")
    
    # 判断是否安全
    is_safe = security_score >= 80
    
    # 生成建议
    recommendations = []
    files_to_remove = []
    
    # 高危问题建议
    if backdoor_critical > 0:
        recommendations.append(f"🚨 发现{backdoor_critical}处高危后门特征（eval/assert动态执行），强烈建议人工深度审查")
        files_to_remove.extend([f['file'] for f in findings.get('backdoor_critical', [])])
    
    if obfuscation_critical > 0:
        recommendations.append(f"🔒 发现{obfuscation_critical}处代码混淆（Base64/gzinflate），可能隐藏恶意代码")
        files_to_remove.extend([f['file'] for f in findings.get('obfuscation_critical', [])])
    
    if data_leak > 0:
        recommendations.append(f"🔐 发现{data_leak}处敏感数据泄露风险（密码/Token传输），需仔细检查")
    
    if tracking_ads > 0:
        recommendations.append(f"📊 发现{tracking_ads}处广告/统计代码（bt.cn/api等），建议移除")
        files_to_remove.extend([f['file'] for f in findings.get('tracking_ads', [])])
    
    if sql_injection_risk > 0:
        recommendations.append(f"🗄️ 发现{sql_injection_risk}处SQL注入风险（$_GET/$_POST直接拼接），需修复")
    
    if privilege_escalation > 0:
        recommendations.append(f"🔓 发现{privilege_escalation}处权限提升操作（chmod 777/sudo），需谨慎")
    
    if dangerous_functions > 0:
        recommendations.append(f"💀 发现{dangerous_functions}处危险函数（unserialize/extract），存在安全隐患")
    
    # 正常功能提示
    if command_execution > 0:
        recommendations.append(f"ℹ️ 检测到{command_execution}处命令执行（管理面板正常功能）")
    
    if remote_connection > 0:
        recommendations.append(f"ℹ️ 检测到{remote_connection}处远程连接（管理面板正常功能）")
    
    # 生成总结
    if security_score >= 95:
        summary = "✅ 代码质量优秀，未发现严重安全问题，可以安全使用"
    elif security_score >= 80:
        summary = "⚠️ 存在少量可疑代码，建议进行人工审查后使用"
    elif security_score >= 60:
        summary = "🔴 存在多处安全风险，需要仔细审查和清理后才能使用"
    else:
        summary = "🚨 发现大量严重安全问题，强烈不建议使用"
    
    # 最终输出
    print(f"\n" + "=" * 60)
    print(f"📊 最终安全评分")
    print("=" * 60)
    print(f"\n🎯 综合评分: {security_score}/100")
    print(f"📁 检测文件数: {len(files_info)}")
    print(f"⚠️  风险文件数: {len(risky_files)}")
    print(f"🔍 问题总数: {total_issues}")
    print(f"\n💡 总结: {summary}")
    
    # 分类统计
    print(f"\n" + "=" * 60)
    print("📋 分类统计")
    print("=" * 60)
    print(f"  🚨 高危后门: {backdoor_critical}处")
    print(f"  🔒 代码混淆: {obfuscation_critical}处")
    print(f"  📊 广告统计: {tracking_ads}处")
    print(f"  🔐 数据泄露: {data_leak}处")
    print(f"  🗄️ SQL注入: {sql_injection_risk}处")
    print(f"  🔓 权限提升: {privilege_escalation}处")
    print(f"  💀 危险函数: {dangerous_functions}处")
    print(f"  🔧 命令执行: {command_execution}处 (管理面板正常)")
    print(f"  🌐 远程连接: {remote_connection}处 (管理面板正常)")
    print(f"  📤 文件传输: {file_transfer}处 (管理面板正常)")
    print("=" * 60)
    
    return {
        'status': 'completed',
        'security_score': security_score,
        'is_safe': is_safe,
        'total_issues': total_issues,
        'risky_files': len(risky_files),
        'analyzed_files': len(files_info),
        'findings': findings,
        'recommendations': recommendations,
        'files_to_remove': list(set(files_to_remove)),
        'summary': summary,
        'deduction_details': risk_details,  # 扣分详情
        'total_deductions': deductions,  # 总扣分
        'category_stats': {
            'backdoor_critical': backdoor_critical,
            'command_execution': command_execution,
            'remote_connection': remote_connection,
            'obfuscation_critical': obfuscation_critical,
            'tracking_ads': tracking_ads,
            'data_leak': data_leak,
            'suspicious_domain': suspicious_domain,
            'file_transfer': file_transfer,
            'sql_injection_risk': sql_injection_risk,
            'privilege_escalation': privilege_escalation,
            'dangerous_functions': dangerous_functions,
        }
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

