#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BT-Panel AI安全检测脚本
功能：使用Gemini AI对下载的文件进行深度安全分析
"""

import requests
import json
import os
import zipfile
import sys
import hashlib
from datetime import datetime

# 加载配置
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
VERSION_FILE = os.path.join(os.path.dirname(__file__), 'new_version.json')

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)

GEMINI_API_KEY = config['gemini_api_key']
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

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

def ai_security_analysis(files_info, version):
    """使用Gemini AI进行安全分析"""
    print("\n" + "=" * 60)
    print("AI安全分析（使用Gemini）")
    print("=" * 60)
    
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        print("⚠️  Gemini API Key未配置，跳过AI分析")
        return {
            'status': 'skipped',
            'reason': 'API key not configured',
            'recommendation': 'manual_review'
        }
    
    # 准备分析提示词
    prompt = f"""请作为一个安全专家，对宝塔面板 {version} 升级包进行安全审计。

以下是升级包中的关键文件清单（共{len(files_info)}个文件）:
"""
    
    # 添加文件信息
    for i, file_info in enumerate(files_info[:20], 1):  # 限制前20个文件
        prompt += f"\n{i}. {file_info['path']} ({file_info['size']} bytes)"
    
    prompt += f"""

请重点检查：
1. **后门风险**: 是否存在可疑的远程连接、命令执行、数据上传等后门代码
2. **恶意代码**: 是否包含病毒、木马、挖矿等恶意程序
3. **隐私泄露**: 是否存在未授权的数据收集和上报
4. **广告追踪**: 是否包含广告展示或用户行为追踪
5. **安全漏洞**: 是否存在SQL注入、命令注入等安全漏洞

请给出：
1. 安全评分（0-100分）
2. 主要发现（如果有）
3. 是否建议使用
4. 需要移除的内容（如果有）

以JSON格式返回结果，格式如下：
{{
    "security_score": 95,
    "is_safe": true,
    "main_findings": ["发现1", "发现2"],
    "recommendations": ["建议1", "建议2"],
    "files_to_remove": ["文件1", "文件2"],
    "summary": "总体评价"
}}
"""
    
    try:
        print("正在调用Gemini AI分析...")
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # 解析Gemini响应
            if 'candidates' in result and len(result['candidates']) > 0:
                text = result['candidates'][0]['content']['parts'][0]['text']
                print("\n✅ AI分析完成")
                print("\n" + "=" * 60)
                print("AI分析结果:")
                print("=" * 60)
                print(text)
                
                # 尝试提取JSON
                try:
                    # 提取JSON部分
                    if '```json' in text:
                        json_text = text.split('```json')[1].split('```')[0].strip()
                    elif '{' in text and '}' in text:
                        json_text = text[text.find('{'):text.rfind('}')+1]
                    else:
                        json_text = text
                    
                    ai_result = json.loads(json_text)
                    return ai_result
                except:
                    # 如果无法解析JSON，返回原始文本
                    return {
                        'status': 'analyzed',
                        'raw_response': text,
                        'security_score': 0,
                        'is_safe': False,
                        'summary': '需要人工审查AI响应'
                    }
            else:
                print("❌ AI响应格式异常")
                return {'status': 'error', 'reason': 'Invalid response format'}
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return {'status': 'error', 'reason': f'API error {response.status_code}'}
    
    except Exception as e:
        print(f"❌ AI分析失败: {e}")
        return {'status': 'error', 'reason': str(e)}

def main():
    """主函数"""
    print("=" * 60)
    print("BT-Panel 下载与AI安全检测")
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
    
    # 下载文件
    filename = f"LinuxPanel-{version}.zip"
    file_path = os.path.join(download_dir, filename)
    
    if not os.path.exists(file_path):
        if not download_file(download_url, file_path):
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
    
    # AI安全分析
    ai_result = ai_security_analysis(files_info, version)
    
    # 保存完整结果
    final_result = {
        'version': version,
        'filename': filename,
        'md5': md5,
        'download_url': download_url,
        'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'basic_check': basic_check,
        'ai_analysis': ai_result,
        'files_analyzed': len(files_info)
    }
    
    result_file = os.path.join(download_dir, f'security_report_{version}.json')
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, indent=4, ensure_ascii=False)
    
    print(f"\n✅ 完整检测报告已保存: {result_file}")
    
    # 判断是否安全
    if ai_result.get('is_safe', False) and ai_result.get('security_score', 0) >= config['security_threshold']:
        print(f"\n🎉 安全检测通过！(评分: {ai_result.get('security_score')}/100)")
        print("\n下一步：运行 4_generate_report.py 生成检测报告")
        return True
    else:
        print(f"\n⚠️  安全检测未通过或需要人工审查")
        print(f"   评分: {ai_result.get('security_score', 0)}/100")
        print(f"   阈值: {config['security_threshold']}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

