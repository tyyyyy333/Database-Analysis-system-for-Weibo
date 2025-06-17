import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from collections import defaultdict
from ..sentiment.sentiment_analyzer import SentimentAnalyzer

class HeatAnalyzer:
    """热度分析器，用于分析明星微博热度数据"""
    
    def __init__(self, db_url: str):
        """初始化热度分析器
        
        Args:
            db_url: 数据库连接URL
        """
        self.logger = logging.getLogger(__name__)
        self.engine = create_engine(db_url)

        
    def _ensure_heat_table(self) -> bool:
        """确保热度表存在"""
        try:
            with self.engine.connect() as conn:
                # 检查表是否存在
                result = conn.execute(
                    text("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='heat_data';
                    """)
                ).scalar()
                
                if not result:
                    # 创建热度表
                    conn.execute(text("""
                        CREATE TABLE heat_data (
                            date DATE,
                            celebrity_id VARCHAR(50),
                            post_count INTEGER DEFAULT 0,
                            comment_count INTEGER DEFAULT 0,
                            like_count INTEGER DEFAULT 0,
                            repost_count INTEGER DEFAULT 0,
                            total_heat FLOAT DEFAULT 0.0,
                            heat_change FLOAT DEFAULT 0.0,
                            PRIMARY KEY (date, celebrity_id),
                            FOREIGN KEY (celebrity_id) REFERENCES celebrity(weibo_id)
                        )
                    """))
                    conn.commit()
                    self.logger.info("热度表创建成功")
                return True
                
        except Exception as e:
            self.logger.error(f"热度表检查/创建失败: {str(e)}")
            return False
            
    def _calculate_daily_heat(self, celebrity_id: str, date: datetime) -> Dict[str, Any]:
        """计算指定日期的热度数据，使用指数平滑模型
        
        Args:
            celebrity_id: 明星ID
            date: 日期
            
        Returns:
            Dict: 热度数据
        """
        try:
            with self.engine.connect() as conn:
                # 获取时间窗口内的数据（3天）
                window_start = date - timedelta(days=3)
                
                # 获取时间窗口内的微博数据
                post_stats = conn.execute(
                    text("""
                        SELECT 
                            DATE(created_at) as date,
                            COUNT(*) as post_count,
                            SUM(like_count) as like_count,
                            SUM(repost_count) as repost_count
                        FROM post
                        WHERE celebrity_id = :celebrity_id
                        AND created_at >= :window_start
                        AND created_at <= :date
                        GROUP BY DATE(created_at)
                        ORDER BY date
                    """),
                    {
                        'celebrity_id': celebrity_id,
                        'window_start': window_start,
                        'date': date
                    }
                ).fetchall()
                
                # 获取时间窗口内的评论数据
                comment_stats = conn.execute(
                    text("""
                        SELECT 
                            DATE(c.created_at) as date,
                            COUNT(*) as comment_count
                        FROM comment c
                        JOIN post p ON c.post_id = p.post_id
                        WHERE p.celebrity_id = :celebrity_id
                        AND c.created_at >= :window_start
                        AND c.created_at <= :date
                        GROUP BY DATE(c.created_at)
                        ORDER BY date
                    """),
                    {
                        'celebrity_id': celebrity_id,
                        'window_start': window_start,
                        'date': date
                    }
                ).fetchall()
                
                # 将数据转换为DataFrame以便处理
                post_df = pd.DataFrame(post_stats)
                comment_df = pd.DataFrame(comment_stats)
                
                # 合并数据
                if not post_df.empty and not comment_df.empty:
                    df = pd.merge(post_df, comment_df, on='date', how='outer')
                else:
                    df = pd.DataFrame(columns=['date', 'post_count', 'like_count', 'repost_count', 'comment_count'])
                
                # 填充缺失值
                df = df.fillna(0)
                
                # 计算每日基础热度
                # 权重设置：
                # 微博数: 1.0
                # 评论数: 2.0
                # 点赞数: 0.5
                # 转发数: 1.5
                df['daily_heat'] = (
                    df['post_count'] * 1.0 +
                    df['comment_count'] * 2.0 +
                    df['like_count'] * 0.5 +
                    df['repost_count'] * 1.5
                )
                
                # 使用指数平滑计算热度
                # alpha = 0.4 表示新数据权重为0.4，历史数据权重为0.6
                # 由于时间窗口较短，增加新数据权重以更快反映变化
                alpha = 0.4
                df['smoothed_heat'] = df['daily_heat'].ewm(alpha=alpha, adjust=False).mean()
                
                # 获取最终热度值（最新一天）
                total_heat = df['smoothed_heat'].iloc[-1] if not df.empty else 0.0
                
                # 获取前一天的热度值
                prev_heat = conn.execute(
                    text("""
                        SELECT total_heat
                        FROM heat_data
                        WHERE celebrity_id = :celebrity_id
                        AND date = :prev_date
                    """),
                    {
                        'celebrity_id': celebrity_id,
                        'prev_date': (date - timedelta(days=1)).date()
                    }
                ).scalar() or 0.0
                
                # 计算热度变化
                heat_change = total_heat - prev_heat
                
                # 获取当天的原始数据（用于记录）
                today_stats = df.iloc[-1] if not df.empty else pd.Series({
                    'post_count': 0,
                    'comment_count': 0,
                    'like_count': 0,
                    'repost_count': 0
                })
                
                return {
                    'date': date.date(),
                    'celebrity_id': celebrity_id,
                    'post_count': int(today_stats['post_count']),
                    'comment_count': int(today_stats['comment_count']),
                    'like_count': int(today_stats['like_count']),
                    'repost_count': int(today_stats['repost_count']),
                    'total_heat': float(total_heat),
                    'heat_change': float(heat_change)
                }
                
        except Exception as e:
            self.logger.error(f"计算热度数据失败: {str(e)}")
            return None
            
    def update_heat_data(self, celebrity_id: str, days: int = 7) -> bool:
        """更新热度数据
        
        Args:
            celebrity_id: 明星ID
            days: 更新最近几天的数据
            
        Returns:
            bool: 是否更新成功
        """
        try:
            if not self._ensure_heat_table():
                return False
                
            # 获取需要更新的日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            with self.engine.connect() as conn:
                for date in pd.date_range(start_date, end_date):
                    # 计算当天的热度数据
                    heat_data = self._calculate_daily_heat(celebrity_id, date)
                    if heat_data:
                        # 更新或插入热度数据
                        conn.execute(
                            text("""
                                INSERT INTO heat_data (
                                    date, celebrity_id, post_count, comment_count,
                                    like_count, repost_count, total_heat, heat_change
                                ) VALUES (
                                    :date, :celebrity_id, :post_count, :comment_count,
                                    :like_count, :repost_count, :total_heat, :heat_change
                                )
                                ON CONFLICT (date, celebrity_id) DO UPDATE SET
                                    post_count = EXCLUDED.post_count,
                                    comment_count = EXCLUDED.comment_count,
                                    like_count = EXCLUDED.like_count,
                                    repost_count = EXCLUDED.repost_count,
                                    total_heat = EXCLUDED.total_heat,
                                    heat_change = EXCLUDED.heat_change,
                                    updated_at = CURRENT_TIMESTAMP
                            """),
                            heat_data
                        )
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"更新热度数据失败: {str(e)}")
            return False
            
    def get_heat_data(self, celebrity_id: str, days: int = 7) -> Dict[str, Any]:
        """获取热度数据
        
        Args:
            celebrity_id: 明星ID
            days: 获取最近几天的数据
            
        Returns:
            Dict: 热度数据
        """
        try:
            with self.engine.connect() as conn:
                # 获取热度数据
                heat_data = conn.execute(
                    text("""
                        SELECT *
                        FROM heat_data
                        WHERE celebrity_id = :celebrity_id
                        AND date >= :start_date
                        ORDER BY date DESC
                    """),
                    {
                        'celebrity_id': celebrity_id,
                        'start_date': (datetime.now() - timedelta(days=days)).date()
                    }
                ).fetchall()
                
                # 转换为字典列表
                data = [dict(row) for row in heat_data]
                
                return {
                    "status": "success",
                    "data": {
                        "heat_data": data
                    }
                }
                
        except Exception as e:
            self.logger.error(f"获取热度数据失败: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
 
 