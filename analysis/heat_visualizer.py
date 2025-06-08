import logging
from typing import Dict, List, Any, Optional
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
from pathlib import Path
from sqlalchemy import create_engine, text
import json
import numpy as np

class HeatVisualizer:
    """热度分析可视化器"""
    
    def __init__(self, db_url: str, output_dir: str = 'data/visualizations'):
        """初始化热度分析可视化器
        
        Args:
            db_url: 数据库连接URL
            output_dir: 图表输出目录
        """
        self.logger = logging.getLogger(__name__)
        self.engine = create_engine(db_url)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置图表样式
        plt.style.use('seaborn')
        sns.set_palette("husl")
        
    def generate_heat_trend(self, trend_data: List[Dict[str, Any]], 
                          title: str = "热度趋势") -> str:
        """生成热度趋势图
        
        Args:
            trend_data: 热度趋势数据
            title: 图表标题
            
        Returns:
            str: 图表保存路径
        """
        try:
            df = pd.DataFrame(trend_data)
            df['date'] = pd.to_datetime(df['date'])
            
            plt.figure(figsize=(12, 6))
            plt.plot(df['date'], df['heat'], marker='o', linestyle='-', color='#FF6B6B')
            plt.title(title)
            plt.xlabel('日期')
            plt.ylabel('热度值')
            plt.xticks(rotation=45)
            plt.grid(True)
            
            # 添加趋势线
            z = np.polyfit(range(len(df)), df['heat'], 1)
            p = np.poly1d(z)
            plt.plot(df['date'], p(range(len(df))), "r--", alpha=0.8)
            
            # 保存图表
            chart_path = self.output_dir / f'heat_trend_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            plt.savefig(chart_path, bbox_inches='tight', dpi=300)
            plt.close()
            
            return str(chart_path)
            
        except Exception as e:
            self.logger.error(f"生成热度趋势图失败: {str(e)}")
            return None
            
    def generate_heat_distribution(self, distribution_data: Dict[str, int], 
                                 title: str = "热度分布") -> str:
        """生成热度分布图
        
        Args:
            distribution_data: 热度分布数据
            title: 图表标题
            
        Returns:
            str: 图表保存路径
        """
        try:
            plt.figure(figsize=(10, 6))
            plt.bar(
                distribution_data.keys(),
                distribution_data.values(),
                color=['#4ECDC4', '#FF6B6B', '#45B7D1']
            )
            plt.title(title)
            plt.xlabel('热度级别')
            plt.ylabel('数量')
            
            # 添加数值标签
            for i, v in enumerate(distribution_data.values()):
                plt.text(i, v, str(v), ha='center', va='bottom')
            
            # 保存图表
            chart_path = self.output_dir / f'heat_distribution_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            plt.savefig(chart_path, bbox_inches='tight', dpi=300)
            plt.close()
            
            return str(chart_path)
            
        except Exception as e:
            self.logger.error(f"生成热度分布图失败: {str(e)}")
            return None
            
    def generate_topic_heat_map(self, topic_data: List[Dict[str, Any]], 
                              title: str = "话题热度地图") -> str:
        """生成话题热度地图
        
        Args:
            topic_data: 话题热度数据
            title: 图表标题
            
        Returns:
            str: 图表保存路径
        """
        try:
            df = pd.DataFrame(topic_data)
            
            plt.figure(figsize=(12, 8))
            sns.heatmap(
                df.pivot_table(
                    values='heat',
                    index='date',
                    columns='topic',
                    aggfunc='mean'
                ),
                cmap='YlOrRd',
                annot=True,
                fmt='.2f'
            )
            plt.title(title)
            plt.xlabel('话题')
            plt.ylabel('日期')
            plt.xticks(rotation=45)
            
            # 保存图表
            chart_path = self.output_dir / f'topic_heat_map_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            plt.savefig(chart_path, bbox_inches='tight', dpi=300)
            plt.close()
            
            return str(chart_path)
            
        except Exception as e:
            self.logger.error(f"生成话题热度地图失败: {str(e)}")
            return None
            
    def generate_celebrity_heat_comparison(self, celebrity_data: List[Dict[str, Any]], 
                                        title: str = "明星热度对比") -> str:
        """生成明星热度对比图
        
        Args:
            celebrity_data: 明星热度数据
            title: 图表标题
            
        Returns:
            str: 图表保存路径
        """
        try:
            df = pd.DataFrame(celebrity_data)
            
            plt.figure(figsize=(12, 6))
            sns.barplot(
                data=df,
                x='celebrity_name',
                y='heat',
                palette='viridis'
            )
            plt.title(title)
            plt.xlabel('明星')
            plt.ylabel('热度值')
            plt.xticks(rotation=45)
            
            # 添加数值标签
            for i, v in enumerate(df['heat']):
                plt.text(i, v, f'{v:.2f}', ha='center', va='bottom')
            
            # 保存图表
            chart_path = self.output_dir / f'celebrity_heat_comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            plt.savefig(chart_path, bbox_inches='tight', dpi=300)
            plt.close()
            
            return str(chart_path)
            
        except Exception as e:
            self.logger.error(f"生成明星热度对比图失败: {str(e)}")
            return None
            
    def save_analysis_results(self, results: Dict[str, Any], 
                            celebrity_id: Optional[int] = None,
                            topic: Optional[str] = None) -> bool:
        """保存分析结果到数据库
        
        Args:
            results: 分析结果
            celebrity_id: 明星ID
            topic: 话题关键词
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 保存热度分析结果
            heat_query = """
                INSERT INTO heat_analysis_results 
                (celebrity_id, topic, total_heat, average_heat, 
                 heat_distribution, heat_trend, created_at)
                VALUES (:celebrity_id, :topic, :total_heat, :average_heat,
                        :heat_distribution, :heat_trend, :created_at)
            """
            
            with self.engine.connect() as conn:
                conn.execute(
                    text(heat_query),
                    {
                        'celebrity_id': celebrity_id,
                        'topic': topic,
                        'total_heat': results['total_heat'],
                        'average_heat': results['average_heat'],
                        'heat_distribution': json.dumps(results['heat_distribution']),
                        'heat_trend': json.dumps(results['heat_trend']),
                        'created_at': datetime.now()
                    }
                )
                
            # 保存热度最高的微博
            if 'top_posts' in results:
                posts_query = """
                    INSERT INTO heat_analysis_posts
                    (analysis_id, post_id, content, heat, created_at)
                    VALUES (:analysis_id, :post_id, :content, :heat, :created_at)
                """
                
                # 获取刚插入的分析结果ID
                analysis_id_query = """
                    SELECT LAST_INSERT_ID() as id
                """
                with self.engine.connect() as conn:
                    analysis_id = conn.execute(text(analysis_id_query)).scalar()
                    
                    for post in results['top_posts']:
                        conn.execute(
                            text(posts_query),
                            {
                                'analysis_id': analysis_id,
                                'post_id': post['id'],
                                'content': post['content'],
                                'heat': post['heat'],
                                'created_at': post['created_at']
                            }
                        )
                        
            return True
            
        except Exception as e:
            self.logger.error(f"保存分析结果失败: {str(e)}")
            return False
            
    def export_analysis_report(self, results: Dict[str, Any], 
                             output_path: Optional[str] = None) -> str:
        """导出分析报告
        
        Args:
            results: 分析结果
            output_path: 输出路径，可选
            
        Returns:
            str: 报告文件路径
        """
        try:
            if output_path is None:
                output_path = self.output_dir / f'heat_analysis_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
                
            # 生成HTML报告
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>热度分析报告</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .section {{ margin-bottom: 20px; }}
                    .metric {{ margin: 10px 0; }}
                    .post {{ margin: 5px 0; padding: 5px; border: 1px solid #ddd; }}
                </style>
            </head>
            <body>
                <h1>热度分析报告</h1>
                <div class="section">
                    <h2>热度概览</h2>
                    <div class="metric">
                        <p>总热度: {results['total_heat']:.2f}</p>
                        <p>平均热度: {results['average_heat']:.2f}</p>
                    </div>
                </div>
                <div class="section">
                    <h2>热度分布</h2>
                    <div class="metric">
                        <p>高热: {results['heat_distribution']['high']}</p>
                        <p>中热: {results['heat_distribution']['medium']}</p>
                        <p>低热: {results['heat_distribution']['low']}</p>
                    </div>
                </div>
                <div class="section">
                    <h2>热度最高的微博</h2>
                    {self._format_posts_html(results.get('top_posts', []))}
                </div>
            </body>
            </html>
            """
            
            # 保存报告
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"导出分析报告失败: {str(e)}")
            return None
            
    def _format_posts_html(self, posts: List[Dict[str, Any]]) -> str:
        """格式化微博HTML
        
        Args:
            posts: 微博列表
            
        Returns:
            str: 格式化后的HTML
        """
        html = ""
        for post in posts:
            html += f"""
            <div class="post">
                <p><strong>热度值: {post['heat']:.2f}</strong> ({post['created_at']})</p>
                <p>{post['content']}</p>
            </div>
            """
        return html

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 测试配置
    db_url = "mysql+pymysql://root:123456@localhost:3306/celebrity_analysis"
    
    # 创建可视化器实例
    visualizer = HeatVisualizer(db_url)
    
    # 测试数据
    test_data = {
        "total_heat": 85.5,
        "average_heat": 0.75,
        "heat_distribution": {
            "high": 5,
            "medium": 10,
            "low": 15
        },
        "heat_trend": [
            {"date": "2024-03-01", "heat": 0.8},
            {"date": "2024-03-02", "heat": 0.7}
        ],
        "top_posts": [
            {
                "id": 1,
                "content": "测试微博1",
                "heat": 0.9,
                "created_at": "2024-03-01T12:00:00"
            },
            {
                "id": 2,
                "content": "测试微博2",
                "heat": 0.8,
                "created_at": "2024-03-01T13:00:00"
            }
        ]
    }
    
    # 测试生成图表
    trend_chart = visualizer.generate_heat_trend(
        test_data['heat_trend']
    )
    print(f"热度趋势图保存路径: {trend_chart}")
    
    distribution_chart = visualizer.generate_heat_distribution(
        test_data['heat_distribution']
    )
    print(f"热度分布图保存路径: {distribution_chart}")
    
    # 测试保存分析结果
    save_result = visualizer.save_analysis_results(
        test_data,
        celebrity_id=1
    )
    print(f"保存分析结果: {'成功' if save_result else '失败'}")
    
    # 测试导出报告
    report_path = visualizer.export_analysis_report(test_data)
    print(f"分析报告保存路径: {report_path}") 