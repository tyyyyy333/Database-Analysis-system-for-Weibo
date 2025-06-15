import os
import json
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from .weibo_spider.spiders.user import UserSpider
from .weibo_spider.spiders.tweet import TweetSpider
from .weibo_spider.spiders.comment import CommentSpider

class WeiboSpiderRunner:
    def __init__(self, db_config):
        self.settings = {
            'BOT_NAME': 'weibo_spider',
            'SPIDER_MODULES': ['datacrawl.weibo_spider.spiders'],
            'NEWSPIDER_MODULE': 'datacrawl.weibo_spider.spiders',
            'ROBOTSTXT_OBEY': False,
            'COOKIES_ENABLED': False,
            'CONCURRENT_REQUESTS': 16,
            'DOWNLOAD_DELAY': 1,
            'DOWNLOADER_MIDDLEWARES': {
                'datacrawl.weibo_spider.middlewares.UserAgentMiddleware': 543,
            },
            'ITEM_PIPELINES': {
                'datacrawl.weibo_spider.pipelines.WeiboPipeline': 300,
            },
            'DEFAULT_REQUEST_HEADERS': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
                'cookie': ''  # 需要填入cookie
            },
            'DATABASE': db_config
        }
        
    def set_cookie(self, cookie):
        """设置微博cookie"""
        self.settings['DEFAULT_REQUEST_HEADERS']['cookie'] = cookie
        
    def run_spider(self, celebrity_ids, start_date=None, end_date=None):
        """
        运行爬虫
        :param celebrity_ids: 明星微博ID列表
        :param start_date: 开始日期，格式：YYYY-MM-DD
        :param end_date: 结束日期，格式：YYYY-MM-DD
        """
        if not self.settings['DEFAULT_REQUEST_HEADERS']['cookie']:
            raise ValueError("请先设置微博cookie")
            
        process = CrawlerProcess(self.settings)
        
        for user_id in celebrity_ids:
            # 爬取用户信息
            process.crawl(UserSpider, user_id=user_id)
            
            # 爬取用户微博
            process.crawl(TweetSpider, user_id=user_id, 
                        start_date=start_date, 
                        end_date=end_date)
            
            # 爬取评论
            process.crawl(CommentSpider, user_id=user_id)
        
        process.start() 