# 用户粉丝分析，主要过程如下：
# 扫描用户表，选取近七天在指定明星的微博下有评论的用户
# 检索每个该用户在该明星微博下的所有评论表数据，制作成list
# list经过 sentiment_analyzer的analyze_black_fan，返回一个dict
# dict与用户表、明星表等连接，成为黑粉表
# 所有用户遍历完成后使用black_fan_analyzer.py 对黑粉表中的用户结合用户表进行各项分析，得到分析结果

import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from collections import defaultdict
from .sentiment.sentiment_analyzer import SentimentAnalyzer
from .sentiment.black_fan_analyzer import BlackFanAnalyzer

class FanAnalyzer:
    """粉丝分析器，用于分析明星的粉丝群体特征"""
    
    def __init__(self, db_url: str):
        """初始化粉丝分析器
        
        Args:
            db_url: 数据库连接URL
        """
        self.logger = logging.getLogger(__name__)
        self.engine = create_engine(db_url)
        self.sentiment_analyzer = SentimentAnalyzer(db_url)
        
        # 检查并创建黑粉表
        self._ensure_black_fans_table()
        
    def _ensure_black_fans_table(self) -> None:
        """确保黑粉表存在，如果不存在则创建"""
        try:
            # 检查表是否存在
            check_query = """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='black_fans';
            """
            
            with self.engine.connect() as conn:
                table_exists = conn.execute(text(check_query)).scalar()
                
            if not table_exists:
                # 创建黑粉表
                create_query = """
                    CREATE TABLE black_fans (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        celebrity_id VARCHAR(50) NOT NULL,
                        black_fan_score FLOAT NOT NULL,
                        comment_count INTEGER DEFAULT 0,
                        last_active TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (celebrity_id) REFERENCES celebrity(weibo_id)
                    );
                    
                    -- 创建索引
                    CREATE INDEX idx_black_fans_celebrity ON black_fans(celebrity_id);
                    CREATE INDEX idx_black_fans_score ON black_fans(black_fan_score);
                    CREATE INDEX idx_black_fans_last_active ON black_fans(last_active);
                """
                
                with self.engine.connect() as conn:
                    conn.execute(text(create_query))
                    conn.commit()
                    
                self.logger.info("黑粉表创建成功")
            else:
                self.logger.info("黑粉表已存在")
                
        except Exception as e:
            self.logger.error(f"检查/创建黑粉表失败: {str(e)}")
            raise
            
    def analyze_fans(self, celebrity_id: int, days: int = 7) -> Dict[str, Any]:
        """分析明星的粉丝群体
        
        Args:
            celebrity_id: 明星ID
            days: 分析时间范围（天）
            
        Returns:
            Dict: 分析结果
        """
        try:
            # 1. 获取最近活跃的粉丝
            active_fans = self._get_active_fans(celebrity_id, days)
            if not active_fans:
                return {
                    "status": "error",
                    "message": "未找到活跃粉丝"
                }
                
            # 2. 分析每个粉丝的评论并更新黑粉表
            black_fan_count = 0
            for fan in active_fans:
                # 获取该粉丝的所有评论
                comments = self._get_fan_comments(fan['weibo_id'], celebrity_id)
                
                # 分析是否为黑粉
                black_fan_result = self.sentiment_analyzer.analyze_black_fan(comments)
                
                # 如果是黑粉，更新黑粉表
                if black_fan_result['is_black_fan']:
                    self._update_black_fan_table(
                        user_id=fan['weibo_id'],
                        celebrity_id=celebrity_id,
                        black_fan_score=black_fan_result['score'],
                        comment_count=len(comments),
                        last_active=fan['last_active']
                    )
                    black_fan_count += 1
                    
            # 3. 对黑粉表进行分析
            black_fan_analyzer = BlackFanAnalyzer(self.engine)
            black_fan_analysis = black_fan_analyzer.analyze_black_fans(celebrity_id)
            
            # 4. 生成分析报告
            report = {
                'total_fans': len(active_fans),
                'black_fan_count': black_fan_count,
                'black_fan_ratio': black_fan_count / len(active_fans) if active_fans else 0,
                'black_fan_analysis': black_fan_analysis
            }
            
            return {
                'status': 'success',
                'data': report
            }
            
        except Exception as e:
            self.logger.error(f"粉丝分析失败: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
            
    def _get_active_fans(self, celebrity_id: int, days: int) -> List[Dict]:
        """获取最近活跃的粉丝
        
        Args:
            celebrity_id: 明星ID
            days: 时间范围（天）
            
        Returns:
            List[Dict]: 活跃粉丝列表
        """
        query = """
            SELECT DISTINCT wu.*, MAX(c.created_at) as last_active
            FROM weibo_users wu
            JOIN comments c ON wu.weibo_id = c.user_id
            JOIN posts p ON c.post_id = p.post_id
            WHERE p.celebrity_id = :celebrity_id
            AND c.created_at >= :start_date
            GROUP BY wu.weibo_id
            ORDER BY last_active DESC
        """
        
        start_date = datetime.now() - timedelta(days=days)
        
        with self.engine.connect() as conn:
            result = conn.execute(
                text(query),
                {
                    'celebrity_id': celebrity_id,
                    'start_date': start_date
                }
            ).fetchall()
            
        return [dict(row) for row in result]
        
    def _get_fan_comments(self, user_id: int, celebrity_id: int) -> List[Dict]:
        """获取粉丝的所有评论
        
        Args:
            user_id: 用户ID
            celebrity_id: 明星ID
            
        Returns:
            List[Dict]: 评论列表
        """
        query = """
            SELECT c.*
            FROM comments c
            JOIN posts p ON c.post_id = p.post_id
            WHERE c.user_id = :user_id
            AND p.celebrity_id = :celebrity_id
            ORDER BY c.created_at DESC
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(
                text(query),
                {
                    'user_id': user_id,
                    'celebrity_id': celebrity_id
                }
            ).fetchall()
            
        return [dict(row) for row in result]
        
    def _update_black_fan_table(self, user_id: int, celebrity_id: int, 
                              black_fan_score: float, comment_count: int,
                              last_active: datetime) -> None:
        """更新黑粉表
        
        Args:
            user_id: 用户ID
            celebrity_id: 明星ID
            black_fan_score: 黑粉分数
            comment_count: 评论数量
            last_active: 最后活跃时间
        """
        query = """
            INSERT INTO black_fans (user_id, celebrity_id, black_fan_score, 
                                  comment_count, last_active, created_at)
            VALUES (:user_id, :celebrity_id, :black_fan_score, 
                    :comment_count, :last_active, :created_at)
            ON CONFLICT (user_id, celebrity_id) 
            DO UPDATE SET
                black_fan_score = :black_fan_score,
                comment_count = :comment_count,
                last_active = :last_active,
                updated_at = :created_at
        """
        
        with self.engine.connect() as conn:
            conn.execute(
                text(query),
                {
                    'user_id': user_id,
                    'celebrity_id': celebrity_id,
                    'black_fan_score': black_fan_score,
                    'comment_count': comment_count,
                    'last_active': last_active,
                    'created_at': datetime.now()
                }
            )
            conn.commit()