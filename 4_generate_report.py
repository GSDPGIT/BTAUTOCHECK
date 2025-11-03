#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BT-Panel 检测报告生成脚本
功能：生成Markdown格式的安全检测报告
"""

import json
import os
import sys
from datetime import datetime

def generate_markdown_report(result_data):
    """生成详细的Markdown格式检测报告"""
    version = result_data['version']
    md5 = result_data['md5']
    basic_check = result_data.get('basic_check', {})
    static_analysis = result_data.get('static_analysis', {})
    ai_analysis = result_data.get('ai_analysis', None)
    category_stats = static_analysis.get('category_stats', {})
    findings = static_analysis.get('findings', {})
    
    # 分类名称和说明
    category_info = {
        'backdoor_critical': {
            'name': '🚨 高危后门特征',
            'severity': '严重',
            'desc': 'eval($var)、assert($var)等动态代码执行，可能被利用执行任意代码'
        },
        'command_execution': {
            'name': '🔧 系统命令执行',
            'severity': '正常',
            'desc': '管理面板需要执行系统命令来管理服务器，这是正常功能'
        },
        'remote_connection': {
            'name': '🌐 远程连接',
            'severity': '正常',
            'desc': '管理面板需要建立网络连接进行更新、插件下载等，这是正常功能'
        },
        'obfuscation_critical': {
            'name': '🔒 代码混淆/加密',
            'severity': '中等',
            'desc': 'Base64长字符串解码、gzinflate等，可能用于隐藏恶意代码'
        },
        'tracking_ads': {
            'name': '📊 广告/统计追踪',
            'severity': '严重',
            'desc': '向bt.cn、io.bt.sb等域名发送统计数据，可能泄露用户隐私'
        },
        'data_leak': {
            'name': '🔐 敏感数据泄露',
            'severity': '严重',
            'desc': '密码、Token等敏感数据通过HTTP传输，存在泄露风险'
        },
        'suspicious_domain': {
            'name': '🌍 可疑域名/IP',
            'severity': '中等',
            'desc': '直接通过IP地址或可疑域名进行HTTP请求'
        },
        'file_transfer': {
            'name': '📤 文件传输',
            'severity': '正常',
            'desc': '管理面板需要下载/上传文件，这是正常功能'
        },
        'sql_injection_risk': {
            'name': '🗄️ SQL注入风险',
            'severity': '严重',
            'desc': '直接将用户输入($_GET/$_POST)拼接到SQL查询，存在注入风险'
        },
        'privilege_escalation': {
            'name': '🔓 权限提升',
            'severity': '中等',
            'desc': 'chmod 777、sudo等权限操作，可能存在权限滥用风险'
        },
        'dangerous_functions': {
            'name': '💀 危险函数',
            'severity': '严重',
            'desc': 'unserialize($_GET)、extract($_POST)等，可能导致代码执行'
        }
    }
    
    # 生成报告
    report = f"""# 🔍 BT-Panel {version} 安全检测报告（详细版）

> **检测时间**: {result_data.get('check_time', 'N/A')}  
> **检测版本**: Linux Panel {version}  
> **安全评分**: {static_analysis.get('security_score', 0)}/100  
> **检测状态**: {'✅ 通过' if static_analysis.get('is_safe', False) else '⚠️ 需审查'}  
> **检测文件数**: {result_data.get('files_analyzed', 0)} 个

---

## 📦 文件基本信息

| 项目 | 信息 |
|------|------|
| 文件名 | `{result_data['filename']}` |
| MD5 | `{md5}` |
| 文件大小 | {basic_check.get('size_mb', 0)} MB |
| 压缩包文件数 | {basic_check.get('file_count', 0)} 个 |
| 实际分析文件数 | {result_data.get('files_analyzed', 0)} 个 |
| 下载来源 | {result_data['download_url']} |

---

## 🤖 AI深度分析

"""
    
    # 添加AI分析结果
    if ai_analysis:
        report += f"""
**AI模型**: {ai_analysis.get('provider', 'Unknown').upper()}  
**分析文件数**: {ai_analysis.get('analyzed_files', 0)} 个高风险文件  
**AI评分**: {ai_analysis.get('average_score', 0)}/100  
**发现问题**: {ai_analysis.get('total_findings', 0)} 个  
**AI建议**: {'✅ 安全可用' if ai_analysis.get('overall_safe', False) else '⚠️ 需要审查'}

<details>
<summary><b>展开查看AI发现的问题</b></summary>

"""
        ai_findings = ai_analysis.get('findings', [])
        if ai_findings:
            for i, finding in enumerate(ai_findings[:10], 1):
                report += f"""
**问题 {i}**: {finding.get('type', 'Unknown')}  
- **严重程度**: {finding.get('severity', 'unknown')}  
- **描述**: {finding.get('description', 'N/A')}  
- **位置**: 第 {finding.get('line', 'N/A')} 行
"""
        else:
            report += "\n✅ AI未发现明显安全问题\n"
        
        report += "\n</details>\n"
    else:
        report += """
**AI分析状态**: ⚪ 未启用

要启用AI分析，请在 `config.json` 中配置：
```json
"ai_providers": {
    "enabled": true,
    "primary_provider": "gemini"
}
```

"""
    
    report += """
---

## 📊 静态规则分析

**综合评分**: {static_analysis.get('security_score', 0)}/100  
**总扣分**: {static_analysis.get('total_deductions', 0)}分

**扣分明细**:
"""
    
    # 使用实际的扣分详情（从静态分析结果读取）
    deduction_details = static_analysis.get('deduction_details', [])
    
    if deduction_details:
        for detail in deduction_details:
            report += f"- {detail}\n"
    else:
        report += "- 无扣分记录\n"
    
    report += "\n**正常功能（不扣分）**:\n"
    report += f"- 🔧 命令执行: {category_stats.get('command_execution', 0)}处 (管理面板必需功能)\n"
    report += f"- 🌐 远程连接: {category_stats.get('remote_connection', 0)}处 (管理面板必需功能)\n"
    report += f"- 📤 文件传输: {category_stats.get('file_transfer', 0)}处 (管理面板必需功能)\n"
    
    report += "\n---\n\n"
    report += f"## 🔍 详细检测结果\n\n"
    report += f"**总问题数**: {static_analysis.get('total_issues', 0)}  \n"
    report += f"**风险文件数**: {static_analysis.get('risky_files', 0)}/{result_data.get('files_analyzed', 0)}\n\n"
    
    # 按严重程度排序显示
    priority_order = [
        'backdoor_critical',
        'obfuscation_critical', 
        'sql_injection_risk',
        'dangerous_functions',
        'tracking_ads',
        'data_leak',
        'privilege_escalation',
        'suspicious_domain',
        'file_transfer',
        'remote_connection',
        'command_execution'
    ]
    
    for category in priority_order:
        items = findings.get(category, [])
        if not items:
            continue
        
        info = category_info.get(category, {})
        count = len(items)
        
        report += f"\n### {info.get('name', category)} ({count} 处)\n\n"
        report += f"**严重程度**: {info.get('severity', '未知')}  \n"
        report += f"**说明**: {info.get('desc', '暂无说明')}\n\n"
        
        # 列出所有文件（不省略）
        report += f"<details>\n<summary>点击展开查看所有 {count} 个文件</summary>\n\n"
        
        for i, item in enumerate(items, 1):
            report += f"{i}. **{item['file']}** (匹配{item['matches']}处)\n"
            report += f"   - 匹配规则: `{item['pattern']}`\n"
            
            # 显示代码样本
            if item.get('samples'):
                report += f"   - 样本: "
                for j, sample in enumerate(item['samples'][:2], 1):
                    if j > 1:
                        report += ", "
                    report += f"`{sample}`"
                report += "\n"
            report += "\n"
        
        report += "</details>\n\n"
    
    # 安全建议
    report += "---\n\n## 💡 安全建议\n\n"
    
    if static_analysis.get('recommendations'):
        for i, rec in enumerate(static_analysis['recommendations'], 1):
            report += f"{i}. {rec}\n"
    
    # 总结
    report += "\n---\n\n## 📋 检测总结\n\n"
    report += f"{static_analysis.get('summary', '无总结')}\n\n"
    
    # 检测信息
    report += "---\n\n## ℹ️ 检测信息\n\n"
    report += f"- **分析文件数**: {result_data.get('files_analyzed', 0)}\n"
    report += f"- **检测方式**: 基础检查 + 静态规则分析\n"
    report += f"- **检测工具**: Python脚本 + 规则引擎（11类检测）\n"
    report += f"- **检测日期**: {result_data.get('check_time', 'N/A')}\n"
    report += f"- **报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    report += "\n---\n\n"
    report += f"**自动化系统**: BTAUTOCHECK V1.0  \n"
    report += f"**GitHub**: https://github.com/GSDPGIT/BTAUTOCHECK\n"
    
    return report

def main():
    """主函数"""
    print("=" * 60)
    print("生成安全检测报告")
    print("=" * 60)
    
    download_dir = os.path.join(os.path.dirname(__file__), 'downloads')
    
    # 查找最新的检测结果
    result_files = [f for f in os.listdir(download_dir) if f.startswith('security_report_') and f.endswith('.json')]
    
    if not result_files:
        print("❌ 未找到检测结果文件")
        return False
    
    # 使用最新的结果文件
    latest_result = sorted(result_files)[-1]
    result_path = os.path.join(download_dir, latest_result)
    
    print(f"读取检测结果: {result_path}")
    
    with open(result_path, 'r', encoding='utf-8') as f:
        result_data = json.load(f)
    
    # 生成Markdown报告
    print("\n正在生成Markdown报告...")
    markdown_report = generate_markdown_report(result_data)
    
    # 保存报告
    version = result_data['version']
    report_file = os.path.join(download_dir, f'SECURITY_REPORT_{version}.md')
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(markdown_report)
    
    print(f"✅ 报告已生成: {report_file}")
    
    # 显示报告预览
    print("\n" + "=" * 60)
    print("报告预览")
    print("=" * 60)
    print(markdown_report[:500] + "...\n")
    
    print("=" * 60)
    print("下一步：运行 5_update_and_upload.py 自动更新并上传")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

