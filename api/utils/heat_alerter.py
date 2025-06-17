import numpy as np
from typing import Dict, List, Tuple
import logging

class HeatAlerter:
    """热力图告警器，用于检测和告警异常热力值"""
    
    def __init__(self, threshold: float = 0.8):
        """
        初始化热力图告警器
        
        Args:
            threshold: 告警阈值，默认0.8
        """
        self.threshold = threshold
        self.logger = logging.getLogger(__name__)
        
    def analyze_heatmap(self, heatmap: np.ndarray) -> List[Dict]:
        """
        分析热力图，检测异常区域
        
        Args:
            heatmap: 热力图数据
            
        Returns:
            异常区域列表，每个区域包含位置和热度值
        """
        alerts = []
        height, width = heatmap.shape
        
        # 使用滑动窗口检测异常区域
        window_size = 3
        for i in range(height - window_size + 1):
            for j in range(width - window_size + 1):
                window = heatmap[i:i+window_size, j:j+window_size]
                avg_heat = np.mean(window)
                
                if avg_heat > self.threshold:
                    alerts.append({
                        'position': (i, j),
                        'heat_value': float(avg_heat),
                        'window_size': window_size
                    })
        
        return alerts
    
    def get_alert_level(self, heat_value: float) -> str:
        """
        根据热度值确定告警级别
        
        Args:
            heat_value: 热度值
            
        Returns:
            告警级别：'low', 'medium', 'high'
        """
        if heat_value > 0.9:
            return 'high'
        elif heat_value > 0.8:
            return 'medium'
        else:
            return 'low'
    
    def format_alert_message(self, alerts: List[Dict]) -> str:
        """
        格式化告警消息
        
        Args:
            alerts: 告警列表
            
        Returns:
            格式化的告警消息
        """
        if not alerts:
            return "未检测到异常热力值"
            
        message = "检测到以下异常热力区域：\n"
        for alert in alerts:
            level = self.get_alert_level(alert['heat_value'])
            message += f"- 位置: {alert['position']}, 热度值: {alert['heat_value']:.2f}, 级别: {level}\n"
            
        return message 