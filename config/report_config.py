import os
from typing import Dict, Any

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '123456'),
    'database': os.getenv('DB_NAME', 'celebrity_analysis'),
    'charset': 'utf8mb4'
}

# 数据库连接URL
DB_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

# SMTP配置
SMTP_CONFIG = {
    'host': os.getenv('SMTP_HOST', 'smtp.example.com'),
    'port': int(os.getenv('SMTP_PORT', 587)),
    'username': os.getenv('SMTP_USERNAME', 'user@example.com'),
    'password': os.getenv('SMTP_PASSWORD', 'password'),
    'use_tls': True,
    'from_email': os.getenv('SMTP_FROM_EMAIL', 'user@example.com'),
    'from_name': os.getenv('SMTP_FROM_NAME', '舆情分析系统')
}

# 报告配置
REPORT_CONFIG = {
    'template_dir': os.getenv('REPORT_TEMPLATE_DIR', 'templates/reports'),
    'output_dir': os.getenv('REPORT_OUTPUT_DIR', 'output/reports'),
    'chart_dir': os.getenv('REPORT_CHART_DIR', 'output/charts'),
    'max_retries': int(os.getenv('REPORT_MAX_RETRIES', 3)),
    'retry_interval': int(os.getenv('REPORT_RETRY_INTERVAL', 300)),  # 秒
}

# 预测模型配置
PREDICTION_CONFIG = {
    'heat_threshold': float(os.getenv('HEAT_THRESHOLD', 0.8)),
    'sentiment_threshold': float(os.getenv('SENTIMENT_THRESHOLD', -0.6)),
    'prediction_days': int(os.getenv('PREDICTION_DAYS', 7)),
    'min_data_points': int(os.getenv('MIN_DATA_POINTS', 7)),
}

# 图表配置
CHART_CONFIG = {
    'style': 'seaborn',
    'font_family': 'SimHei',
    'figure_size': (12, 6),
    'dpi': 300,
    'colors': {
        'positive': '#2ecc71',
        'negative': '#e74c3c',
        'neutral': '#95a5a6',
        'high': '#e74c3c',
        'medium': '#f1c40f',
        'low': '#3498db'
    }
}

# 日志配置
LOG_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': os.getenv('LOG_FILE', 'logs/report.log'),
    'max_size': int(os.getenv('LOG_MAX_SIZE', 10 * 1024 * 1024)),  # 10MB
    'backup_count': int(os.getenv('LOG_BACKUP_COUNT', 5))
}

# 定时任务配置
SCHEDULER_CONFIG = {
    'daily_time': os.getenv('DAILY_REPORT_TIME', '08:00'),
    'weekly_day': int(os.getenv('WEEKLY_REPORT_DAY', 1)),  # 1-7，表示周一至周日
    'weekly_time': os.getenv('WEEKLY_REPORT_TIME', '09:00'),
    'monthly_day': int(os.getenv('MONTHLY_REPORT_DAY', 1)),  # 1-31
    'monthly_time': os.getenv('MONTHLY_REPORT_TIME', '10:00'),
    'timezone': os.getenv('TIMEZONE', 'Asia/Shanghai')
}

def get_config() -> Dict[str, Any]:
    """
    获取完整配置
    
    Returns:
        配置字典
    """
    return {
        'db': DB_CONFIG,
        'db_url': DB_URL,
        'smtp': SMTP_CONFIG,
        'report': REPORT_CONFIG,
        'prediction': PREDICTION_CONFIG,
        'chart': CHART_CONFIG,
        'log': LOG_CONFIG,
        'scheduler': SCHEDULER_CONFIG
    } 