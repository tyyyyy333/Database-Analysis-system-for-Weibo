from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine, text
import json
import logging
from pathlib import Path
import jinja2
import os
from jinja2 import Environment, FileSystemLoader
from .data_collector import ReportDataCollector
from .chart_generator import ChartGenerator
from .prediction_model import PredictionModel
from .report_sender import ReportSender

class ReportGenerator:
    def __init__(self, db_url: str, smtp_config: Dict[str, Any], template_dir: str, output_dir: str):
        """
        初始化报告生成器
        
        Args:
            db_url: 数据库连接URL
            smtp_config: SMTP服务器配置
            template_dir: 模板目录
            output_dir: 输出目录
        """
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.data_collector = ReportDataCollector(db_url)
        self.chart_generator = ChartGenerator(output_dir)
        self.prediction_model = PredictionModel()
        self.report_sender = ReportSender(db_url, smtp_config)
        
        # 设置模板环境
        self.template_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_report(self, template_id: int, report_time: datetime) -> bool:
        """
        生成报告
        
        Args:
            template_id: 模板ID
            report_time: 报告时间
            
        Returns:
            生成是否成功
        """
        try:
            # 获取模板信息
            template = self._get_template(template_id)
            if not template:
                raise ValueError(f"模板不存在: {template_id}")
                
            # 确定时间范围
            start_time, end_time = self._get_time_range(template['report_type'], report_time)
            
            # 收集数据
            data = self._collect_report_data(template['report_type'], start_time, end_time)
            
            # 生成图表
            charts = self._generate_charts(data)
            
            # 生成预测
            predictions = self._generate_predictions(data)
            
            # 渲染报告
            report_content = self._render_template(template, data, charts, predictions)
            
            # 保存报告
            report_id = self._save_report_record(
                template_id=template_id,
                report_time=report_time,
                content=report_content,
                data=data,
                charts=charts,
                predictions=predictions
            )
            
            # 发送报告
            return self.report_sender.send_report(report_id)
            
        except Exception as e:
            self.logger.error(f"生成报告时出错: {str(e)}")
            return False
            
    def _get_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """
        获取报告模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            模板信息
        """
        query = """
            SELECT *
            FROM report_templates
            WHERE id = :template_id
            AND is_active = true
        """
        
        with self.data_collector.engine.connect() as conn:
            result = conn.execute(query, {'template_id': template_id}).fetchone()
            
        return dict(result) if result else None
        
    def _get_time_range(self, report_type: str, report_time: datetime) -> tuple:
        """
        获取报告时间范围
        
        Args:
            report_type: 报告类型
            report_time: 报告时间
            
        Returns:
            (开始时间, 结束时间)
        """
        if report_type == 'daily':
            start_time = report_time.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(days=1)
        elif report_type == 'weekly':
            start_time = report_time - timedelta(days=7)
            end_time = report_time
        else:  # monthly
            start_time = report_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_time = report_time
            
        return start_time, end_time
        
    def _collect_report_data(self, report_type: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """
        收集报告数据
        
        Args:
            report_type: 报告类型
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            报告数据
        """
        return {
            'heat_data': self.data_collector.collect_heat_data(start_time, end_time),
            'sentiment_data': self.data_collector.collect_sentiment_data(start_time, end_time),
            'alert_data': self.data_collector.collect_alert_data(start_time, end_time),
            'hot_topics': self.data_collector.collect_hot_topics(start_time, end_time),
            'typical_comments': self.data_collector.collect_typical_comments(start_time, end_time)
        }
        
    def _generate_charts(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        生成图表
        
        Args:
            data: 报告数据
            
        Returns:
            图表文件路径字典
        """
        return {
            'heat_trend': self.chart_generator.generate_heat_trend_chart(
                data['heat_data']['daily_data']
            ),
            'sentiment_dist': self.chart_generator.generate_sentiment_distribution_chart(
                data['sentiment_data']['stats']['distribution']
            ),
            'alert_stats': self.chart_generator.generate_alert_statistics_chart(
                data['alert_data']['daily_data']
            ),
            'heat_box': self.chart_generator.generate_heat_box_chart(
                data['heat_data']['daily_data']
            ),
            'topic_heat': self.chart_generator.generate_topic_heat_chart(
                data['hot_topics']
            )
        }
        
    def _generate_predictions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成预测
        
        Args:
            data: 报告数据
            
        Returns:
            预测结果
        """
        return {
            'heat': self.prediction_model.predict_heat_trend(
                data['heat_data']['daily_data']
            ),
            'sentiment': self.prediction_model.predict_sentiment_trend(
                data['sentiment_data']['daily_data']
            ),
            'alert': self.prediction_model.predict_alert_probability(
                data['heat_data']['daily_data'],
                data['sentiment_data']['daily_data']
            )
        }
        
    def _render_template(self, template: Dict[str, Any], data: Dict[str, Any],
                        charts: Dict[str, str], predictions: Dict[str, Any]) -> str:
        """
        渲染报告模板
        
        Args:
            template: 模板信息
            data: 报告数据
            charts: 图表文件路径
            predictions: 预测结果
            
        Returns:
            渲染后的报告内容
        """
        template = self.template_env.get_template(f"{template['report_type']}.html")
        return template.render(
            report_time=data['heat_data']['daily_data'][-1]['date'],
            heat_data=data['heat_data']['stats'],
            sentiment_data=data['sentiment_data']['stats'],
            alert_data=data['alert_data']['stats'],
            hot_topics=data['hot_topics'],
            typical_comments=data['typical_comments'],
            charts=charts,
            predictions=predictions,
            now=datetime.now()
        )
        
    def _save_report_record(self, template_id: int, report_time: datetime,
                           content: str, data: Dict[str, Any],
                           charts: Dict[str, str], predictions: Dict[str, Any]) -> int:
        """
        保存报告记录
        
        Args:
            template_id: 模板ID
            report_time: 报告时间
            content: 报告内容
            data: 报告数据
            charts: 图表文件路径
            predictions: 预测结果
            
        Returns:
            报告ID
        """
        query = """
            INSERT INTO report_records
            (template_id, report_time, content, data, charts, predictions, status, created_at)
            VALUES
            (:template_id, :report_time, :content, :data, :charts, :predictions, 'pending', NOW())
            RETURNING id
        """
        
        with self.data_collector.engine.connect() as conn:
            result = conn.execute(query, {
                'template_id': template_id,
                'report_time': report_time,
                'content': content,
                'data': data,
                'charts': charts,
                'predictions': predictions
            }).fetchone()
            
        return result[0]
        
    def generate_charts(self, data: Dict[str, Any], output_dir: str) -> Dict[str, str]:
        """生成报告图表"""
        charts = {}
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 生成热度趋势图
        if 'heat_data' in data:
            plt.figure(figsize=(10, 6))
            df = pd.DataFrame(data['heat_data']['trend'])
            plt.plot(df['date'], df['avg_heat'])
            plt.title('热度趋势')
            plt.xlabel('日期')
            plt.ylabel('平均热度')
            plt.xticks(rotation=45)
            plt.tight_layout()
            heat_trend_path = output_path / 'heat_trend.png'
            plt.savefig(heat_trend_path)
            plt.close()
            charts['heat_trend'] = str(heat_trend_path)
            
        # 生成情感分布图
        if 'sentiment_data' in data:
            plt.figure(figsize=(8, 8))
            df = pd.DataFrame(data['sentiment_data']['distribution'])
            plt.pie(df['count'], labels=df['sentiment'], autopct='%1.1f%%')
            plt.title('情感分布')
            sentiment_dist_path = output_path / 'sentiment_dist.png'
            plt.savefig(sentiment_dist_path)
            plt.close()
            charts['sentiment_dist'] = str(sentiment_dist_path)
            
        # 生成预警统计图
        if 'alert_data' in data:
            plt.figure(figsize=(10, 6))
            df = pd.DataFrame(data['alert_data']['stats'])
            plt.bar(df['alert_level'], df['count'])
            plt.title('预警统计')
            plt.xlabel('预警级别')
            plt.ylabel('数量')
            plt.tight_layout()
            alert_stats_path = output_path / 'alert_stats.png'
            plt.savefig(alert_stats_path)
            plt.close()
            charts['alert_stats'] = str(alert_stats_path)
            
        return charts 