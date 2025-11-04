#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BTAUTOCHECK 智能告警规则引擎
Smart Alert Rules Engine
"""

import json
import os
from datetime import datetime, timedelta
from notification import NotificationManager

class AlertRulesEngine:
    """智能告警规则引擎"""
    
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.alert_history_file = 'logs/alert_history.json'
        self.notif_manager = NotificationManager()
    
    def load_config(self):
        """加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置失败: {e}")
            return {}
    
    def should_alert(self, check_result):
        """判断是否应该发送告警"""
        rules = self.config.get('alert_rules', {})
        
        # 如果未配置规则，使用默认行为
        if not rules:
            return self._default_alert_logic(check_result)
        
        # 检查静默时间
        if self._in_silent_hours(rules.get('silent_hours', {})):
            print("🔕 当前在静默时间，不发送告警")
            return False
        
        # 检查各级别规则
        alert_level = None
        matched_rule = None
        
        # 严重告警
        if self._match_critical_rules(check_result, rules.get('critical', {})):
            alert_level = 'critical'
            matched_rule = rules.get('critical', {})
        
        # 警告告警
        elif self._match_warning_rules(check_result, rules.get('warning', {})):
            alert_level = 'warning'
            matched_rule = rules.get('warning', {})
        
        # 信息告警
        elif self._match_info_rules(check_result, rules.get('info', {})):
            alert_level = 'info'
            matched_rule = rules.get('info', {})
        
        if not alert_level:
            return False
        
        # 检查告警去重
        if self._is_duplicate_alert(check_result, alert_level, matched_rule):
            print(f"🔕 告警去重：{alert_level}级别的告警在冷却期内")
            return False
        
        # 发送告警
        return self._send_alert(check_result, alert_level, matched_rule)
    
    def _match_critical_rules(self, result, rule):
        """匹配严重告警规则"""
        if not rule.get('enabled', False):
            return False
        
        conditions = rule.get('conditions', [])
        
        # 评分过低
        if 'score_critical' in conditions:
            threshold = rule.get('score_threshold', 60)
            score = result.get('static_analysis', {}).get('security_score', 100)
            if score < threshold:
                return True
        
        # 发现后门
        if 'backdoor_found' in conditions:
            backdoor_count = result.get('static_analysis', {}).get('deduction_details', {}).get('backdoor_critical', {}).get('count', 0)
            if backdoor_count > 0:
                return True
        
        # 高风险文件过多
        if 'high_risk_files' in conditions:
            threshold = rule.get('high_risk_threshold', 50)
            risk_files = result.get('static_analysis', {}).get('risk_files_count', 0)
            if risk_files > threshold:
                return True
        
        return False
    
    def _match_warning_rules(self, result, rule):
        """匹配警告级别规则"""
        if not rule.get('enabled', False):
            return False
        
        conditions = rule.get('conditions', [])
        
        # 评分偏低
        if 'score_warning' in conditions:
            threshold = rule.get('score_threshold', 75)
            score = result.get('static_analysis', {}).get('security_score', 100)
            if score < threshold:
                return True
        
        # AI评分与静态评分差异大
        if 'score_divergence' in conditions:
            static_score = result.get('static_analysis', {}).get('security_score', 0)
            ai_score = result.get('ai_analysis', {}).get('average_score', 0)
            
            if ai_score > 0 and abs(static_score - ai_score) > 15:
                return True
        
        return False
    
    def _match_info_rules(self, result, rule):
        """匹配信息级别规则"""
        if not rule.get('enabled', False):
            return False
        
        conditions = rule.get('conditions', [])
        
        # 发现新版本
        if 'new_version_found' in conditions:
            return True
        
        # 评分提升
        if 'score_improved' in conditions:
            # 对比上一次报告
            prev_score = self._get_previous_score()
            current_score = result.get('static_analysis', {}).get('security_score', 0)
            if prev_score and current_score > prev_score + 5:
                return True
        
        return False
    
    def _in_silent_hours(self, silent_config):
        """检查是否在静默时间"""
        if not silent_config.get('enabled', False):
            return False
        
        now = datetime.now()
        current_time = now.time()
        
        try:
            start_str = silent_config.get('start', '22:00')
            end_str = silent_config.get('end', '08:00')
            
            start_time = datetime.strptime(start_str, '%H:%M').time()
            end_time = datetime.strptime(end_str, '%H:%M').time()
            
            # 处理跨天情况（22:00-08:00）
            if start_time > end_time:
                return current_time >= start_time or current_time < end_time
            else:
                return start_time <= current_time < end_time
        except Exception as e:
            print(f"解析静默时间失败: {e}")
            return False
    
    def _is_duplicate_alert(self, result, alert_level, rule):
        """检查是否是重复告警（去重）"""
        repeat_interval = rule.get('repeat_interval_hours', 24)
        
        # 加载告警历史
        history = self._load_alert_history()
        
        version = result.get('version', 'unknown')
        alert_key = f"{version}_{alert_level}"
        
        if alert_key in history:
            last_alert_time = datetime.fromisoformat(history[alert_key]['last_alert'])
            time_since_last = datetime.now() - last_alert_time
            
            if time_since_last < timedelta(hours=repeat_interval):
                return True  # 在冷却期内
        
        return False
    
    def _send_alert(self, result, alert_level, rule):
        """发送告警"""
        version = result.get('version', 'unknown')
        static_score = result.get('static_analysis', {}).get('security_score', 0)
        ai_score = result.get('ai_analysis', {}).get('average_score', 0)
        
        # 构建告警消息
        title = self._build_alert_title(alert_level, version, static_score)
        message = self._build_alert_message(result, alert_level)
        
        # 选择通知渠道
        channels = rule.get('channels', ['email'])
        
        # 发送通知
        try:
            for channel in channels:
                if channel == 'email':
                    self.notif_manager.send_email(title, message)
                elif channel == 'serverchan':
                    self.notif_manager.send_serverchan(title, message)
                elif channel == 'telegram':
                    self.notif_manager.send_telegram(title, message)
                elif channel == 'webhook':
                    self.notif_manager.send_webhook(title, message)
                # 其他渠道...
            
            # 记录告警历史
            self._record_alert(version, alert_level)
            
            print(f"✅ 告警已发送：{alert_level} - {version}")
            return True
            
        except Exception as e:
            print(f"❌ 发送告警失败: {e}")
            return False
    
    def _build_alert_title(self, level, version, score):
        """构建告警标题"""
        icons = {
            'critical': '🔴',
            'warning': '⚠️',
            'info': '📢'
        }
        
        titles = {
            'critical': '严重告警',
            'warning': '安全警告',
            'info': '信息通知'
        }
        
        icon = icons.get(level, '📢')
        title = titles.get(level, '通知')
        
        return f"{icon} BT-Panel {title}: {version} (评分:{score})"
    
    def _build_alert_message(self, result, level):
        """构建告警消息"""
        version = result.get('version', 'unknown')
        static_score = result.get('static_analysis', {}).get('security_score', 0)
        ai_score = result.get('ai_analysis', {}).get('average_score', 0)
        risk_files = result.get('static_analysis', {}).get('risk_files_count', 0)
        
        message = f"""
BT-Panel版本检测报告

版本: {version}
检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

评分信息:
  静态评分: {static_score}/100
  AI评分: {ai_score}/100 {'(未启用)' if ai_score == 0 else ''}

风险统计:
  风险文件数: {risk_files}

"""
        
        # 添加主要问题
        deduction_details = result.get('static_analysis', {}).get('deduction_details', {})
        if deduction_details:
            message += "\n主要问题:\n"
            for category, detail in deduction_details.items():
                count = detail.get('count', 0)
                if count > 0:
                    deduction = detail.get('deduction', 0)
                    message += f"  - {category}: {count}处 (扣{deduction}分)\n"
        
        # 添加建议
        if level == 'critical':
            message += "\n⚠️ 建议: 暂缓升级，等待官方修复或人工审查"
        elif level == 'warning':
            message += "\n💡 建议: 建议测试环境验证后再升级"
        else:
            message += "\n✅ 建议: 可以安全升级"
        
        message += f"\n\n查看完整报告: http://你的IP:5000/reports"
        
        return message
    
    def _load_alert_history(self):
        """加载告警历史"""
        if not os.path.exists(self.alert_history_file):
            return {}
        
        try:
            with open(self.alert_history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _record_alert(self, version, level):
        """记录告警历史"""
        history = self._load_alert_history()
        
        alert_key = f"{version}_{level}"
        history[alert_key] = {
            'version': version,
            'level': level,
            'last_alert': datetime.now().isoformat(),
            'count': history.get(alert_key, {}).get('count', 0) + 1
        }
        
        # 保存
        os.makedirs(os.path.dirname(self.alert_history_file), exist_ok=True)
        try:
            with open(self.alert_history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存告警历史失败: {e}")
    
    def _get_previous_score(self):
        """获取上一次的评分"""
        # 简单实现：从文件读取
        try:
            import glob
            reports = glob.glob('downloads/security_report_*.json')
            reports.sort(key=os.path.getmtime, reverse=True)
            
            if len(reports) >= 2:
                with open(reports[1], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('static_analysis', {}).get('security_score', 0)
        except:
            pass
        
        return None
    
    def _default_alert_logic(self, result):
        """默认告警逻辑（未配置规则时）"""
        score = result.get('static_analysis', {}).get('security_score', 100)
        
        # 评分低于阈值就告警
        threshold = self.config.get('security_threshold', 80)
        
        if score < threshold:
            title = f"⚠️ BT-Panel安全警告: 评分{score}低于阈值{threshold}"
            message = f"版本{result.get('version')}的安全评分为{score}，低于设定阈值{threshold}，请查看详细报告。"
            
            try:
                self.notif_manager.send_all(title, message)
                return True
            except:
                return False
        
        return False

# 测试
if __name__ == '__main__':
    engine = AlertRulesEngine()
    
    # 模拟检测结果
    test_result = {
        'version': '11.3.0',
        'static_analysis': {
            'security_score': 65,
            'risk_files_count': 120,
            'deduction_details': {
                'backdoor_critical': {'count': 2, 'deduction': 20},
                'data_leak': {'count': 15, 'deduction': 10}
            }
        },
        'ai_analysis': {
            'average_score': 70
        }
    }
    
    print("=" * 60)
    print("🔔 智能告警规则引擎测试")
    print("=" * 60)
    
    if engine.should_alert(test_result):
        print("✅ 触发告警")
    else:
        print("⭕ 未触发告警")

