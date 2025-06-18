BOT_NAME = 'weibo_spider'

SPIDER_MODULES = ['datacrawl.weibo_spider.spiders']
NEWSPIDER_MODULE = 'datacrawl.weibo_spider.spiders'

# 爬虫设置
ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 8  # 降低并发数
DOWNLOAD_DELAY = 5  # 增加延迟到5秒
RANDOMIZE_DOWNLOAD_DELAY = True
DOWNLOAD_TIMEOUT = 30  # 增加超时时间

# 启用中间件
DOWNLOADER_MIDDLEWARES = {
    'datacrawl.weibo_spider.middlewares.UserAgentMiddleware': 543,
    'datacrawl.weibo_spider.middlewares.ProxyMiddleware': 544,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
}

# 代理设置
PROXY_LIST = [
    # 这里添加您的代理IP列表，格式如下：
    # 'http://username:password@ip:port',
    # 'http://ip:port',
    # 'socks5://ip:port',
]

# 数据库设置
DATABASE = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',
    'database': 'celebrity_analysis'
}

# 启用管道
ITEM_PIPELINES = {
    'datacrawl.weibo_spider.pipelines.WeiboPipeline': 300,
}

# 日志设置
LOG_LEVEL = 'DEBUG'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'

# 重试设置
RETRY_ENABLED = True
RETRY_TIMES = 5  # 增加重试次数
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429, 403, 404]
DOWNLOADER_RETRY_DELAY = 10  # 重试延迟时间

# Cookie设置
COOKIES_ENABLED = True
COOKIES_DEBUG = True

# 并发设置
CONCURRENT_REQUESTS_PER_DOMAIN = 4
CONCURRENT_REQUESTS_PER_IP = 4

# 自动限速
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = True 