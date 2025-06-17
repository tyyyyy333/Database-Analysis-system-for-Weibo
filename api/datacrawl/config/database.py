import os

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# SQLite数据库配置
DB_CONFIG = {
    'database': os.path.join(BASE_DIR, 'data', 'celebrity_analysis.db')
} 