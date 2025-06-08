from typing import Dict, List, Any, Optional
import pandas as pd
from sqlalchemy import create_engine
import openai
from pandasai import PandasAI
import logging
from pathlib import Path
import json
import matplotlib.pyplot as plt
import seaborn as sns
import os
import datetime
import numpy as np

class AIAnalyzer:
    """AI智能分析器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db_engine = create_engine(config['database_url'])
        self.pandas_ai = PandasAI()
        self._load_prompts()
    
    def _load_prompts(self):
        """加载提示词模板"""
        prompt_file = Path(__file__).parent / 'prompts' / 'analysis_prompts.json'
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                self.prompts = json.load(f)
        else:
            self.prompts = self._get_default_prompts()
    
    def _get_default_prompts(self) -> Dict:
        """获取默认提示词模板"""
        return {
            'trend_analysis': "分析{celebrity}在{time_range}内的{metric}趋势，并解释关键变化点",
            'sentiment_analysis': "分析{celebrity}的评论情感分布，识别主要情感倾向和变化",
            'fan_analysis': "分析{celebrity}的粉丝画像，包括活跃度、互动类型等特征",
            'comparison_analysis': "比较{celebrity1}和{celebrity2}在{metric}方面的差异"
        }
    
    def analyze_trend(self, celebrity: str, metric: str, time_range: str) -> Dict:
        """分析趋势
        
        Args:
            celebrity: 明星名称
            metric: 分析指标
            time_range: 时间范围
            
        Returns:
            分析结果
        """
        try:
            # 获取数据
            query = f"""
            SELECT created_at, {metric}
            FROM post
            WHERE celebrity_id = '{celebrity}'
            AND created_at >= DATE_SUB(NOW(), INTERVAL {time_range})
            ORDER BY created_at
            """
            df = pd.read_sql(query, self.db_engine)
            
            # 使用PandasAI分析
            prompt = self.prompts['trend_analysis'].format(
                celebrity=celebrity,
                time_range=time_range,
                metric=metric
            )
            analysis = self.pandas_ai.run(df, prompt)
            
            return {
                'status': 'success',
                'data': analysis,
                'visualization': self._generate_trend_chart(df, metric)
            }
        except Exception as e:
            self.logger.error(f"趋势分析失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def analyze_sentiment(self, celebrity: str) -> Dict:
        """分析情感
        
        Args:
            celebrity: 明星名称
            
        Returns:
            情感分析结果
        """
        try:
            # 获取情感数据
            query = """
            SELECT s.sentiment_category, COUNT(*) as count
            FROM sentiment_for_comment s
            JOIN comment c ON s.comment_id = c.comment_id
            JOIN post p ON c.post_id = p.post_id
            WHERE p.celebrity_id = %s
            GROUP BY s.sentiment_category
            """
            df = pd.read_sql(query, self.db_engine, params=[celebrity])
            
            # 使用PandasAI分析
            prompt = self.prompts['sentiment_analysis'].format(
                celebrity=celebrity
            )
            analysis = self.pandas_ai.run(df, prompt)
            
            return {
                'status': 'success',
                'data': analysis,
                'visualization': self._generate_sentiment_chart(df)
            }
        except Exception as e:
            self.logger.error(f"情感分析失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def analyze_fans(self, celebrity: str) -> Dict:
        """分析粉丝画像
        
        Args:
            celebrity: 明星名称
            
        Returns:
            粉丝分析结果
        """
        try:
            # 获取粉丝数据
            query = """
            SELECT u.*, COUNT(c.comment_id) as comment_count
            FROM user u
            JOIN comment c ON u.fan_id = c.fan_id
            JOIN post p ON c.post_id = p.post_id
            WHERE p.celebrity_id = %s
            GROUP BY u.fan_id
            """
            df = pd.read_sql(query, self.db_engine, params=[celebrity])
            
            # 使用PandasAI分析
            prompt = self.prompts['fan_analysis'].format(
                celebrity=celebrity
            )
            analysis = self.pandas_ai.run(df, prompt)
            
            return {
                'status': 'success',
                'data': analysis,
                'visualization': self._generate_fan_chart(df)
            }
        except Exception as e:
            self.logger.error(f"粉丝分析失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def compare_celebrities(self, celebrity1: str, celebrity2: str, metric: str) -> Dict:
        """比较两个明星
        
        Args:
            celebrity1: 第一个明星
            celebrity2: 第二个明星
            metric: 比较指标
            
        Returns:
            比较分析结果
        """
        try:
            # 获取比较数据
            query = """
            SELECT celebrity_id, {metric}, created_at
            FROM post
            WHERE celebrity_id IN (%s, %s)
            ORDER BY created_at
            """.format(metric=metric)
            df = pd.read_sql(query, self.db_engine, params=[celebrity1, celebrity2])
            
            # 使用PandasAI分析
            prompt = self.prompts['comparison_analysis'].format(
                celebrity1=celebrity1,
                celebrity2=celebrity2,
                metric=metric
            )
            analysis = self.pandas_ai.run(df, prompt)
            
            return {
                'status': 'success',
                'data': analysis,
                'visualization': self._generate_comparison_chart(df, metric)
            }
        except Exception as e:
            self.logger.error(f"明星比较分析失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _generate_trend_chart(self, df: pd.DataFrame, metric: str) -> str:
        """生成趋势分析图表
        
        Args:
            df: 包含时间序列数据的DataFrame
            metric: 要分析的指标名称
            
        Returns:
            图表保存路径
        """
        try:
            plt.figure(figsize=(12, 6))
            sns.set_style("whitegrid")
            
            # 绘制趋势线
            sns.lineplot(data=df, x='date', y=metric, marker='o')
            
            # 添加移动平均线
            df['ma'] = df[metric].rolling(window=7).mean()
            sns.lineplot(data=df, x='date', y='ma', color='red', linestyle='--', label='7日移动平均')
            
            # 设置图表样式
            plt.title(f'{metric}趋势分析', fontsize=14, pad=15)
            plt.xlabel('日期', fontsize=12)
            plt.ylabel(metric, fontsize=12)
            plt.xticks(rotation=45)
            plt.legend()
            
            # 保存图表
            chart_path = f'data/charts/trend_{metric}_{datetime.datetime.now().strftime("%Y%m%d")}.png'
            os.makedirs(os.path.dirname(chart_path), exist_ok=True)
            plt.savefig(chart_path, bbox_inches='tight', dpi=300)
            plt.close()
            
            return chart_path
        except Exception as e:
            self.logger.error(f"生成趋势图表失败: {str(e)}")
            return None
    
    def _generate_sentiment_chart(self, df: pd.DataFrame) -> str:
        """生成情感分析图表
        
        Args:
            df: 包含情感分析数据的DataFrame
            
        Returns:
            图表保存路径
        """
        try:
            # 创建子图
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # 情感分布饼图
            sentiment_counts = df['sentiment'].value_counts()
            ax1.pie(sentiment_counts, labels=sentiment_counts.index, autopct='%1.1f%%')
            ax1.set_title('情感分布')
            
            # 情感趋势折线图
            sentiment_trend = df.groupby(['date', 'sentiment']).size().unstack()
            sentiment_trend.plot(kind='line', ax=ax2, marker='o')
            ax2.set_title('情感趋势变化')
            ax2.set_xlabel('日期')
            ax2.set_ylabel('数量')
            plt.xticks(rotation=45)
            
            # 保存图表
            chart_path = f'data/charts/sentiment_{datetime.datetime.now().strftime("%Y%m%d")}.png'
            os.makedirs(os.path.dirname(chart_path), exist_ok=True)
            plt.savefig(chart_path, bbox_inches='tight', dpi=300)
            plt.close()
            
            return chart_path
        except Exception as e:
            self.logger.error(f"生成情感分析图表失败: {str(e)}")
            return None
    
    def _generate_fan_chart(self, df: pd.DataFrame) -> str:
        """生成粉丝分析图表
        
        Args:
            df: 包含粉丝数据的DataFrame
            
        Returns:
            图表保存路径
        """
        try:
            # 创建子图
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            
            # 性别分布
            gender_counts = df['gender'].value_counts()
            ax1.pie(gender_counts, labels=gender_counts.index, autopct='%1.1f%%')
            ax1.set_title('粉丝性别分布')
            
            # 地区分布（Top 10）
            location_counts = df['location'].value_counts().head(10)
            location_counts.plot(kind='bar', ax=ax2)
            ax2.set_title('粉丝地区分布(Top 10)')
            plt.xticks(rotation=45)
            
            # 粉丝数分布
            sns.histplot(data=df, x='followers_count', bins=30, ax=ax3)
            ax3.set_title('粉丝数分布')
            ax3.set_xlabel('粉丝数')
            ax3.set_ylabel('数量')
            
            # 关注数分布
            sns.histplot(data=df, x='following_count', bins=30, ax=ax4)
            ax4.set_title('关注数分布')
            ax4.set_xlabel('关注数')
            ax4.set_ylabel('数量')
            
            # 调整布局
            plt.tight_layout()
            
            # 保存图表
            chart_path = f'data/charts/fan_analysis_{datetime.datetime.now().strftime("%Y%m%d")}.png'
            os.makedirs(os.path.dirname(chart_path), exist_ok=True)
            plt.savefig(chart_path, bbox_inches='tight', dpi=300)
            plt.close()
            
            return chart_path
        except Exception as e:
            self.logger.error(f"生成粉丝分析图表失败: {str(e)}")
            return None
    
    def _generate_comparison_chart(self, df: pd.DataFrame, metric: str) -> str:
        """生成明星比较图表
        
        Args:
            df: 包含比较数据的DataFrame
            metric: 要比较的指标名称
            
        Returns:
            图表保存路径
        """
        try:
            plt.figure(figsize=(12, 6))
            sns.set_style("whitegrid")
            
            # 绘制对比柱状图
            sns.barplot(data=df, x='celebrity', y=metric)
            
            # 设置图表样式
            plt.title(f'{metric}对比分析', fontsize=14, pad=15)
            plt.xlabel('明星', fontsize=12)
            plt.ylabel(metric, fontsize=12)
            plt.xticks(rotation=45)
            
            # 添加数值标签
            for i, v in enumerate(df[metric]):
                plt.text(i, v, f'{v:.0f}', ha='center', va='bottom')
            
            # 保存图表
            chart_path = f'data/charts/comparison_{metric}_{datetime.datetime.now().strftime("%Y%m%d")}.png'
            os.makedirs(os.path.dirname(chart_path), exist_ok=True)
            plt.savefig(chart_path, bbox_inches='tight', dpi=300)
            plt.close()
            
            return chart_path
        except Exception as e:
            self.logger.error(f"生成比较分析图表失败: {str(e)}")
            return None

if __name__ == "__main__":
    # 测试配置
    test_config = {
        'database_url': 'mysql://root:123456@localhost/celebrity_sentiment',
        'openai_api_key': 'your-api-key-here'
    }
    
    # 创建分析器实例
    analyzer = AIAnalyzer(test_config)
    
    # 测试图表生成
    print("\n测试图表生成:")
    
    # 生成测试数据
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    test_data = pd.DataFrame({
        'date': dates,
        'likes': np.random.randint(1000, 5000, size=len(dates)),
        'sentiment': np.random.choice(['正面', '中性', '负面'], size=len(dates)),
        'gender': np.random.choice(['男', '女'], size=len(dates)),
        'location': np.random.choice(['北京', '上海', '广州', '深圳', '杭州'], size=len(dates)),
        'followers_count': np.random.randint(1000, 10000, size=len(dates)),
        'following_count': np.random.randint(100, 1000, size=len(dates))
    })
    
    # 测试趋势图表
    trend_chart = analyzer._generate_trend_chart(test_data, 'likes')
    print(f"趋势图表生成: {'成功' if trend_chart else '失败'}")
    
    # 测试情感分析图表
    sentiment_chart = analyzer._generate_sentiment_chart(test_data)
    print(f"情感分析图表生成: {'成功' if sentiment_chart else '失败'}")
    
    # 测试粉丝分析图表
    fan_chart = analyzer._generate_fan_chart(test_data)
    print(f"粉丝分析图表生成: {'成功' if fan_chart else '失败'}")
    
    # 测试比较分析图表
    comparison_data = pd.DataFrame({
        'celebrity': ['明星1', '明星2', '明星3'],
        'likes': [5000, 3000, 4000]
    })
    comparison_chart = analyzer._generate_comparison_chart(comparison_data, 'likes')
    print(f"比较分析图表生成: {'成功' if comparison_chart else '失败'}") 