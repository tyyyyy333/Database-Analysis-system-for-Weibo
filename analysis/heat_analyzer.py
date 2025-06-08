import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from collections import defaultdict
from sentiment.sentiment_analyzer import SentimentAnalyzer
from .heat_visualizer import HeatVisualizer

class HeatAnalyzer:
    """热度分析器类"""
    
    def __init__(self, db_url: str):
        """初始化热度分析器
        
        Args:
            db_url: 数据库连接URL
        """
        self.logger = logging.getLogger(__name__)
        self.engine = create_engine(db_url)
        self.sentiment_analyzer = SentimentAnalyzer()
        self.visualizer = HeatVisualizer(db_url)
        
        # 热度计算权重配置
        self.weights = {
            'likes': 0.3,        # 点赞权重
            'reposts': 0.3,      # 转发权重
            'comments': 0.2,     # 评论权重
            'views': 0.1,        # 浏览权重
            'time_decay': 0.1    # 时间衰减权重
        }
        
        # 热度预警阈值
        self.alert_thresholds = {
            'high': 0.8,    # 高热预警阈值
            'medium': 0.5,  # 中热预警阈值
            'low': 0.3      # 低热预警阈值
        }
        
        # 舆论水平阈值
        self.sentiment_thresholds = {
            'positive': 0.6,    # 正面舆论阈值
            'neutral': 0.4,     # 中性舆论阈值
            'negative': 0.2     # 负面舆论阈值
        }
        
    def calculate_post_heat(self, post_data: Dict[str, Any]) -> float:
        """计算单条微博的热度值
        
        Args:
            post_data: 微博数据，包含互动数据
            
        Returns:
            float: 热度值（0-1之间）
        """
        try:
            # 获取互动数据
            likes = post_data.get('likes', 0)
            reposts = post_data.get('reposts', 0)
            comments = post_data.get('comments', 0)
            views = post_data.get('views', 0)
            
            # 计算时间衰减因子
            created_at = post_data.get('created_at')
            if created_at:
                time_decay = self._calculate_time_decay(created_at)
            else:
                time_decay = 1.0
                
            # 计算热度值
            heat = (
                self.weights['likes'] * self._normalize_value(likes) +
                self.weights['reposts'] * self._normalize_value(reposts) +
                self.weights['comments'] * self._normalize_value(comments) +
                self.weights['views'] * self._normalize_value(views)
            ) * (1 - self.weights['time_decay'] * (1 - time_decay))
            
            return min(max(heat, 0), 1)  # 确保热度值在0-1之间
            
        except Exception as e:
            self.logger.error(f"计算微博热度失败: {str(e)}")
            return 0.0
            
    def calculate_celebrity_heat(self, celebrity_id: int, 
                               days: int = 7) -> Dict[str, Any]:
        """计算明星的整体热度
        
        Args:
            celebrity_id: 明星ID
            days: 分析天数
            
        Returns:
            Dict: 包含热度分析结果的字典
        """
        try:
            # 获取明星微博数据
            query = """
                SELECT p.*, c.name as celebrity_name
                FROM posts p
                JOIN celebrities c ON p.celebrity_id = c.id
                WHERE p.celebrity_id = :celebrity_id
                AND p.created_at >= :start_date
                ORDER BY p.created_at DESC
            """
            
            start_date = datetime.now() - timedelta(days=days)
            
            with self.engine.connect() as conn:
                posts = conn.execute(
                    text(query),
                    {
                        'celebrity_id': celebrity_id,
                        'start_date': start_date
                    }
                ).fetchall()
                
            if not posts:
                return {
                    "total_heat": 0,
                    "average_heat": 0,
                    "heat_trend": [],
                    "top_posts": [],
                    "heat_distribution": {
                        "high": 0,
                        "medium": 0,
                        "low": 0
                    }
                }
                
            # 计算每条微博的热度
            post_heats = []
            for post in posts:
                heat = self.calculate_post_heat(dict(post))
                post_heats.append({
                    'id': post.id,
                    'content': post.content,
                    'heat': heat,
                    'created_at': post.created_at
                })
                
            # 计算总体热度
            total_heat = sum(p['heat'] for p in post_heats)
            average_heat = total_heat / len(post_heats) if post_heats else 0
            
            # 计算热度分布
            heat_distribution = {
                'high': len([p for p in post_heats if p['heat'] >= self.alert_thresholds['high']]),
                'medium': len([p for p in post_heats if self.alert_thresholds['medium'] <= p['heat'] < self.alert_thresholds['high']]),
                'low': len([p for p in post_heats if p['heat'] < self.alert_thresholds['medium']])
            }
            
            # 生成热度趋势
            heat_trend = []
            for i in range(days):
                date = start_date + timedelta(days=i)
                day_posts = [p for p in post_heats if p['created_at'].date() == date.date()]
                day_heat = sum(p['heat'] for p in day_posts) / len(day_posts) if day_posts else 0
                heat_trend.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'heat': day_heat
                })
                
            # 获取热度最高的微博
            top_posts = sorted(post_heats, key=lambda x: x['heat'], reverse=True)[:5]
            
            # 生成分析结果
            results = {
                'total_heat': total_heat,
                'average_heat': average_heat,
                'heat_distribution': heat_distribution,
                'heat_trend': heat_trend,
                'top_posts': top_posts
            }
            
            # 生成可视化
            self.visualizer.generate_heat_trend(heat_trend)
            self.visualizer.generate_heat_distribution(heat_distribution)
            
            # 保存分析结果
            self.visualizer.save_analysis_results(results, celebrity_id=celebrity_id)
            
            # 导出分析报告
            self.visualizer.export_analysis_report(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"计算明星热度失败: {str(e)}")
            return {
                "total_heat": 0,
                "average_heat": 0,
                "heat_trend": [],
                "top_posts": [],
                "heat_distribution": {
                    "high": 0,
                    "medium": 0,
                    "low": 0
                }
            }
            
    def analyze_topic_heat(self, topic: str, days: int = 7) -> Dict[str, Any]:
        """分析话题热度
        
        Args:
            topic: 话题关键词
            days: 分析天数
            
        Returns:
            Dict: 包含话题热度分析结果的字典
        """
        try:
            # 获取话题相关微博
            query = """
                SELECT p.*, c.name as celebrity_name
                FROM posts p
                JOIN celebrities c ON p.celebrity_id = c.id
                WHERE p.content LIKE :topic
                AND p.created_at >= :start_date
                ORDER BY p.created_at DESC
            """
            
            start_date = datetime.now() - timedelta(days=days)
            
            with self.engine.connect() as conn:
                posts = conn.execute(
                    text(query),
                    {
                        'topic': f'%{topic}%',
                        'start_date': start_date
                    }
                ).fetchall()
                
            if not posts:
                return {
                    "topic": topic,
                    "total_heat": 0,
                    "average_heat": 0,
                    "heat_trend": [],
                    "related_celebrities": [],
                    "top_posts": []
                }
                
            # 计算每条微博的热度
            post_heats = []
            for post in posts:
                heat = self.calculate_post_heat(dict(post))
                post_heats.append({
                    'id': post.id,
                    'content': post.content,
                    'heat': heat,
                    'created_at': post.created_at,
                    'celebrity_name': post.celebrity_name
                })
                
            # 计算总体热度
            total_heat = sum(p['heat'] for p in post_heats)
            average_heat = total_heat / len(post_heats) if post_heats else 0
            
            # 计算热度分布
            heat_distribution = {
                'high': len([p for p in post_heats if p['heat'] >= self.alert_thresholds['high']]),
                'medium': len([p for p in post_heats if self.alert_thresholds['medium'] <= p['heat'] < self.alert_thresholds['high']]),
                'low': len([p for p in post_heats if p['heat'] < self.alert_thresholds['medium']])
            }
            
            # 生成热度趋势
            heat_trend = []
            for i in range(days):
                date = start_date + timedelta(days=i)
                day_posts = [p for p in post_heats if p['created_at'].date() == date.date()]
                day_heat = sum(p['heat'] for p in day_posts) / len(day_posts) if day_posts else 0
                heat_trend.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'heat': day_heat
                })
                
            # 获取热度最高的微博
            top_posts = sorted(post_heats, key=lambda x: x['heat'], reverse=True)[:5]
            
            # 生成分析结果
            results = {
                'topic': topic,
                'total_heat': total_heat,
                'average_heat': average_heat,
                'heat_distribution': heat_distribution,
                'heat_trend': heat_trend,
                'top_posts': top_posts
            }
            
            # 生成可视化
            self.visualizer.generate_heat_trend(heat_trend)
            self.visualizer.generate_heat_distribution(heat_distribution)
            
            # 保存分析结果
            self.visualizer.save_analysis_results(results, topic=topic)
            
            # 导出分析报告
            self.visualizer.export_analysis_report(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"分析话题热度失败: {str(e)}")
            return {
                "topic": topic,
                "total_heat": 0,
                "average_heat": 0,
                "heat_trend": [],
                "related_celebrities": [],
                "top_posts": []
            }
            
    def _calculate_time_decay(self, created_at: datetime) -> float:
        """计算时间衰减因子
        
        Args:
            created_at: 创建时间
            
        Returns:
            float: 时间衰减因子（0-1之间）
        """
        now = datetime.now()
        hours_diff = (now - created_at).total_seconds() / 3600
        
        # 使用指数衰减函数
        decay = np.exp(-hours_diff / 24)  # 24小时衰减到约0.37
        return min(max(decay, 0), 1)
        
    def _normalize_value(self, value: int) -> float:
        """归一化数值
        
        Args:
            value: 原始数值
            
        Returns:
            float: 归一化后的值（0-1之间）
        """
        # 使用对数归一化
        if value <= 0:
            return 0
        return min(np.log1p(value) / 10, 1)  # 使用log1p避免log(0)，除以10作为缩放因子
        
    def check_heat_alert(self, heat_value: float) -> str:
        """检查热度预警
        
        Args:
            heat_value: 热度值
            
        Returns:
            str: 预警级别
        """
        if heat_value >= self.alert_thresholds['high']:
            return 'high'
        elif heat_value >= self.alert_thresholds['medium']:
            return 'medium'
        elif heat_value >= self.alert_thresholds['low']:
            return 'low'
        else:
            return 'normal'

    def analyze_public_opinion(self, post_id: Optional[int] = None, celebrity_id: Optional[int] = None, 
                             time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """分析舆论水平
        
        Args:
            post_id: 微博ID，可选
            celebrity_id: 明星ID，可选
            time_range: 时间范围，可选
            
        Returns:
            Dict: 包含舆论分析结果的字典
        """
        try:
            # 构建查询条件
            conditions = []
            params = {}
            
            if post_id:
                conditions.append("p.id = :post_id")
                params["post_id"] = post_id
            elif celebrity_id:
                conditions.append("p.celebrity_id = :celebrity_id")
                params["celebrity_id"] = celebrity_id
                
            if time_range:
                start_time, end_time = time_range
                conditions.append("p.created_at BETWEEN :start_time AND :end_time")
                params.update({
                    "start_time": start_time,
                    "end_time": end_time
                })
                
            # 查询评论数据
            query = f"""
                SELECT 
                    p.id as post_id,
                    p.content as post_content,
                    c.id as comment_id,
                    c.content as comment_content,
                    c.created_at,
                    u.id as user_id,
                    u.nickname as user_nickname
                FROM posts p
                LEFT JOIN comments c ON p.id = c.post_id
                LEFT JOIN users u ON c.user_id = u.id
                WHERE {' AND '.join(conditions)}
                ORDER BY c.created_at DESC
            """
            
            with self.engine.connect() as conn:
                comments_df = pd.read_sql(text(query), conn, params=params)
                
            if comments_df.empty:
                return {
                    "sentiment_distribution": {
                        "positive": 0,
                        "neutral": 0,
                        "negative": 0
                    },
                    "average_sentiment": 0.0,
                    "sentiment_trend": [],
                    "top_positive_comments": [],
                    "top_negative_comments": [],
                    "black_fan_ratio": 0.0
                }
                
            # 分析每条评论的情感
            sentiment_results = []
            for _, row in comments_df.iterrows():
                if pd.isna(row['comment_content']):
                    continue
                    
                result = self.sentiment_analyzer.analyze_sentiment(row['comment_content'])
                sentiment_results.append({
                    'post_id': row['post_id'],
                    'comment_id': row['comment_id'],
                    'content': row['comment_content'],
                    'user_id': row['user_id'],
                    'user_nickname': row['user_nickname'],
                    'created_at': row['created_at'],
                    'sentiment': result['sentiment'],
                    'strength': result['strength'],
                    'confidence': result['confidence']
                })
                
            # 计算情感分布
            sentiment_counts = defaultdict(int)
            for result in sentiment_results:
                sentiment_counts[result['sentiment']] += 1
                
            total_comments = len(sentiment_results)
            sentiment_distribution = {
                "positive": sentiment_counts['正面'] / total_comments if total_comments > 0 else 0,
                "neutral": sentiment_counts['中性'] / total_comments if total_comments > 0 else 0,
                "negative": sentiment_counts['负面'] / total_comments if total_comments > 0 else 0
            }
            
            # 计算平均情感强度
            average_sentiment = sum(r['strength'] for r in sentiment_results) / total_comments if total_comments > 0 else 0
            
            # 计算情感趋势
            sentiment_df = pd.DataFrame(sentiment_results)
            sentiment_df['date'] = pd.to_datetime(sentiment_df['created_at']).dt.date
            sentiment_trend = sentiment_df.groupby('date')['strength'].mean().reset_index()
            sentiment_trend = sentiment_trend.to_dict('records')
            
            # 获取最正面和最负面的评论
            top_positive = sorted(sentiment_results, key=lambda x: x['strength'], reverse=True)[:5]
            top_negative = sorted(sentiment_results, key=lambda x: x['strength'])[:5]
            
            # 分析黑粉比例
            user_comments = defaultdict(list)
            for result in sentiment_results:
                user_comments[result['user_id']].append({
                    'content': result['content'],
                    'created_at': result['created_at']
                })
                
            black_fan_count = 0
            for user_id, comments in user_comments.items():
                if len(comments) >= 3:  # 只分析评论数大于等于3的用户
                    result = self.sentiment_analyzer.analyze_black_fan(comments)
                    if result['is_black_fan']:
                        black_fan_count += 1
                        
            black_fan_ratio = black_fan_count / len(user_comments) if user_comments else 0
            
            return {
                "sentiment_distribution": sentiment_distribution,
                "average_sentiment": float(average_sentiment),
                "sentiment_trend": sentiment_trend,
                "top_positive_comments": [
                    {
                        "content": c['content'],
                        "user": c['user_nickname'],
                        "sentiment": c['sentiment'],
                        "strength": c['strength'],
                        "created_at": c['created_at'].isoformat()
                    }
                    for c in top_positive
                ],
                "top_negative_comments": [
                    {
                        "content": c['content'],
                        "user": c['user_nickname'],
                        "sentiment": c['sentiment'],
                        "strength": c['strength'],
                        "created_at": c['created_at'].isoformat()
                    }
                    for c in top_negative
                ],
                "black_fan_ratio": float(black_fan_ratio)
            }
            
        except Exception as e:
            self.logger.error(f"分析舆论水平失败: {str(e)}")
            return {
                "sentiment_distribution": {
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0
                },
                "average_sentiment": 0.0,
                "sentiment_trend": [],
                "top_positive_comments": [],
                "top_negative_comments": [],
                "black_fan_ratio": 0.0
            }

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 测试配置
    db_url = "mysql+pymysql://root:123456@localhost:3306/celebrity_analysis"
    
    # 创建热度分析器实例
    analyzer = HeatAnalyzer(db_url)
    
    # 测试单条微博热度计算
    test_post = {
        'likes': 1000,
        'reposts': 500,
        'comments': 200,
        'views': 10000,
        'created_at': datetime.now() - timedelta(hours=2)
    }
    heat = analyzer.calculate_post_heat(test_post)
    print(f"测试微博热度值: {heat:.4f}")
    
    # 测试明星热度分析
    celebrity_heat = analyzer.calculate_celebrity_heat(
        celebrity_id=1,
        days=7
    )
    print("\n明星热度分析结果:")
    print(f"总热度: {celebrity_heat['total_heat']:.4f}")
    print(f"平均热度: {celebrity_heat['average_heat']:.4f}")
    print(f"热度分布: {celebrity_heat['heat_distribution']}")
    
    # 测试话题热度分析
    topic_heat = analyzer.analyze_topic_heat(
        topic="新剧",
        days=7
    )
    print("\n话题热度分析结果:")
    print(f"话题: {topic_heat['topic']}")
    print(f"总热度: {topic_heat['total_heat']:.4f}")
    print(f"平均热度: {topic_heat['average_heat']:.4f}")
    print(f"相关明星数量: {len(topic_heat['related_celebrities'])}")
    
    # 测试舆论水平分析
    public_opinion = analyzer.analyze_public_opinion(
        celebrity_id=1,
        time_range=(datetime.now() - timedelta(days=7), datetime.now())
    )
    print("\n舆论水平分析结果:")
    print(f"情感分布: {public_opinion['sentiment_distribution']}")
    print(f"平均情感强度: {public_opinion['average_sentiment']:.4f}")
    print(f"黑粉比例: {public_opinion['black_fan_ratio']:.4f}")
    print("\n最正面评论:")
    for comment in public_opinion['top_positive_comments']:
        print(f"- {comment['user']}: {comment['content']} (情感强度: {comment['strength']:.2f})")
    print("\n最负面评论:")
    for comment in public_opinion['top_negative_comments']:
        print(f"- {comment['user']}: {comment['content']} (情感强度: {comment['strength']:.2f})") 