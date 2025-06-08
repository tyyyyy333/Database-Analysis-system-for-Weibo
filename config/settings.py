import os
from pathlib import Path

# 项目基础路径配置
BASE_DIR = Path(__file__).resolve().parent.parent

# 数据存储路径配置
DATA_DIR = BASE_DIR / 'data'
CRAWLED_DATA_DIR = DATA_DIR / 'crawled'  # 爬取的原始数据
CLEANED_DATA_DIR = DATA_DIR / 'cleaned'  # 清洗后的数据
MODEL_DIR = DATA_DIR / 'models'  # 模型存储目录

# 创建必要的目录结构
for dir_path in [DATA_DIR, CRAWLED_DATA_DIR, CLEANED_DATA_DIR, MODEL_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 微博爬虫配置
WEIBO_SETTINGS = {
    'LOGIN_URL': 'https://weibo.com/login.php',
    'HEADERS': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    },
    'SCROLL_PAUSE_TIME': 2,  # 页面滚动间隔时间
    'MAX_SCROLL_TIMES': 10,  # 最大滚动次数
    'COMMENT_PAGE_SIZE': 20  # 评论分页大小
}

# 情感分析配置
SENTIMENT_SETTINGS = {
    'POSITIVE_THRESHOLD': 0.6,  # 正面情感阈值
    'NEGATIVE_THRESHOLD': 0.4,  # 负面情感阈值
    'MODEL_PATH': str(MODEL_DIR / 'sentiment_model'),
    'BATCH_SIZE': 32  # 批处理大小
}

# 黑粉识别配置
BLACK_FAN_SETTINGS = {
    'NEGATIVE_COMMENT_THRESHOLD': 3,  # 负面评论阈值
    'COMMENT_FREQUENCY_THRESHOLD': 10,  # 评论频率阈值
    'BLACK_SCORE_THRESHOLD': 8,  # 黑粉分数阈值
}

# 热度计算配置
HEAT_SETTINGS = {
    'LIKE_WEIGHT': 1,  # 点赞权重
    'COMMENT_WEIGHT': 2,  # 评论权重
    'REPOST_WEIGHT': 2,  # 转发权重
    'TOPIC_WEIGHT': 0.3,  # 话题权重
    'TIME_DECAY_FACTOR': 0.9  # 时间衰减因子
}

# 日志配置
LOG_SETTINGS = {
    'LOG_DIR': BASE_DIR / 'logs',
    'LOG_LEVEL': 'INFO',
    'LOG_FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

# 创建日志目录
LOG_SETTINGS['LOG_DIR'].mkdir(parents=True, exist_ok=True)

# Redis缓存配置
CACHE_SETTINGS = {
    'REDIS_HOST': 'localhost',
    'REDIS_PORT': 6379,
    'REDIS_DB': 0,
    'CACHE_EXPIRE_TIME': 3600  # 缓存过期时间（秒）
}

# 数据导出配置
EXPORT_SETTINGS = {
    'REPORT_TEMPLATE_DIR': BASE_DIR / 'templates',  # 报告模板目录
    'EXPORT_DIR': BASE_DIR / 'exports',  # 导出文件目录
    'SUPPORTED_FORMATS': ['pdf', 'html', 'excel']  # 支持的导出格式
}

# 创建导出目录
EXPORT_SETTINGS['EXPORT_DIR'].mkdir(parents=True, exist_ok=True) 