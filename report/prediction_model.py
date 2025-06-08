import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Any, Tuple
import logging
from datetime import datetime, timedelta

class PredictionModel:
    def __init__(self):
        """
        初始化预测模型
        """
        self.logger = logging.getLogger(__name__)
        self.heat_model = LinearRegression()
        self.sentiment_model = LinearRegression()
        self.scaler = StandardScaler()
        
    def predict_heat_trend(self, data: List[Dict[str, Any]], days: int = 7) -> Dict[str, Any]:
        """
        预测热度趋势
        
        Args:
            data: 历史热度数据
            days: 预测天数
            
        Returns:
            预测结果
        """
        try:
            # 准备数据
            df = pd.DataFrame(data)
            X = np.array(range(len(df))).reshape(-1, 1)
            y = df['daily_avg'].values
            
            # 标准化数据
            X_scaled = self.scaler.fit_transform(X)
            
            # 训练模型
            self.heat_model.fit(X_scaled, y)
            
            # 生成预测数据
            future_X = np.array(range(len(df), len(df) + days)).reshape(-1, 1)
            future_X_scaled = self.scaler.transform(future_X)
            predictions = self.heat_model.predict(future_X_scaled)
            
            # 计算趋势
            trend = self._calculate_trend(predictions)
            
            return {
                'trend': trend,
                'max_heat': float(np.max(predictions)),
                'min_heat': float(np.min(predictions)),
                'predictions': predictions.tolist()
            }
            
        except Exception as e:
            self.logger.error(f"预测热度趋势时出错: {str(e)}")
            raise
            
    def predict_sentiment_trend(self, data: List[Dict[str, Any]], days: int = 7) -> Dict[str, Any]:
        """
        预测情感趋势
        
        Args:
            data: 历史情感数据
            days: 预测天数
            
        Returns:
            预测结果
        """
        try:
            # 准备数据
            df = pd.DataFrame(data)
            X = np.array(range(len(df))).reshape(-1, 1)
            y = df['daily_avg'].values
            
            # 标准化数据
            X_scaled = self.scaler.fit_transform(X)
            
            # 训练模型
            self.sentiment_model.fit(X_scaled, y)
            
            # 生成预测数据
            future_X = np.array(range(len(df), len(df) + days)).reshape(-1, 1)
            future_X_scaled = self.scaler.transform(future_X)
            predictions = self.sentiment_model.predict(future_X_scaled)
            
            # 计算趋势
            trend = self._calculate_trend(predictions)
            
            # 计算情感分布
            positive = np.mean(predictions > 0.5)
            negative = np.mean(predictions < -0.5)
            neutral = 1 - positive - negative
            
            return {
                'trend': trend,
                'positive': float(positive),
                'negative': float(negative),
                'neutral': float(neutral),
                'predictions': predictions.tolist()
            }
            
        except Exception as e:
            self.logger.error(f"预测情感趋势时出错: {str(e)}")
            raise
            
    def predict_alert_probability(self, heat_data: List[Dict[str, Any]], 
                                sentiment_data: List[Dict[str, Any]], 
                                days: int = 7) -> Dict[str, Any]:
        """
        预测预警概率
        
        Args:
            heat_data: 历史热度数据
            sentiment_data: 历史情感数据
            days: 预测天数
            
        Returns:
            预测结果
        """
        try:
            # 准备数据
            heat_df = pd.DataFrame(heat_data)
            sentiment_df = pd.DataFrame(sentiment_data)
            
            # 计算预警概率
            high_prob = self._calculate_alert_probability(
                heat_df['daily_avg'].values,
                sentiment_df['daily_avg'].values,
                'high'
            )
            
            medium_prob = self._calculate_alert_probability(
                heat_df['daily_avg'].values,
                sentiment_df['daily_avg'].values,
                'medium'
            )
            
            low_prob = self._calculate_alert_probability(
                heat_df['daily_avg'].values,
                sentiment_df['daily_avg'].values,
                'low'
            )
            
            return {
                'high_probability': float(high_prob),
                'medium_probability': float(medium_prob),
                'low_probability': float(low_prob)
            }
            
        except Exception as e:
            self.logger.error(f"预测预警概率时出错: {str(e)}")
            raise
            
    def _calculate_trend(self, data: np.ndarray) -> str:
        """
        计算数据趋势
        
        Args:
            data: 数据数组
            
        Returns:
            趋势描述
        """
        if len(data) < 2:
            return "数据不足"
            
        # 计算变化率
        change_rate = (data[-1] - data[0]) / data[0] * 100
        
        if change_rate > 5:
            return "显著上升"
        elif change_rate > 0:
            return "轻微上升"
        elif change_rate > -5:
            return "轻微下降"
        else:
            return "显著下降"
            
    def _calculate_alert_probability(self, heat_data: np.ndarray, 
                                   sentiment_data: np.ndarray,
                                   alert_level: str) -> float:
        """
        计算预警概率
        
        Args:
            heat_data: 热度数据
            sentiment_data: 情感数据
            alert_level: 预警级别
            
        Returns:
            预警概率
        """
        # 设置阈值
        thresholds = {
            'high': {'heat': 0.8, 'sentiment': -0.6},
            'medium': {'heat': 0.6, 'sentiment': -0.4},
            'low': {'heat': 0.4, 'sentiment': -0.2}
        }
        
        # 计算概率
        heat_prob = np.mean(heat_data > thresholds[alert_level]['heat'])
        sentiment_prob = np.mean(sentiment_data < thresholds[alert_level]['sentiment'])
        
        return (heat_prob + sentiment_prob) / 2 