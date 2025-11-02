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
    """生成Markdown格式的检测报告"""
    version = result_data['version']
    md5 = result_data['md5']
    basic_check = result_data.get('basic_check', {})
    static_analysis = result_data.get('static_analysis', {})
    
    report = f"""# BT-Panel {version} 安全检测报告

> **检测时间**: {result_data.get('check_time', 'N/A')}  
> **检测版本**: Linux Panel {version}  
> **检测状态**: {'✅ 通过' if static_analysis.get('is_safe', False) else '⚠️ 需审查'}

---

## 📦 文件信息

| 项目 | 信息 |
|------|------|
| 文件名 | `{result_data['filename']}` |
| MD5 | `{md5}` |
| 文件大小 | {basic_check.get('size_mb', 0)} MB |
| 文件数量 | {basic_check.get('file_count', 0)} 个 |
| 下载来源 | {result_data['download_url']} |

---

## 🔍 基础安全检查

| 检查项 | 结果 |
|--------|------|
| 文件完整性 | {'✅ 通过' if basic_check.get('is_valid_zip', False) else '❌ 失败'} |
| ZIP有效性 | {'✅ 有效' if basic_check.get('is_valid_zip', False) else '❌ 无效'} |
| 可疑文件数 | {len(basic_check.get('suspicious_files', []))} 个 |
"""
    
    if basic_check.get('suspicious_files'):
        report += "\n### ⚠️ 发现的可疑文件\n\n"
        for file in basic_check['suspicious_files'][:10]:
            report += f"- `{file}`\n"
    
    report += "\n---\n\n## 🛡️ 静态安全分析（规则引擎）\n\n"
    
    score = static_analysis.get('security_score', 0)
    is_safe = static_analysis.get('is_safe', False)
    
    report += f"### 安全评分: {score}/100\n\n"
    report += f"**结论**: {'✅ 安全可用' if is_safe else '⚠️ 需要审查'}\n\n"
    
    # 统计信息
    report += f"**检测统计**:\n"
    report += f"- 总问题数: {static_analysis.get('total_issues', 0)}\n"
    report += f"- 风险文件数: {static_analysis.get('risky_files', 0)}/{result_data.get('files_analyzed', 0)}\n\n"
    
    # 详细发现
    findings = static_analysis.get('findings', {})
    if any(findings.values()):
        report += "### 检测发现详情\n\n"
        
        category_names = {
            'backdoor': '🚨 后门特征',
            'remote_connection': '🌐 远程连接',
            'obfuscation': '🔒 代码混淆',
            'file_operation': '📁 文件操作',
            'database': '🗄️ 数据库操作',
            'upload_download': '⬆️ 上传下载',
            'tracking': '📊 广告统计'
        }
        
        for category, items in findings.items():
            if items:
                report += f"\n**{category_names.get(category, category)}** ({len(items)} 处)\n\n"
                for item in items[:5]:  # 只显示前5个
                    report += f"- `{item['file']}`: {item['matches']} 处匹配\n"
                if len(items) > 5:
                    report += f"- ... 还有 {len(items) - 5} 个文件\n"
                report += "\n"
    
    if static_analysis.get('recommendations'):
        report += "### 安全建议\n\n"
        for rec in static_analysis['recommendations']:
            report += f"- {rec}\n"
        report += "\n"
    
    if static_analysis.get('files_to_remove'):
        report += "### 建议移除的文件\n\n"
        for file in list(set(static_analysis['files_to_remove']))[:20]:
            report += f"- `{file}`\n"
        if len(static_analysis['files_to_remove']) > 20:
            report += f"- ... 还有 {len(static_analysis['files_to_remove']) - 20} 个文件\n"
        report += "\n"
    
    if static_analysis.get('summary'):
        report += f"### 总结\n\n{static_analysis['summary']}\n\n"
    
    report += "---\n\n"
    report += f"## 📊 检测统计\n\n"
    report += f"- **分析文件数**: {result_data.get('files_analyzed', 0)}\n"
    report += f"- **检测方式**: 基础检查 + 静态规则分析\n"
    report += f"- **检测工具**: Python脚本 + 规则引擎\n"
    report += f"- **检测日期**: {result_data.get('check_time', 'N/A')}\n"
    
    report += "\n---\n\n"
    report += f"## ✅ 检测结论\n\n"
    
    if static_analysis.get('is_safe', False) and static_analysis.get('security_score', 0) >= 95:
        report += f"✅ **通过检测**\n\n"
        report += f"此版本（{version}）经过静态规则分析，未发现明显的安全风险，建议可以使用。\n\n"
        report += f"**MD5**: `{md5}`\n\n"
        report += "**下一步**: 运行 5_update_and_upload.py 自动更新并上传到GitHub\n"
    else:
        report += f"⚠️ **需要人工审查**\n\n"
        report += f"建议进行详细的人工安全审查后再决定是否使用。\n"
    
    report += "\n---\n\n"
    report += f"**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n"
    report += f"**自动化系统**: BT-Panel Auto-Update System V1.0\n"
    
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

