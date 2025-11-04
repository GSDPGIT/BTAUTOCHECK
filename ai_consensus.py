#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BTAUTOCHECK AI共识分析引擎
AI Consensus Analysis Engine
"""

import json
import statistics
from ai_analyzer import AIAnalyzer

class AIConsensusAnalyzer:
    """AI共识分析器 - 使用多个AI模型进行交叉验证"""
    
    def __init__(self, config_file='config.json'):
        self.analyzer = AIAnalyzer(config_file)
        self.config = self.analyzer.config
    
    def analyze_with_consensus(self, code_sample, file_info="", min_ais=2, max_ais=3):
        """
        使用多个AI进行共识分析
        
        Args:
            code_sample: 代码样本
            file_info: 文件信息
            min_ais: 最少使用的AI数量
            max_ais: 最多使用的AI数量
            
        Returns:
            共识分析结果
        """
        ai_config = self.config.get('ai_providers', {})
        
        if not ai_config.get('enabled', False):
            return {
                'consensus_available': False,
                'message': 'AI未启用'
            }
        
        # 获取启用的AI列表
        enabled_ais = []
        for provider, provider_config in ai_config.items():
            if provider in ['enabled', 'primary_provider', 'fallback_enabled']:
                continue
            if isinstance(provider_config, dict) and provider_config.get('enabled', False):
                enabled_ais.append(provider)
        
        if len(enabled_ais) < min_ais:
            return {
                'consensus_available': False,
                'message': f'至少需要{min_ais}个AI，当前只有{len(enabled_ais)}个启用'
            }
        
        # 限制AI数量
        ais_to_use = enabled_ais[:max_ais]
        
        print(f"\n🤖 AI共识分析")
        print(f"参与AI: {', '.join(ais_to_use)}")
        print("=" * 60)
        
        # 调用多个AI进行分析
        results = []
        for ai_provider in ais_to_use:
            try:
                print(f"🔍 正在调用 {ai_provider}...")
                
                provider_config = ai_config.get(ai_provider, {})
                prompt = self.analyzer._build_security_prompt(code_sample, file_info)
                
                result = self.analyzer._call_ai_provider(ai_provider, prompt, provider_config)
                
                if result:
                    result['provider'] = ai_provider
                    results.append(result)
                    print(f"✅ {ai_provider}: 评分 {result.get('security_score', 'N/A')}")
                else:
                    print(f"❌ {ai_provider}: 调用失败")
                    
            except Exception as e:
                print(f"❌ {ai_provider} 异常: {e}")
                continue
        
        if len(results) < min_ais:
            return {
                'consensus_available': False,
                'message': f'只有{len(results)}个AI成功响应，不足{min_ais}个'
            }
        
        # 进行共识分析
        consensus = self._calculate_consensus(results)
        
        print(f"\n📊 共识分析结果:")
        print(f"  平均评分: {consensus['consensus_score']}")
        print(f"  一致性: {consensus['agreement_level']}")
        print(f"  共同发现: {len(consensus['common_findings'])}个")
        print("=" * 60)
        
        return consensus
    
    def _calculate_consensus(self, results):
        """计算AI共识"""
        # 提取评分
        scores = [r.get('security_score', 0) for r in results]
        
        # 计算一致性
        if len(scores) >= 2:
            score_std = statistics.stdev(scores)
            if score_std < 5:
                agreement_level = 'high'  # 高度一致
                agreement_text = '高度一致'
            elif score_std < 10:
                agreement_level = 'medium'  # 中等一致
                agreement_text = '中等一致'
            else:
                agreement_level = 'low'  # 分歧较大
                agreement_text = '分歧较大'
        else:
            score_std = 0
            agreement_level = 'unknown'
            agreement_text = '无法判断'
        
        # 找出共同发现的问题
        common_findings = self._find_common_findings(results)
        divergent_findings = self._find_divergent_findings(results)
        
        # 综合评分（取平均值）
        consensus_score = round(statistics.mean(scores), 1) if scores else 0
        
        # 风险等级共识
        risk_levels = [r.get('risk_level', 'unknown') for r in results]
        consensus_risk = max(set(risk_levels), key=risk_levels.count)  # 多数投票
        
        return {
            'consensus_available': True,
            'total_ais': len(results),
            'consensus_score': consensus_score,
            'score_std_dev': round(score_std, 2),
            'agreement_level': agreement_level,
            'agreement_text': agreement_text,
            'consensus_risk': consensus_risk,
            'individual_results': results,
            'common_findings': common_findings,
            'divergent_findings': divergent_findings,
            'recommendation': self._generate_recommendation(consensus_score, agreement_level, common_findings)
        }
    
    def _find_common_findings(self, results):
        """找出所有AI都发现的问题"""
        if len(results) < 2:
            return []
        
        # 收集所有findings
        all_findings = []
        for r in results:
            findings = r.get('findings', [])
            for f in findings:
                if isinstance(f, dict):
                    all_findings.append(f.get('description', str(f)))
                else:
                    all_findings.append(str(f))
        
        # 找出出现次数 >= 结果数量的问题（所有AI都发现）
        from collections import Counter
        finding_counts = Counter(all_findings)
        
        common = [
            {'description': finding, 'agreement_count': count}
            for finding, count in finding_counts.items()
            if count >= len(results)  # 所有AI都发现
        ]
        
        return common
    
    def _find_divergent_findings(self, results):
        """找出只有部分AI发现的问题"""
        if len(results) < 2:
            return []
        
        # 收集所有findings
        all_findings = []
        for r in results:
            findings = r.get('findings', [])
            for f in findings:
                if isinstance(f, dict):
                    all_findings.append(f.get('description', str(f)))
                else:
                    all_findings.append(str(f))
        
        # 找出出现次数 < 结果数量的问题（部分AI发现）
        from collections import Counter
        finding_counts = Counter(all_findings)
        
        divergent = [
            {'description': finding, 'agreement_count': count, 'total_ais': len(results)}
            for finding, count in finding_counts.items()
            if 1 <= count < len(results)  # 部分AI发现
        ]
        
        # 按同意数量排序
        divergent.sort(key=lambda x: x['agreement_count'], reverse=True)
        
        return divergent
    
    def _generate_recommendation(self, consensus_score, agreement_level, common_findings):
        """生成建议"""
        if consensus_score >= 80:
            if agreement_level == 'high':
                return '✅ 所有AI一致认为安全，强烈推荐升级'
            else:
                return '✅ 整体安全，但AI之间存在分歧，建议人工审查后升级'
        
        elif consensus_score >= 70:
            if len(common_findings) > 0:
                return '⚠️ AI一致发现了一些问题，建议审查后再升级'
            else:
                return '⚠️ 评分中等，AI之间有分歧，建议测试环境验证'
        
        else:
            return '❌ 评分较低，不建议升级，需要详细审查'

# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("🤖 AI共识分析引擎测试")
    print("=" * 60)
    
    consensus = AIConsensusAnalyzer()
    
    test_code = """
import os
import sys

def process_data(user_input):
    # 处理用户输入
    result = eval(user_input)  # 潜在风险
    return result

def upload_data(data):
    import requests
    requests.post('http://analytics.bt.cn/collect', json=data)
"""
    
    result = consensus.analyze_with_consensus(test_code, "test.py", min_ais=2, max_ais=3)
    
    if result.get('consensus_available'):
        print(f"\n📊 共识结果:")
        print(f"  参与AI数: {result['total_ais']}")
        print(f"  共识评分: {result['consensus_score']}")
        print(f"  一致性: {result['agreement_text']}")
        print(f"  共同发现: {len(result['common_findings'])}个")
        print(f"  分歧问题: {len(result['divergent_findings'])}个")
        print(f"\n💡 建议: {result['recommendation']}")
    else:
        print(f"\n⚠️ {result['message']}")

