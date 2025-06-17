import torch
import torch.nn as nn
from transformers import BertTokenizer, BertModel
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from ...models.model_manager import ModelManager
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from ...database.models import Comment, Post

class SentimentAnalyzer:
    """情感分析器"""
    
    def __init__(self, db_url: str):
        """初始化情感分析器
        
        Args:
            db_url: 数据库连接URL
        """
        self.logger = logging.getLogger(__name__)
        self.db_url = db_url
        # 使用模型管理器加载模型
        try:
            model_manager = ModelManager()
            self.tokenizer, self.model = model_manager.get_bert_model()
            self.device = self.model.device
            self.logger.info(f"BERT模型加载成功，使用设备: {self.device}")
        except Exception as e:
            self.logger.error(f"BERT模型加载失败: {str(e)}")
            # raise
        
        # 情感类别
        self.sentiment_labels = ['负面', '中性', '正面']
        
        # 黑粉分析相关
        self.black_fan_threshold = 0.7  # 黑粉判定阈值
        self.time_window = timedelta(days=7)  # 分析时间窗口
        self.min_comments = 3  # 最小评论数
        
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """分析文本情感
        
        Args:
            text: 输入文本
            
        Returns:
            情感分析结果
        """
        try:
            # 准备输入
            inputs = self.tokenizer(
                text,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors='pt'
            ).to(self.device)
            
            # 预测
            with torch.no_grad():
                outputs = self.model(**inputs)
                probabilities = torch.softmax(outputs, dim=1)
                sentiment_scores = probabilities[0].cpu().numpy()
                
            # 获取情感类别和置信度
            sentiment_idx = np.argmax(sentiment_scores)
            sentiment = self.sentiment_labels[sentiment_idx]
            confidence = float(sentiment_scores[sentiment_idx])
            
            # 计算情感强度（-1到1之间）
            sentiment_strength = (sentiment_scores[2] - sentiment_scores[0]) / (sentiment_scores[2] + sentiment_scores[0] + 1e-6)
            
            return {
                'sentiment': sentiment,
                'confidence': confidence,
                'strength': float(sentiment_strength),
                'scores': {
                    label: float(score)
                    for label, score in zip(self.sentiment_labels, sentiment_scores)
                }
            }
            
        except Exception as e:
            self.logger.error(f"情感分析失败: {str(e)}")
            return {
                'sentiment': '未知',
                'confidence': 0.0,
                'strength': 0.0,
                'scores': {label: 0.0 for label in self.sentiment_labels}
            }
            
    def analyze_black_fan(self, celebrity_id: str) -> Dict[str, Any]:
        """分析黑粉
        
        Args:
            celebrity_id: 明星ID
            
        Returns:
            黑粉分析结果
        """
        try:
            # 从数据库获取评论数据
            engine = create_engine(self.db_url)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # 获取该明星的所有评论
            comments = session.query(Comment).join(Post).filter(
                Post.celebrity_id == celebrity_id,
                Comment.is_deleted == 0
            ).order_by(Comment.created_at).all()
            
            if not comments:
                return {
                    'is_black_fan': False,
                    'reason': '没有评论数据',
                    'score': 0.0
                }
                
            # 转换评论数据格式
            user_comments = []
            for comment in comments:
                user_comments.append({
                    'content': comment.content,
                    'created_at': comment.created_at
                })
            
            if len(user_comments) < self.min_comments:
                return {
                    'is_black_fan': False,
                    'reason': f'评论数量不足{self.min_comments}条',
                    'score': 0.0
                }
                
            # 按时间排序
            user_comments.sort(key=lambda x: x['created_at'])
            
            # 分析时间窗口内的评论
            recent_comments = [
                comment for comment in user_comments
                if datetime.now() - comment['created_at'] <= self.time_window
            ]
            
            if not recent_comments:
                return {
                    'is_black_fan': False,
                    'reason': f'最近{self.time_window}天内无评论',
                    'score': 0.0
                }
                
            # 分析每条评论的情感
            sentiment_results = []
            for comment in recent_comments:
                result = self.analyze_sentiment(comment['content'])
                sentiment_results.append({
                    'sentiment': result['sentiment'],
                    'strength': result['strength'],
                    'created_at': comment['created_at']
                })
                
            # 计算黑粉评分
            negative_ratio = sum(1 for r in sentiment_results if r['sentiment'] == '负面') / len(sentiment_results)
            avg_strength = sum(r['strength'] for r in sentiment_results) / len(sentiment_results)
            time_span = (sentiment_results[-1]['created_at'] - sentiment_results[0]['created_at']).total_seconds()
            comment_frequency = len(sentiment_results) / (time_span / 3600)  # 每小时评论数
            
            # 首先计算负面评论的加权分数
            negative_score = negative_ratio * (
                0.4 + 
                0.3 * (1 - (avg_strength + 1) / 2) +  # 情感强度对负面评论的影响
                0.3 * min(comment_frequency / 10, 1)  # 评论频率对负面评论的影响
            )

            # 最终黑粉分数
            black_fan_score = negative_score
            
            is_black_fan = black_fan_score >= self.black_fan_threshold
            
            result = {
                'is_black_fan': is_black_fan,
                'score': float(black_fan_score),
                'metrics': {
                    'negative_ratio': float(negative_ratio),
                    'avg_strength': float(avg_strength),
                    'comment_frequency': float(comment_frequency)
                },
                'reason': '黑粉特征明显' if is_black_fan else '未达到黑粉判定标准'
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"黑粉分析失败: {str(e)}")
            return {
                'is_black_fan': False,
                'reason': f'分析过程出错: {str(e)}',
                'score': 0.0
            }
        finally:
            session.close()
            
class PostSentimentAnalyzer:
    """微博情感分析器，用于分析微博及其评论的情感倾向"""
    
    def __init__(self, db_url: str):
        """初始化微博情感分析器
        
        Args:
            db_url: 数据库连接URL
        """
        self.logger = logging.getLogger(__name__)
        self.engine = create_engine(db_url)
        self.comment_analyzer = SentimentAnalyzer(db_url)  # 评论情感分析器
        
    def analyze_post_sentiment(self, post_id: str) -> Dict[str, Any]:
        """分析单条微博的情感倾向
        
        Args:
            post_id: 微博ID
            
        Returns:
            Dict: 分析结果
        """
        try:
            # 1. 获取微博内容和情感分数
            with self.engine.connect() as conn:
                post = conn.execute(
                    text("""
                        SELECT p.*, 
                               CASE 
                                   WHEN p.sentiment_score != 0 THEN true 
                                   ELSE false 
                               END as has_sentiment_score
                        FROM post p 
                        WHERE p.post_id = :post_id
                    """),
                    {'post_id': post_id}
                ).fetchone()
                
                if not post:
                    return {
                        "status": "error",
                        "message": "微博不存在"
                    }
                
                # 如果已经计算过情感分数（不为0），直接返回结果
                if post['has_sentiment_score']:
                    return {
                        "status": "success",
                        "data": {
                            "post_id": post_id,
                            "sentiment_score": post['sentiment_score'],
                            "is_cached": True
                        }
                    }
                    
                # 2. 获取微博的所有评论
                comments = conn.execute(
                    text("""
                        SELECT c.*, s.sentiment_score
                        FROM comment c
                        LEFT JOIN sentiment_for_comment s ON c.comment_id = s.comment_id
                        WHERE c.post_id = :post_id
                    """),
                    {'post_id': post_id}
                ).fetchall()
                
            # 3. 分析微博内容的情感
            post_sentiment = self.comment_analyzer.analyze_sentiment(post['content'])
            
            # 4. 计算评论的情感分数
            comment_scores = [c['sentiment_score'] for c in comments if c['sentiment_score'] is not None]
            
            # 5. 计算综合情感分数
            # 微博内容权重0.4，评论情感权重0.6
            post_weight = 0.4
            comment_weight = 0.6
            
            if comment_scores:
                comment_avg = sum(comment_scores) / len(comment_scores)
                final_score = (
                    post_sentiment['scores']['正面'] * post_weight +
                    comment_avg * comment_weight
                )
            else:
                final_score = post_sentiment['scores']['正面']
                
            # 6. 更新微博的情感分数
            with self.engine.connect() as conn:
                conn.execute(
                    text("""
                        UPDATE post 
                        SET sentiment_score = :sentiment_score
                        WHERE post_id = :post_id
                    """),
                    {
                        'post_id': post_id,
                        'sentiment_score': final_score
                    }
                )
                conn.commit()
                
            return {
                        "status": "success",
                        "data": {
                            "post_id": post_id,
                            "sentiment_score": final_score,
                            "is_cached": False
                        }
                    }
            
        except Exception as e:
            self.logger.error(f"微博情感分析失败: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
            
    def analyze_posts_batch(self, post_ids: List[str]) -> Dict[str, Any]:
        """批量分析微博情感
        
        Args:
            post_ids: 微博ID列表
            
        Returns:
            Dict: 分析结果
        """
        results = []
        for post_id in post_ids:
            result = self.analyze_post_sentiment(post_id)
            if result["status"] == "success":
                results.append(result["data"])
                
        return {
            "status": "success",
            "data": {
                "total": len(post_ids),
                "success": len(results),
                "failed": len(post_ids) - len(results),
                "results": results
            }
        }
        
    def analyze_celebrity_posts(self, celebrity_id: str, days: int = 7) -> Dict[str, Any]:
        """分析明星最近发布的微博情感
        
        Args:
            celebrity_id: 明星ID
            days: 分析最近几天的微博
            
        Returns:
            Dict: 分析结果
        """
        try:
            # 1. 获取明星最近发布的微博
            with self.engine.connect() as conn:
                posts = conn.execute(
                    text("""
                        SELECT post_id 
                        FROM post 
                        WHERE celebrity_id = :celebrity_id 
                        AND created_at >= :start_date
                        ORDER BY created_at DESC
                    """),
                    {
                        'celebrity_id': celebrity_id,
                        'start_date': datetime.now() - timedelta(days=days)
                    }
                ).fetchall()
                
            # 2. 批量分析微博情感
            return self.analyze_posts_batch([p['post_id'] for p in posts])
            
        except Exception as e:
            self.logger.error(f"明星微博情感分析失败: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

if __name__ == "__main__":
    pass
 