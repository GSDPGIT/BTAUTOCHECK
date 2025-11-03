#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全配置管理工具 - API Key加密
Secure Configuration Manager - API Key Encryption
"""

import os
import sys
import json
import base64
import hashlib
from cryptography.fernet import Fernet
from getpass import getpass

class SecureConfig:
    """安全配置管理器"""
    
    def __init__(self, config_file='config.json', key_file='.config.key'):
        self.config_file = config_file
        self.key_file = key_file
        self.cipher = None
        
    def _get_or_create_key(self):
        """获取或创建加密密钥"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            os.chmod(self.key_file, 0o600)  # 只有所有者可读写
            return key
    
    def _init_cipher(self):
        """初始化加密器"""
        if not self.cipher:
            key = self._get_or_create_key()
            self.cipher = Fernet(key)
    
    def encrypt_value(self, value):
        """
        加密值
        
        Args:
            value: 要加密的字符串
            
        Returns:
            加密后的字符串
        """
        self._init_cipher()
        if not value or value.startswith('ENC['):
            return value
        
        encrypted = self.cipher.encrypt(value.encode())
        return f"ENC[{encrypted.decode()}]"
    
    def decrypt_value(self, value):
        """
        解密值
        
        Args:
            value: 加密的字符串
            
        Returns:
            解密后的字符串
        """
        if not value or not value.startswith('ENC['):
            return value
        
        self._init_cipher()
        encrypted_data = value[4:-1]  # 去掉 ENC[ 和 ]
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        return decrypted.decode()
    
    def encrypt_config(self):
        """加密配置文件中的敏感信息"""
        print("="*60)
        print("🔐 加密配置文件")
        print("="*60)
        
        if not os.path.exists(self.config_file):
            print(f"❌ 配置文件不存在: {self.config_file}")
            return False
        
        # 读取配置
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 需要加密的字段
        sensitive_fields = [
            ('gemini_api_key',),
            ('github_token',),
            ('notifications', 'email', 'smtp_password'),
            ('notifications', 'serverchan', 'sendkey'),
            ('notifications', 'bark', 'device_key'),
            ('notifications', 'telegram', 'bot_token'),
        ]
        
        # 加密敏感字段
        changed = False
        for field_path in sensitive_fields:
            obj = config
            for key in field_path[:-1]:
                if key in obj:
                    obj = obj[key]
                else:
                    break
            else:
                final_key = field_path[-1]
                if final_key in obj and obj[final_key]:
                    original = obj[final_key]
                    encrypted = self.encrypt_value(original)
                    if original != encrypted:
                        obj[final_key] = encrypted
                        changed = True
                        print(f"✅ 已加密: {' -> '.join(field_path)}")
        
        if changed:
            # 保存加密后的配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            print(f"\n✅ 配置已加密并保存到: {self.config_file}")
            print(f"🔑 密钥文件: {self.key_file} (请妥善保管)")
            return True
        else:
            print("\nℹ️  配置已是加密状态，无需再次加密")
            return True
    
    def decrypt_config(self):
        """解密配置文件"""
        print("="*60)
        print("🔓 解密配置文件")
        print("="*60)
        
        if not os.path.exists(self.config_file):
            print(f"❌ 配置文件不存在: {self.config_file}")
            return False
        
        # 读取配置
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 解密所有加密字段
        def decrypt_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str):
                        obj[key] = self.decrypt_value(value)
                    elif isinstance(value, (dict, list)):
                        decrypt_recursive(value)
            elif isinstance(list):
                for i, item in enumerate(obj):
                    if isinstance(item, str):
                        obj[i] = self.decrypt_value(item)
                    elif isinstance(item, (dict, list)):
                        decrypt_recursive(item)
        
        decrypt_recursive(config)
        
        # 保存解密后的配置
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        print(f"✅ 配置已解密并保存到: {self.config_file}")
        print(f"⚠️  请注意：配置文件现在包含明文密钥，请谨慎处理")
        return True
    
    def load_config(self):
        """
        加载配置（自动解密）
        
        Returns:
            配置字典
        """
        if not os.path.exists(self.config_file):
            return {}
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 自动解密
        def decrypt_recursive(obj):
            if isinstance(obj, dict):
                result = {}
                for key, value in obj.items():
                    if isinstance(value, str):
                        result[key] = self.decrypt_value(value)
                    elif isinstance(value, (dict, list)):
                        result[key] = decrypt_recursive(value)
                    else:
                        result[key] = value
                return result
            elif isinstance(obj, list):
                return [decrypt_recursive(item) if isinstance(item, (dict, list, str)) else item 
                       for item in obj]
            elif isinstance(obj, str):
                return self.decrypt_value(obj)
            return obj
        
        return decrypt_recursive(config)
    
    def set_env_from_config(self):
        """从配置设置环境变量"""
        config = self.load_config()
        
        # 设置常用的环境变量
        env_map = {
            'gemini_api_key': 'GEMINI_API_KEY',
            'github_token': 'GITHUB_TOKEN',
        }
        
        for config_key, env_key in env_map.items():
            if config_key in config and config[config_key]:
                os.environ[env_key] = config[config_key]
                print(f"✅ 已设置环境变量: {env_key}")


def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='BTAUTOCHECK安全配置管理')
    parser.add_argument('action', choices=['encrypt', 'decrypt', 'load'],
                       help='操作: encrypt(加密), decrypt(解密), load(加载测试)')
    
    args = parser.parse_args()
    
    manager = SecureConfig()
    
    if args.action == 'encrypt':
        manager.encrypt_config()
    elif args.action == 'decrypt':
        manager.decrypt_config()
    elif args.action == 'load':
        print("="*60)
        print("🔍 加载并解密配置")
        print("="*60)
        config = manager.load_config()
        print("\n📋 配置内容 (敏感信息已解密):")
        print(json.dumps(config, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()

