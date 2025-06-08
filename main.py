import logging
import os
from datetime import datetime
from typing import Dict, Any

from config.report_config import get_config
from database.db_utils import DatabaseUtils
from datacrawl.crawler import WeiboCrawler
from data_processing.data_cleaner import DataCleaner
from sentiment.sentiment_analyzer import SentimentAnalyzer
from sentiment.black_fan_analyzer import BlackFanAnalyzer
from analysis.heat_analyzer import HeatAnalyzer
from analysis.heat_visualizer import HeatVisualizer
from analysis.heat_alerter import HeatAlerter
from report.report_generator import ReportGenerator
from report.report_scheduler import ReportScheduler
from utils.scheduler import Scheduler

class CelebritySentimentSystem:
    def __init__(self):
        # 加载配置
        self.config = get_config()
        
        # 初始化日志
        self._setup_logging()
        
        # 初始化数据库连接
        self.db_utils = DatabaseUtils(self.config['db_url'])
        
        # 初始化各个模块
        self._init_modules()
        
        # 初始化调度器
        self.scheduler = Scheduler()
        
        self.logger.info("系统初始化完成")

    def _setup_logging(self):
        """配置日志系统"""
        log_config = self.config['log']
        os.makedirs(os.path.dirname(log_config['file']), exist_ok=True)
        
        logging.basicConfig(
            level=log_config['level'],
            format=log_config['format'],
            filename=log_config['file']
        )
        self.logger = logging.getLogger(__name__)

    def _init_modules(self):
        """初始化各个功能模块"""
        # 数据采集模块
        self.crawler = WeiboCrawler(self.db_utils)
        
        # 数据清洗模块
        self.data_cleaner = DataCleaner(self.db_utils)
        
        # 情感分析模块
        self.sentiment_analyzer = SentimentAnalyzer(self.db_utils)
        self.black_fan_analyzer = BlackFanAnalyzer(self.db_utils)
        
        # 热度分析模块
        self.heat_analyzer = HeatAnalyzer(self.db_utils)
        self.heat_visualizer = HeatVisualizer()
        self.heat_alerter = HeatAlerter(self.db_utils)
        
        # 报告生成模块
        self.report_generator = ReportGenerator(
            self.db_utils,
            self.config['report'],
            self.config['smtp']
        )
        
        # 报告调度模块
        self.report_scheduler = ReportScheduler(
            self.db_utils,
            self.report_generator,
            self.config['scheduler']
        )

    def start(self):
        """启动系统"""
        try:
            self.logger.info("系统启动")
            
            # 启动数据采集任务
            self.scheduler.add_job(
                self.crawler.start_crawling,
                'interval',
                hours=1,
                id='data_crawling'
            )
            
            # 启动数据清洗任务
            self.scheduler.add_job(
                self.data_cleaner.clean_all_data,
                'interval',
                hours=1,
                id='data_cleaning'
            )
            
            # 启动情感分析任务
            self.scheduler.add_job(
                self.sentiment_analyzer.analyze_all_comments,
                'interval',
                hours=2,
                id='sentiment_analysis'
            )
            
            # 启动热度分析任务
            self.scheduler.add_job(
                self.heat_analyzer.analyze_all_heat,
                'interval',
                hours=2,
                id='heat_analysis'
            )
            
            # 启动预警检测任务
            self.scheduler.add_job(
                self.heat_alerter.check_alerts,
                'interval',
                minutes=30,
                id='alert_checking'
            )
            
            # 启动报告调度任务
            self.report_scheduler.start()
            
            # 启动调度器
            self.scheduler.start()
            
            self.logger.info("所有任务已启动")
            
        except Exception as e:
            self.logger.error(f"系统启动失败: {e}")
            raise

    def stop(self):
        """停止系统"""
        try:
            self.logger.info("系统停止")
            
            # 停止调度器
            self.scheduler.shutdown()
            
            # 停止报告调度器
            self.report_scheduler.stop()
            
            # 关闭数据库连接
            self.db_utils.close()
            
            self.logger.info("系统已安全停止")
            
        except Exception as e:
            self.logger.error(f"系统停止失败: {e}")
            raise

    def generate_report_now(self, template_id: int):
        """立即生成报告"""
        try:
            self.logger.info(f"开始生成报告，模板ID: {template_id}")
            success = self.report_generator.generate_report(template_id)
            if success:
                self.logger.info("报告生成成功")
            else:
                self.logger.error("报告生成失败")
            return success
        except Exception as e:
            self.logger.error(f"报告生成异常: {e}")
            return False

    def analyze_black_fans(self):
        """分析黑粉数据"""
        try:
            self.logger.info("开始分析黑粉数据")
            
            # 获取黑粉分析数据
            ranking_data = self.black_fan_analyzer.analyze_black_fan_ranking()
            location_data = self.black_fan_analyzer.analyze_black_fan_location()
            gender_data = self.black_fan_analyzer.analyze_black_fan_gender()
            activity_data = self.black_fan_analyzer.analyze_black_fan_activity()
            content_data = self.black_fan_analyzer.analyze_black_fan_content()
            
            # 生成可视化图表
            output_dir = self.config['report']['chart_dir']
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.black_fan_analyzer.visualize_black_fan_ranking(
                ranking_data,
                f"{output_dir}/black_fan_ranking_{timestamp}.png"
            )
            self.black_fan_analyzer.visualize_black_fan_location(
                location_data,
                f"{output_dir}/black_fan_location_{timestamp}.png"
            )
            self.black_fan_analyzer.visualize_black_fan_gender(
                gender_data,
                f"{output_dir}/black_fan_gender_{timestamp}.png"
            )
            self.black_fan_analyzer.visualize_black_fan_activity(
                activity_data,
                f"{output_dir}/black_fan_activity_{timestamp}.png"
            )
            self.black_fan_analyzer.visualize_black_fan_content(
                content_data,
                f"{output_dir}/black_fan_content_{timestamp}.png"
            )
            
            self.logger.info("黑粉数据分析完成")
            return True
            
        except Exception as e:
            self.logger.error(f"黑粉数据分析失败: {e}")
            return False

def main():
    """主程序入口"""
    system = CelebritySentimentSystem()
    try:
        system.start()
        # 这里可以添加命令行交互或其他控制逻辑
    except KeyboardInterrupt:
        system.stop()
    except Exception as e:
        logging.error(f"系统运行异常: {e}")
        system.stop()

if __name__ == "__main__":
    main() 