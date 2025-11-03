#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多AI模型安全分析器
Multi-AI Model Security Analyzer
支持: Gemini, OpenAI, Claude, 文心一言, 通义千问, 智谱GLM, DeepSeek, Kimi, 讯飞星火
"""

import json
import os
import sys
import requests
import time
import hashlib
import hmac
import base64
from datetime import datetime
from urllib.parse import urlencode

class AIAnalyzer:
    """AI安全分析器 - 支持多种AI模型"""
    
    def __init__(self, config_file='config.json'):
        """初始化AI分析器"""
        self.config = self.load_config(config_file)
        self.ai_config = self.config.get('ai_providers', {})
        self.primary_provider = self.ai_config.get('primary_provider', 'gemini')
        self.fallback_enabled = self.ai_config.get('fallback_enabled', True)
        
    def load_config(self, config_file):
        """加载配置"""
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def analyze_code(self, code_sample, file_info=""):
        """
        使用AI分析代码安全性
        
        Args:
            code_sample: 代码样本
            file_info: 文件信息
            
        Returns:
            分析结果字典
        """
        if not self.ai_config.get('enabled', False):
            return self._static_analysis_fallback(code_sample)
        
        # 构建分析提示
        prompt = self._build_security_prompt(code_sample, file_info)
        
        # 尝试主要提供商
        provider_config = self.ai_config.get(self.primary_provider, {})
        if provider_config.get('enabled', False):
            result = self._call_ai_provider(self.primary_provider, prompt, provider_config)
            if result:
                return result
        
        # 如果启用了备用，尝试其他提供商
        if self.fallback_enabled:
            for provider_name, provider_config in self.ai_config.items():
                if provider_name in ['enabled', 'primary_provider', 'fallback_enabled']:
                    continue
                if provider_name == self.primary_provider:
                    continue
                if provider_config.get('enabled', False):
                    print(f"🔄 切换到备用AI: {provider_name}")
                    result = self._call_ai_provider(provider_name, prompt, provider_config)
                    if result:
                        return result
        
        # 所有AI都失败，使用静态分析
        print("⚠️  所有AI提供商不可用，使用静态分析")
        return self._static_analysis_fallback(code_sample)
    
    def _build_security_prompt(self, code_sample, file_info):
        """构建安全分析提示词"""
        return f"""你是一个专业的代码安全审计专家。请分析以下BT（宝塔）面板代码的安全性。

文件信息：{file_info}

代码内容：
```
{code_sample[:8000]}  # 限制长度
```

请从以下角度分析：
1. 后门风险（远程连接、命令执行、数据上传）
2. 恶意代码（病毒、木马、挖矿程序）
3. 隐私泄露（未授权的数据收集）
4. 广告追踪（广告展示、行为追踪）
5. 安全漏洞（SQL注入、命令注入等）

请以JSON格式返回分析结果：
{{
    "security_score": 85,
    "risk_level": "low/medium/high",
    "findings": [
        {{"type": "后门", "severity": "high", "description": "...", "line": 123}},
        ...
    ],
    "recommendation": "总体评价和建议",
    "safe_to_use": true/false
}}"""
    
    def _call_ai_provider(self, provider_name, prompt, provider_config):
        """调用AI提供商"""
        try:
            if provider_name == 'gemini':
                return self._call_gemini(prompt, provider_config)
            elif provider_name == 'openai':
                return self._call_openai(prompt, provider_config)
            elif provider_name == 'claude':
                return self._call_claude(prompt, provider_config)
            elif provider_name == 'qianwen':
                return self._call_qianwen(prompt, provider_config)
            elif provider_name == 'wenxin':
                return self._call_wenxin(prompt, provider_config)
            elif provider_name == 'zhipu':
                return self._call_zhipu(prompt, provider_config)
            elif provider_name == 'deepseek':
                return self._call_deepseek(prompt, provider_config)
            elif provider_name == 'kimi':
                return self._call_kimi(prompt, provider_config)
            elif provider_name == 'xunfei':
                return self._call_xunfei(prompt, provider_config)
            else:
                print(f"❌ 未知的AI提供商: {provider_name}")
                return None
        except Exception as e:
            print(f"❌ {provider_name} 调用失败: {e}")
            return None
    
    def _call_gemini(self, prompt, config):
        """调用Google Gemini"""
        api_key = config.get('api_key')
        model = config.get('model', 'gemini-2.0-flash-exp')
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            text = data['candidates'][0]['content']['parts'][0]['text']
            return self._parse_ai_response(text, 'gemini')
        else:
            print(f"❌ Gemini API错误: {response.status_code}")
            return None
    
    def _call_openai(self, prompt, config):
        """调用OpenAI GPT"""
        api_key = config.get('api_key')
        model = config.get('model', 'gpt-4-turbo-preview')
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个专业的代码安全审计专家。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }
        
        response = requests.post('https://api.openai.com/v1/chat/completions', 
                               headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            text = data['choices'][0]['message']['content']
            return self._parse_ai_response(text, 'openai')
        else:
            print(f"❌ OpenAI API错误: {response.status_code}")
            return None
    
    def _call_claude(self, prompt, config):
        """调用Anthropic Claude"""
        api_key = config.get('api_key')
        model = config.get('model', 'claude-3-opus-20240229')
        
        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }
        
        payload = {
            "model": model,
            "max_tokens": 4096,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post('https://api.anthropic.com/v1/messages',
                               headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            text = data['content'][0]['text']
            return self._parse_ai_response(text, 'claude')
        else:
            print(f"❌ Claude API错误: {response.status_code}")
            return None
    
    def _call_qianwen(self, prompt, config):
        """调用阿里通义千问"""
        api_key = config.get('api_key')
        model = config.get('model', 'qwen-max')
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": model,
            "input": {
                "messages": [
                    {"role": "system", "content": "你是一个专业的代码安全审计专家。"},
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {
                "result_format": "message"
            }
        }
        
        response = requests.post('https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
                               headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            text = data['output']['choices'][0]['message']['content']
            return self._parse_ai_response(text, 'qianwen')
        else:
            print(f"❌ 通义千问API错误: {response.status_code}")
            return None
    
    def _call_wenxin(self, prompt, config):
        """调用百度文心一言"""
        api_key = config.get('api_key')
        secret_key = config.get('secret_key')
        
        # 获取access_token
        auth_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"
        auth_response = requests.get(auth_url)
        access_token = auth_response.json().get('access_token')
        
        if not access_token:
            print("❌ 文心一言获取token失败")
            return None
        
        url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro?access_token={access_token}"
        
        payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            text = data.get('result', '')
            return self._parse_ai_response(text, 'wenxin')
        else:
            print(f"❌ 文心一言API错误: {response.status_code}")
            return None
    
    def _call_zhipu(self, prompt, config):
        """调用智谱GLM"""
        api_key = config.get('api_key')
        model = config.get('model', 'glm-4')
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个专业的代码安全审计专家。"},
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post('https://open.bigmodel.cn/api/paas/v4/chat/completions',
                               headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            text = data['choices'][0]['message']['content']
            return self._parse_ai_response(text, 'zhipu')
        else:
            print(f"❌ 智谱GLM API错误: {response.status_code}")
            return None
    
    def _call_deepseek(self, prompt, config):
        """调用DeepSeek"""
        api_key = config.get('api_key')
        model = config.get('model', 'deepseek-chat')
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个专业的代码安全审计专家。"},
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post('https://api.deepseek.com/v1/chat/completions',
                               headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            text = data['choices'][0]['message']['content']
            return self._parse_ai_response(text, 'deepseek')
        else:
            print(f"❌ DeepSeek API错误: {response.status_code}")
            return None
    
    def _call_kimi(self, prompt, config):
        """调用Kimi (月之暗面)"""
        api_key = config.get('api_key')
        model = config.get('model', 'moonshot-v1-8k')
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个专业的代码安全审计专家。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }
        
        response = requests.post('https://api.moonshot.cn/v1/chat/completions',
                               headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            text = data['choices'][0]['message']['content']
            return self._parse_ai_response(text, 'kimi')
        else:
            print(f"❌ Kimi API错误: {response.status_code}")
            return None
    
    def _call_xunfei(self, prompt, config):
        """调用讯飞星火（WebSocket方式，此处简化为HTTP模拟）"""
        # 讯飞星火使用WebSocket，这里提供简化版本
        print("⚠️  讯飞星火需要WebSocket实现，当前版本暂不支持")
        print("   建议使用其他AI提供商")
        return None
    
    def _parse_ai_response(self, text, provider):
        """解析AI响应"""
        try:
            # 尝试从响应中提取JSON
            # AI通常会返回包含代码块的markdown，需要提取JSON部分
            if '```json' in text:
                json_start = text.find('```json') + 7
                json_end = text.find('```', json_start)
                json_text = text[json_start:json_end].strip()
            elif '```' in text:
                json_start = text.find('```') + 3
                json_end = text.find('```', json_start)
                json_text = text[json_start:json_end].strip()
            elif '{' in text and '}' in text:
                json_start = text.find('{')
                json_end = text.rfind('}') + 1
                json_text = text[json_start:json_end]
            else:
                json_text = text
            
            result = json.loads(json_text)
            result['ai_provider'] = provider
            result['ai_response_time'] = datetime.now().isoformat()
            return result
            
        except json.JSONDecodeError:
            # 如果无法解析JSON，返回原始文本
            print(f"⚠️  {provider} 返回格式异常，尝试解析文本...")
            return {
                'security_score': 75,
                'risk_level': 'medium',
                'findings': [],
                'recommendation': text[:500],
                'safe_to_use': True,
                'ai_provider': provider,
                'parse_failed': True
            }
    
    def _static_analysis_fallback(self, code_sample):
        """静态分析备用方案"""
        # 简化的静态分析
        score = 80
        findings = []
        
        # 检测高危模式
        dangerous_patterns = [
            ('eval(', '动态代码执行'),
            ('exec(', '动态代码执行'),
            ('__import__', '动态导入'),
            ('os.system', '系统命令执行'),
            ('subprocess', '子进程执行'),
        ]
        
        for pattern, desc in dangerous_patterns:
            if pattern in code_sample:
                findings.append({
                    'type': '潜在风险',
                    'severity': 'medium',
                    'description': f'发现{desc}: {pattern}'
                })
                score -= 5
        
        return {
            'security_score': max(score, 0),
            'risk_level': 'low' if score >= 80 else 'medium',
            'findings': findings,
            'recommendation': '静态分析完成，建议结合人工审查',
            'safe_to_use': score >= 70,
            'ai_provider': 'static_analysis',
            'is_fallback': True
        }
    
    def batch_analyze_files(self, file_list, max_files=10):
        """
        批量分析文件
        
        Args:
            file_list: 文件路径列表
            max_files: 最大分析文件数
            
        Returns:
            分析结果列表
        """
        results = []
        analyzed_count = 0
        
        print(f"📊 批量分析 {len(file_list)} 个文件（最多分析{max_files}个）")
        
        for filepath in file_list[:max_files]:
            if analyzed_count >= max_files:
                break
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if len(content) > 100:  # 只分析有实质内容的文件
                    print(f"🔍 分析: {filepath}")
                    result = self.analyze_code(content, filepath)
                    if result:
                        result['file'] = filepath
                        results.append(result)
                        analyzed_count += 1
                    
                    # 避免API限流
                    time.sleep(1)
                    
            except Exception as e:
                print(f"⚠️  无法分析 {filepath}: {e}")
                continue
        
        print(f"✅ 已分析 {analyzed_count} 个文件")
        return results


def test_ai_providers():
    """测试所有AI提供商"""
    print("=" * 70)
    print("🧪 测试所有AI提供商")
    print("=" * 70)
    
    analyzer = AIAnalyzer()
    
    test_code = """
    def process_user_input(data):
        # 测试代码
        result = eval(data)
        return result
    """
    
    providers = analyzer.ai_config.keys()
    for provider in providers:
        if provider in ['enabled', 'primary_provider', 'fallback_enabled']:
            continue
        
        config = analyzer.ai_config.get(provider, {})
        if config.get('enabled', False):
            print(f"\n📡 测试 {provider.upper()}...")
            result = analyzer._call_ai_provider(provider, 
                                               analyzer._build_security_prompt(test_code, "test.py"),
                                               config)
            if result:
                print(f"✅ {provider} 可用 - 评分: {result.get('security_score', 'N/A')}")
            else:
                print(f"❌ {provider} 不可用")
        else:
            print(f"⚪ {provider} 未启用")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_ai_providers()
    else:
        print("用法: python3 ai_analyzer.py test")

