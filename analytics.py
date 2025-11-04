#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BTAUTOCHECK 数据分析引擎
Analytics Engine for Trend Analysis and Statistics
"""

import json
import os
import glob
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

class AnalyticsEngine:
    """数据分析引擎"""
    
    def __init__(self):
        self.downloads_dir = 'downloads'
        self.config_file = 'config.json'
    
    def get_all_reports_data(self):
        """加载所有历史报告数据"""
        reports = []
        pattern = os.path.join(self.downloads_dir, 'security_report_*.json')
        files = glob.glob(pattern)
        
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 提取关键信息
                    version = data.get('version', 'unknown')
                    check_time = data.get('check_time', '')
                    
                    static_analysis = data.get('static_analysis', {})
                    ai_analysis = data.get('ai_analysis', {})
                    
                    reports.append({
                        'version': version,
                        'check_time': check_time,
                        'static_score': static_analysis.get('security_score', 0),
                        'ai_score': ai_analysis.get('average_score', 0) if ai_analysis else 0,
                        'risk_files': static_analysis.get('risk_files_count', 0),
                        'total_issues': static_analysis.get('total_issues', 0),
                        'file_path': filepath
                    })
            except Exception as e:
                print(f"读取报告失败 {filepath}: {e}")
                continue
        
        # 按时间排序
        reports.sort(key=lambda x: x['check_time'])
        
        return reports
    
    def get_score_trend(self, days=30):
        """获取评分趋势（最近N天）"""
        reports = self.get_all_reports_data()
        
        # 过滤最近N天的数据
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_reports = [
            r for r in reports 
            if self._parse_date(r['check_time']) >= cutoff_date
        ]
        
        if not recent_reports:
            return {
                'dates': [],
                'versions': [],
                'static_scores': [],
                'ai_scores': [],
                'avg_scores': []
            }
        
        # 构建趋势数据
        trend = {
            'dates': [r['check_time'][:10] for r in recent_reports],  # YYYY-MM-DD
            'versions': [r['version'] for r in recent_reports],
            'static_scores': [r['static_score'] for r in recent_reports],
            'ai_scores': [r['ai_score'] for r in recent_reports],
            'avg_scores': [
                (r['static_score'] + r['ai_score']) / 2 if r['ai_score'] > 0 else r['static_score']
                for r in recent_reports
            ]
        }
        
        return trend
    
    def get_issue_distribution(self):
        """获取问题类型分布（饼图数据）"""
        latest_report = self._get_latest_report()
        
        if not latest_report:
            return {}
        
        static_analysis = latest_report.get('static_analysis', {})
        deduction_details = static_analysis.get('deduction_details', {})
        
        # 构建分类数据
        distribution = {}
        
        category_map = {
            'backdoor_critical': '高危后门',
            'obfuscation_critical': '代码混淆',
            'tracking_ads': '追踪广告',
            'data_leak': '数据泄露',
            'sql_injection_risk': 'SQL注入',
            'suspicious_domain': '可疑域名',
            'privilege_escalation': '权限提升',
            'dangerous_functions': '危险函数',
            'command_execution': '命令执行',
            'remote_connection': '远程连接',
            'file_transfer': '文件传输'
        }
        
        for key, label in category_map.items():
            detail = deduction_details.get(key, {})
            count = detail.get('count', 0)
            if count > 0:
                distribution[label] = count
        
        return distribution
    
    def get_ai_usage_stats(self):
        """获取AI使用统计"""
        reports = self.get_all_reports_data()
        
        ai_stats = defaultdict(lambda: {'count': 0, 'total_score': 0, 'success': 0})
        
        for report in reports:
            filepath = report['file_path']
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    ai_analysis = data.get('ai_analysis', {})
                    
                    if ai_analysis:
                        provider = ai_analysis.get('provider', 'unknown')
                        score = ai_analysis.get('average_score', 0)
                        
                        ai_stats[provider]['count'] += 1
                        ai_stats[provider]['total_score'] += score
                        if score > 0:
                            ai_stats[provider]['success'] += 1
            except:
                continue
        
        # 计算平均分
        result = {}
        for provider, stats in ai_stats.items():
            result[provider] = {
                'count': stats['count'],
                'success_rate': (stats['success'] / stats['count'] * 100) if stats['count'] > 0 else 0,
                'avg_score': (stats['total_score'] / stats['count']) if stats['count'] > 0 else 0
            }
        
        return result
    
    def get_check_frequency_stats(self, days=30):
        """获取检测频率统计"""
        reports = self.get_all_reports_data()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_reports = [
            r for r in reports 
            if self._parse_date(r['check_time']) >= cutoff_date
        ]
        
        # 按日期分组统计
        daily_counts = defaultdict(int)
        for r in recent_reports:
            date_key = r['check_time'][:10]
            daily_counts[date_key] += 1
        
        # 填充空白日期
        all_dates = []
        current = cutoff_date.date()
        end = datetime.now().date()
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            all_dates.append(date_str)
            if date_str not in daily_counts:
                daily_counts[date_str] = 0
            current += timedelta(days=1)
        
        return {
            'dates': all_dates,
            'counts': [daily_counts[d] for d in all_dates],
            'total_checks': len(recent_reports),
            'avg_per_day': len(recent_reports) / days if days > 0 else 0
        }
    
    def get_summary_stats(self):
        """获取汇总统计"""
        reports = self.get_all_reports_data()
        
        if not reports:
            return {
                'total_reports': 0,
                'avg_static_score': 0,
                'avg_ai_score': 0,
                'highest_score': 0,
                'lowest_score': 0,
                'total_versions': 0
            }
        
        static_scores = [r['static_score'] for r in reports if r['static_score'] > 0]
        ai_scores = [r['ai_score'] for r in reports if r['ai_score'] > 0]
        all_scores = static_scores + ai_scores
        
        return {
            'total_reports': len(reports),
            'avg_static_score': round(statistics.mean(static_scores), 2) if static_scores else 0,
            'avg_ai_score': round(statistics.mean(ai_scores), 2) if ai_scores else 0,
            'highest_score': max(all_scores) if all_scores else 0,
            'lowest_score': min(all_scores) if all_scores else 0,
            'total_versions': len(set(r['version'] for r in reports)),
            'latest_check': reports[-1]['check_time'] if reports else 'Never'
        }
    
    def _get_latest_report(self):
        """获取最新报告"""
        reports = self.get_all_reports_data()
        if not reports:
            return None
        
        latest = reports[-1]
        filepath = latest['file_path']
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    
    def _parse_date(self, date_str):
        """解析日期字符串"""
        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except:
            try:
                return datetime.strptime(date_str[:10], '%Y-%m-%d')
            except:
                return datetime.now()

# 测试
if __name__ == '__main__':
    engine = AnalyticsEngine()
    
    print("=" * 60)
    print("📊 BTAUTOCHECK 数据分析引擎")
    print("=" * 60)
    
    # 汇总统计
    summary = engine.get_summary_stats()
    print(f"\n📈 汇总统计:")
    print(f"  总报告数: {summary['total_reports']}")
    print(f"  平均静态评分: {summary['avg_static_score']}")
    print(f"  平均AI评分: {summary['avg_ai_score']}")
    print(f"  最高分: {summary['highest_score']}")
    print(f"  最低分: {summary['lowest_score']}")
    
    # 评分趋势
    trend = engine.get_score_trend(30)
    print(f"\n📊 评分趋势（最近30天）:")
    print(f"  数据点: {len(trend['dates'])}")
    
    # 问题分布
    distribution = engine.get_issue_distribution()
    print(f"\n🔍 问题类型分布:")
    for category, count in distribution.items():
        print(f"  {category}: {count}")
    
    # AI使用统计
    ai_stats = engine.get_ai_usage_stats()
    print(f"\n🤖 AI使用统计:")
    for provider, stats in ai_stats.items():
        print(f"  {provider}: {stats['count']}次, 成功率{stats['success_rate']:.1f}%, 平均分{stats['avg_score']:.1f}")
    
    print("\n" + "=" * 60)

