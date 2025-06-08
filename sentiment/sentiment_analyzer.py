import torch
import torch.nn as nn
from transformers import BertTokenizer, BertModel
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from models.model_manager import ModelManager
from analysis.sentiment_visualizer import SentimentVisualizer
import pandas as pd

class SentimentAnalyzer:
    """情感分析器"""
    
    def __init__(self, db_url: str):
        """初始化情感分析器
        
        Args:
            db_url: 数据库连接URL
        """
        self.logger = logging.getLogger(__name__)
        
        # 使用模型管理器加载模型
        try:
            model_manager = ModelManager()
            self.tokenizer, self.model = model_manager.get_bert_model()
            self.device = self.model.device
            self.logger.info(f"BERT模型加载成功，使用设备: {self.device}")
        except Exception as e:
            self.logger.error(f"BERT模型加载失败: {str(e)}")
            raise
            
        # 初始化可视化器
        self.visualizer = SentimentVisualizer(db_url)
        
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
            
    def analyze_black_fan(self, user_comments: List[Dict]) -> Dict[str, Any]:
        """分析黑粉
        
        Args:
            user_comments: 用户评论列表，每条评论包含content和created_at字段
            
        Returns:
            黑粉分析结果
        """
        try:
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
                    'reason': '最近30天内无评论',
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
            
            black_fan_score = (
                0.4 * negative_ratio +  # 负面评论比例权重
                0.3 * (1 - (avg_strength + 1) / 2) +  # 情感强度权重
                0.3 * min(comment_frequency / 10, 1)  # 评论频率权重
            )
            
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
            
            # 生成黑粉分析图表
            chart_path = self.visualizer.generate_black_fan_analysis(result)
            if chart_path:
                result['chart_path'] = chart_path
                
            return result
            
        except Exception as e:
            self.logger.error(f"黑粉分析失败: {str(e)}")
            return {
                'is_black_fan': False,
                'reason': f'分析过程出错: {str(e)}',
                'score': 0.0
            }
            
    def analyze_public_opinion(self, comments: List[Dict], 
                             celebrity_id: Optional[int] = None,
                             post_id: Optional[int] = None) -> Dict[str, Any]:
        """分析舆论水平
        
        Args:
            comments: 评论列表
            celebrity_id: 明星ID，可选
            post_id: 微博ID，可选
            
        Returns:
            舆论分析结果
        """
        try:
            # 分析每条评论的情感
            sentiment_results = []
            for comment in comments:
                result = self.analyze_sentiment(comment['content'])
                sentiment_results.append({
                    'content': comment['content'],
                    'user': comment.get('user_nickname', '未知用户'),
                    'created_at': comment['created_at'],
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
                user_comments[result['user']].append({
                    'content': result['content'],
                    'created_at': result['created_at']
                })
                
            black_fan_count = 0
            for user, comments in user_comments.items():
                if len(comments) >= self.min_comments:
                    result = self.analyze_black_fan(comments)
                    if result['is_black_fan']:
                        black_fan_count += 1
                        
            black_fan_ratio = black_fan_count / len(user_comments) if user_comments else 0
            
            result = {
                "sentiment_distribution": sentiment_distribution,
                "average_sentiment": float(average_sentiment),
                "sentiment_trend": sentiment_trend,
                "top_positive_comments": [
                    {
                        "content": c['content'],
                        "user": c['user'],
                        "sentiment": c['sentiment'],
                        "strength": c['strength'],
                        "created_at": c['created_at'].isoformat()
                    }
                    for c in top_positive
                ],
                "top_negative_comments": [
                    {
                        "content": c['content'],
                        "user": c['user'],
                        "sentiment": c['sentiment'],
                        "strength": c['strength'],
                        "created_at": c['created_at'].isoformat()
                    }
                    for c in top_negative
                ],
                "black_fan_ratio": float(black_fan_ratio)
            }
            
            # 生成可视化图表
            distribution_chart = self.visualizer.generate_sentiment_distribution(
                sentiment_distribution,
                title=f"情感分布分析 - {'明星' if celebrity_id else '微博'}"
            )
            if distribution_chart:
                result['distribution_chart'] = distribution_chart
                
            trend_chart = self.visualizer.generate_sentiment_trend(
                sentiment_trend,
                title=f"情感趋势分析 - {'明星' if celebrity_id else '微博'}"
            )
            if trend_chart:
                result['trend_chart'] = trend_chart
                
            # 保存分析结果
            if celebrity_id or post_id:
                save_result = self.visualizer.save_analysis_results(
                    result,
                    celebrity_id=celebrity_id,
                    post_id=post_id
                )
                if save_result:
                    result['saved'] = True
                    
            # 导出分析报告
            report_path = self.visualizer.export_analysis_report(result)
            if report_path:
                result['report_path'] = report_path
                
            return result
            
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
    
    # 创建情感分析器实例
    analyzer = SentimentAnalyzer(db_url)
    
    # 测试情感分析
    test_texts = [
        "这个明星真是太棒了，演技很好！",
        "一般般吧，没什么特别的。",
        "太差了，完全看不下去。",
        "这个产品很好用，推荐给大家！",
        "服务态度很差，不推荐。"
    ]
    
    print("\n测试情感分析:")
    for text in test_texts:
        result = analyzer.analyze_sentiment(text)
        print(f"\n文本: {text}")
        print(f"情感: {result['sentiment']}")
        print(f"置信度: {result['confidence']:.2f}")
        print(f"情感强度: {result['strength']:.2f}")
        print("各类别得分:")
        for label, score in result['scores'].items():
            print(f"- {label}: {score:.2f}")
    
    # 测试黑粉分析
    test_comments = [
        {
            'content': '这个明星演技太差了',
            'created_at': datetime.now() - timedelta(days=1)
        },
        {
            'content': '完全看不下去，浪费时间',
            'created_at': datetime.now() - timedelta(days=2)
        },
        {
            'content': '这个角色演得真烂',
            'created_at': datetime.now() - timedelta(days=3)
        },
        {
            'content': '太失望了，完全不符合预期',
            'created_at': datetime.now() - timedelta(days=4)
        },
        {
            'content': '这个明星真的不行',
            'created_at': datetime.now() - timedelta(days=5)
        }
    ]
    
    print("\n测试黑粉分析:")
    result = analyzer.analyze_black_fan(test_comments)
    print(f"是否为黑粉: {result['is_black_fan']}")
    print(f"黑粉得分: {result['score']:.2f}")
    print(f"原因: {result['reason']}")
    print("详细指标:")
    for metric, value in result['metrics'].items():
        print(f"- {metric}: {value:.2f}")
        
    # 测试舆论分析
    print("\n测试舆论分析:")
    public_opinion = analyzer.analyze_public_opinion(
        test_comments,
        celebrity_id=1
    )
    print(f"情感分布: {public_opinion['sentiment_distribution']}")
    print(f"平均情感强度: {public_opinion['average_sentiment']:.4f}")
    print(f"黑粉比例: {public_opinion['black_fan_ratio']:.4f}")
    print("\n最正面评论:")
    for comment in public_opinion['top_positive_comments']:
        print(f"- {comment['user']}: {comment['content']} (情感强度: {comment['strength']:.2f})")
    print("\n最负面评论:")
    for comment in public_opinion['top_negative_comments']:
        print(f"- {comment['user']}: {comment['content']} (情感强度: {comment['strength']:.2f})") 