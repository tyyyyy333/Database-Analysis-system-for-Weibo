import os
import json
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from .weibo_spider.spiders.user import UserSpider
from .weibo_spider.spiders.tweet import TweetSpider
from .weibo_spider.spiders.comment import CommentSpider
import re
import requests
from urllib.parse import urlparse

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
        self.on_complete = None  # 添加完成回调
        
    def set_cookie(self, cookie):
        """设置微博cookie"""
        self.settings['DEFAULT_REQUEST_HEADERS']['cookie'] = cookie
        
    def set_complete_callback(self, callback):
        """设置爬虫完成回调"""
        self.on_complete = callback
        
    def run_spider(self, celebrity_info, start_date=None, end_date=None):
        """
        运行爬虫
        :param celebrity_info: 包含明星信息的字典 {'name': '明星名', 'url': '微博主页URL'}
        :param start_date: 开始日期，格式：YYYY-MM-DD
        :param end_date: 结束日期，格式：YYYY-MM-DD
        """
        if not self.settings['DEFAULT_REQUEST_HEADERS']['cookie']:
            raise ValueError("请先设置微博cookie")
            
        try:
            # 从URL中提取用户ID
            user_id = self.extract_user_id_from_url(celebrity_info['url'])
            
            # 创建爬虫进程
            process = CrawlerProcess(self.settings)
            
            # 爬取用户信息
            process.crawl(
                UserSpider, 
                user_id=user_id,
                celebrity_name=celebrity_info['name']  # 传递明星姓名
            )
            
            # 爬取用户微博
            process.crawl(
                TweetSpider, 
                user_id=user_id,
                celebrity_name=celebrity_info['name'],
                start_date=start_date, 
                end_date=end_date
            )
            
            # 爬取评论
            process.crawl(CommentSpider, user_id=user_id)
            
            # 启动爬虫
            process.start()
            
            # 爬虫完成后触发回调
            if self.on_complete:
                self.on_complete(celebrity_info)
                
            return {'status': 'success', 'message': '爬虫运行完成'}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}