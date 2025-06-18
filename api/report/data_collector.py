from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from typing import Dict, List, Any, Optional
import logging

class ReportDataCollector:
    def __init__(self, db_url: str):
        """
        初始化数据收集器
        
        Args:
            db_url: 数据库连接URL
        """
        self.engine = create_engine(db_url)
        self.logger = logging.getLogger(__name__)
        
    def collect_heat_data(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """
        收集热度数据
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            包含热度数据的字典
        """
        try:
            # 查询热度数据
            query = text("""
                SELECT 
                    DATE(created_at) as date,
                    AVG(heat_score) as daily_avg,
                    MAX(heat_score) as daily_max,
                    MIN(heat_score) as daily_min
                FROM heat_analysis_results
                WHERE created_at BETWEEN :start_time AND :end_time
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
            
            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn, params={
                    'start_time': start_time,
                    'end_time': end_time
                })
            
            # 计算统计数据
            stats = {
                'daily_avg': df['daily_avg'].mean(),
                'daily_max': df['daily_max'].max(),
                'daily_min': df['daily_min'].min(),
                'trend': self._calculate_trend(df['daily_avg']),
                'std': df['daily_avg'].std(),
                'range': df['daily_max'].max() - df['daily_min'].min()
            }
            
            return {
                'stats': stats,
                'daily_data': df.to_dict('records')
            }
            
        except Exception as e:
            self.logger.error(f"收集热度数据时出错: {str(e)}")
            raise
            
    def collect_sentiment_data(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """
        收集情感分析数据
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            包含情感分析数据的字典
        """
        try:
            # 查询情感数据
            query = text("""
                SELECT 
                    DATE(created_at) as date,
                    AVG(sentiment_score) as daily_avg,
                    COUNT(CASE WHEN sentiment = 'positive' THEN 1 END) as positive_count,
                    COUNT(CASE WHEN sentiment = 'negative' THEN 1 END) as negative_count,
                    COUNT(CASE WHEN sentiment = 'neutral' THEN 1 END) as neutral_count
                FROM sentiment_analysis_results
                WHERE created_at BETWEEN :start_time AND :end_time
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
            
            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn, params={
                    'start_time': start_time,
                    'end_time': end_time
                })
            
            # 计算情感分布
            total = df[['positive_count', 'negative_count', 'neutral_count']].sum()
            distribution = {
                'positive': total['positive_count'] / total.sum(),
                'negative': total['negative_count'] / total.sum(),
                'neutral': total['neutral_count'] / total.sum()
            }
            
            # 计算统计数据
            stats = {
                'daily_avg': df['daily_avg'].mean(),
                'trend': self._calculate_trend(df['daily_avg']),
                'std': df['daily_avg'].std(),
                'distribution': distribution
            }
            
            return {
                'stats': stats,
                'daily_data': df.to_dict('records')
            }
            
        except Exception as e:
            self.logger.error(f"收集情感数据时出错: {str(e)}")
            raise
            
    def collect_alert_data(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """
        收集预警数据
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            包含预警数据的字典
        """
        try:
            # 查询预警数据
            query = text("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as alert_count,
                    COUNT(CASE WHEN alert_level = 'high' THEN 1 END) as high_count,
                    COUNT(CASE WHEN alert_level = 'medium' THEN 1 END) as medium_count,
                    COUNT(CASE WHEN alert_level = 'low' THEN 1 END) as low_count
                FROM alert_records
                WHERE created_at BETWEEN :start_time AND :end_time
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
            
            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn, params={
                    'start_time': start_time,
                    'end_time': end_time
                })
            
            # 计算统计数据
            stats = {
                'total_count': df['alert_count'].sum(),
                'high_count': df['high_count'].sum(),
                'medium_count': df['medium_count'].sum(),
                'low_count': df['low_count'].sum(),
                'daily_avg': df['alert_count'].mean(),
                'trend': self._calculate_trend(df['alert_count'])
            }
            
            return {
                'stats': stats,
                'daily_data': df.to_dict('records')
            }
            
        except Exception as e:
            self.logger.error(f"收集预警数据时出错: {str(e)}")
            raise
            
    def collect_hot_topics(self, start_time: datetime, end_time: datetime, limit: int = 20) -> List[Dict[str, Any]]:
        """
        收集热点话题数据
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回的话题数量限制
            
        Returns:
            热点话题列表
        """
        try:
            query = text("""
                SELECT 
                    t.topic_name,
                    AVG(t.heat_score) as avg_heat,
                    MAX(t.heat_score) as max_heat,
                    COUNT(*) as mention_count,
                    MAX(t.created_at) as last_mentioned
                FROM topic_analysis t
                WHERE t.created_at BETWEEN :start_time AND :end_time
                GROUP BY t.topic_name
                ORDER BY avg_heat DESC
                LIMIT :limit
            """)
            
            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn, params={
                    'start_time': start_time,
                    'end_time': end_time,
                    'limit': limit
                })
            
            return df.to_dict('records')
            
        except Exception as e:
            self.logger.error(f"收集热点话题数据时出错: {str(e)}")
            raise
            
    def collect_typical_comments(self, start_time: datetime, end_time: datetime, limit: int = 10) -> List[Dict[str, Any]]:
        """
        收集典型评论数据
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回的评论数量限制
            
        Returns:
            典型评论列表
        """
        try:
            query = text("""
                SELECT 
                    c.content,
                    c.sentiment,
                    c.heat_score,
                    c.interaction_count,
                    c.created_at
                FROM comments c
                WHERE c.created_at BETWEEN :start_time AND :end_time
                ORDER BY c.heat_score DESC, c.interaction_count DESC
                LIMIT :limit
            """)
            
            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn, params={
                    'start_time': start_time,
                    'end_time': end_time,
                    'limit': limit
                })
            
            return df.to_dict('records')
            
        except Exception as e:
            self.logger.error(f"收集典型评论数据时出错: {str(e)}")
            raise
            
    def _calculate_trend(self, series: pd.Series) -> str:
        """
        计算数据趋势
        
        Args:
            series: 时间序列数据
            
        Returns:
            趋势描述
        """
        if len(series) < 2:
            return "数据不足"
            
        # 计算变化率
        change_rate = (series.iloc[-1] - series.iloc[0]) / series.iloc[0] * 100
        
        if change_rate > 5:
            return "显著上升"
        elif change_rate > 0:
            return "轻微上升"
        elif change_rate > -5:
            return "轻微下降"
        else:
            return "显著下降" 
 
 