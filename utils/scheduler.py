import logging
from typing import Dict, Any, Callable
from datetime import datetime, timedelta
import schedule
import time
import threading
from .email_sender import EmailSender
from analysis.heat_analyzer import HeatAnalyzer
from analysis.heat_alerter import HeatAlerter

class Scheduler:
    """定时任务管理器"""
    
    def __init__(self, db_url: str):
        """初始化定时任务管理器
        
        Args:
            db_url: 数据库连接URL
        """
        self.logger = logging.getLogger(__name__)
        self.email_sender = EmailSender()
        self.heat_analyzer = HeatAnalyzer(db_url)
        self.heat_alerter = HeatAlerter(db_url)
        self.running = False
        self.thread = None
        
    def start(self):
        """启动定时任务"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        """停止定时任务"""
        self.running = False
        if self.thread:
            self.thread.join()
            
    def _run_scheduler(self):
        """运行定时任务"""
        # 设置定时任务
        schedule.every(1).hours.do(self._check_heat_alerts)  # 每小时检查热度预警
        schedule.every().day.at("00:00").do(self._send_daily_report)  # 每天发送日报
        schedule.every().monday.at("00:00").do(self._send_weekly_report)  # 每周发送周报
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
            
    def _check_heat_alerts(self):
        """检查热度预警"""
        try:
            # 获取需要监控的明星列表
            query = """
                SELECT id, name
                FROM celebrities
                WHERE is_monitored = 1
            """
            
            with self.heat_analyzer.engine.connect() as conn:
                celebrities = conn.execute(text(query)).fetchall()
                
            # 检查每个明星的热度
            for celebrity in celebrities:
                alert_result = self.heat_alerter.check_celebrity_heat_alert(celebrity.id)
                
                if alert_result['has_alert']:
                    # 发送预警邮件
                    self.email_sender.send_heat_alert({
                        'celebrity_name': celebrity.name,
                        **alert_result
                    })
                    
        except Exception as e:
            self.logger.error(f"检查热度预警失败: {str(e)}")
            
    def _send_daily_report(self):
        """发送每日报告"""
        try:
            # 获取所有明星的热度数据
            query = """
                SELECT id, name
                FROM celebrities
                WHERE is_monitored = 1
            """
            
            with self.heat_analyzer.engine.connect() as conn:
                celebrities = conn.execute(text(query)).fetchall()
                
            # 生成每个明星的日报
            for celebrity in celebrities:
                heat_data = self.heat_analyzer.calculate_celebrity_heat(celebrity.id, days=1)
                
                if heat_data:
                    # 发送日报邮件
                    self.email_sender.send_heat_report({
                        'celebrity_name': celebrity.name,
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        **heat_data
                    })
                    
        except Exception as e:
            self.logger.error(f"发送每日报告失败: {str(e)}")
            
    def _send_weekly_report(self):
        """发送每周报告"""
        try:
            # 获取所有明星的热度数据
            query = """
                SELECT id, name
                FROM celebrities
                WHERE is_monitored = 1
            """
            
            with self.heat_analyzer.engine.connect() as conn:
                celebrities = conn.execute(text(query)).fetchall()
                
            # 生成每个明星的周报
            for celebrity in celebrities:
                heat_data = self.heat_analyzer.calculate_celebrity_heat(celebrity.id, days=7)
                
                if heat_data:
                    # 发送周报邮件
                    self.email_sender.send_heat_report({
                        'celebrity_name': celebrity.name,
                        'date': f"{datetime.now().strftime('%Y-%m-%d')} (周报)",
                        **heat_data
                    })
                    
        except Exception as e:
            self.logger.error(f"发送每周报告失败: {str(e)}")
            
    def add_custom_task(self, task_func: Callable, interval: int, unit: str = 'hours'):
        """添加自定义定时任务
        
        Args:
            task_func: 任务函数
            interval: 时间间隔
            unit: 时间单位（hours/minutes/seconds）
        """
        try:
            if unit == 'hours':
                schedule.every(interval).hours.do(task_func)
            elif unit == 'minutes':
                schedule.every(interval).minutes.do(task_func)
            elif unit == 'seconds':
                schedule.every(interval).seconds.do(task_func)
            else:
                raise ValueError(f"不支持的时间单位: {unit}")
                
        except Exception as e:
            self.logger.error(f"添加自定义任务失败: {str(e)}")

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 测试配置
    db_url = "mysql+pymysql://root:123456@localhost:3306/celebrity_analysis"
    
    # 创建定时任务管理器实例
    scheduler = Scheduler(db_url)
    
    # 启动定时任务
    scheduler.start()
    
    try:
        # 保持程序运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # 停止定时任务
        scheduler.stop() 