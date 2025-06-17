from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import schedule
import time
import threading
from sqlalchemy import create_engine, text
import logging
from pathlib import Path
import json

from .report_generator import ReportGenerator
from .report_sender import ReportSender

class ReportScheduler:
    def __init__(self, db_url: str, smtp_config: Dict[str, Any],
                 template_dir: str = 'templates/reports'):
        """
        初始化报告调度器
        
        Args:
            db_url: 数据库连接URL
            smtp_config: SMTP服务器配置
            template_dir: 报告模板目录
        """
        self.engine = create_engine(db_url)
        self.report_generator = ReportGenerator(db_url, template_dir)
        self.report_sender = ReportSender(db_url, smtp_config)
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
        
        # 调度任务线程
        self.scheduler_thread = None
        self.is_running = False
        
    def start(self):
        """启动调度器"""
        if self.is_running:
            return
            
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
    def stop(self):
        """停止调度器"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
            
    def _run_scheduler(self):
        """运行调度器"""
        # 设置每日报告任务
        schedule.every().day.at("00:00").do(self._generate_daily_reports)
        
        # 设置每周报告任务
        schedule.every().monday.at("00:00").do(self._generate_weekly_reports)
        
        # 设置每月报告任务
        schedule.every().day.at("00:00").do(self._check_monthly_reports)
        
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)
            
    def _generate_daily_reports(self):
        """生成每日报告"""
        try:
            # 获取所有每日报告模板
            templates = self._get_active_templates('daily')
            
            # 生成报告
            for template in templates:
                report_time = datetime.now() - timedelta(days=1)
                self._generate_and_send_report(template['id'], report_time)
                
        except Exception as e:
            self.logger.error(f"生成每日报告失败: {str(e)}")
            
    def _generate_weekly_reports(self):
        """生成每周报告"""
        try:
            # 获取所有每周报告模板
            templates = self._get_active_templates('weekly')
            
            # 生成报告
            for template in templates:
                report_time = datetime.now() - timedelta(days=7)
                self._generate_and_send_report(template['id'], report_time)
                
        except Exception as e:
            self.logger.error(f"生成每周报告失败: {str(e)}")
            
    def _check_monthly_reports(self):
        """检查并生成每月报告"""
        try:
            # 检查是否是月初
            now = datetime.now()
            if now.day != 1:
                return
                
            # 获取所有每月报告模板
            templates = self._get_active_templates('monthly')
            
            # 生成报告
            for template in templates:
                report_time = now - timedelta(days=1)
                self._generate_and_send_report(template['id'], report_time)
                
        except Exception as e:
            self.logger.error(f"生成每月报告失败: {str(e)}")
            
    def _get_active_templates(self, template_type: str) -> List[Dict[str, Any]]:
        """获取活跃的报告模板"""
        query = """
            SELECT * FROM report_templates
            WHERE template_type = :template_type
            AND is_active = TRUE
        """
        
        with self.engine.connect() as conn:
            results = conn.execute(text(query), {
                'template_type': template_type
            }).fetchall()
            
        return [dict(row) for row in results]
        
    def _generate_and_send_report(self, template_id: int, report_time: datetime):
        """生成并发送报告"""
        try:
            # 生成报告
            result = self.report_generator.generate_report(template_id, report_time)
            
            # 发送报告
            if result and 'report_id' in result:
                self.report_sender.send_report(result['report_id'])
                
        except Exception as e:
            self.logger.error(f"生成并发送报告失败: {str(e)}")
            
    def generate_report_now(self, template_id: int) -> bool:
        """
        立即生成报告
        
        Args:
            template_id: 模板ID
            
        Returns:
            是否生成成功
        """
        try:
            # 生成报告
            result = self.report_generator.generate_report(template_id, datetime.now())
            
            # 发送报告
            if result and 'report_id' in result:
                return self.report_sender.send_report(result['report_id'])
                
            return False
            
        except Exception as e:
            self.logger.error(f"立即生成报告失败: {str(e)}")
            return False 
 
 