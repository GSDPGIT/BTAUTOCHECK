#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Gemini API连接
"""

import requests
import json

# 加载配置
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

API_KEY = config['gemini_api_key']
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

print("=" * 60)
print("测试Gemini API连接")
print("=" * 60)
print(f"API Key: {API_KEY[:20]}...{API_KEY[-10:]}")
print()

# 测试请求
test_data = {
    "contents": [{
        "parts": [{
            "text": "你好！请用中文回复：这是一个测试请求，请确认API工作正常。"
        }]
    }]
}

try:
    print("正在发送测试请求...")
    response = requests.post(API_URL, json=test_data, timeout=30)
    
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            text = result['candidates'][0]['content']['parts'][0]['text']
            print("\n✅ API连接成功！")
            print("\nGemini响应:")
            print("=" * 60)
            print(text)
            print("=" * 60)
            print("\n✅ Gemini API配置正确，可以使用！")
        else:
            print("\n⚠️  响应格式异常")
            print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\n❌ API调用失败: {response.status_code}")
        print(f"错误信息: {response.text}")

except Exception as e:
    print(f"\n❌ 连接失败: {e}")
    print("\n请检查:")
    print("1. API Key是否正确")
    print("2. 网络是否可访问Google服务")
    print("3. API Key是否已启用")

print("\n" + "=" * 60)

