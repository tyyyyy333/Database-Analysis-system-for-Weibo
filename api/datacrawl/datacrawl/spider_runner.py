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
        # 设置Scrapy项目设置模块
        os.environ['SCRAPY_SETTINGS_MODULE'] = 'api.datacrawl.datacrawl.weibo_spider.settings'
        
        # 获取Scrapy项目设置
        self.settings = get_project_settings()
        
        # 更新数据库配置
        self.settings.set('DATABASE', db_config)
        
        # 设置爬虫基本配置
        self.settings.update({
            'BOT_NAME': 'weibo_spider',
            'SPIDER_MODULES': ['api.datacrawl.datacrawl.weibo_spider.spiders'],
            'NEWSPIDER_MODULE': 'api.datacrawl.datacrawl.weibo_spider.spiders',
            'ROBOTSTXT_OBEY': False,
            'COOKIES_ENABLED': True,
            'CONCURRENT_REQUESTS': 16,
            'DOWNLOAD_DELAY': 1,
            'DOWNLOADER_MIDDLEWARES': {
                'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
                'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': None,
                'datacrawl.weibo_spider.middlewares.IPProxyMiddleware': 100,
                'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 101,
            },
            'ITEM_PIPELINES': {
                'datacrawl.weibo_spider.pipelines.JsonWriterPipeline': 300,
            },
            'DEFAULT_REQUEST_HEADERS': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) Gecko/20100101 Firefox/61.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
            }
        })
        self.on_complete = None  # 添加完成回调
        
    def set_cookie(self, cookie):
        """设置微博cookie"""
        self.settings['DEFAULT_REQUEST_HEADERS']['Cookie'] = cookie
        
    def set_complete_callback(self, callback):
        """设置爬虫完成回调"""
        self.on_complete = callback
        
    def extract_user_id_from_url(self, url):
        """
        从微博URL中提取用户ID
        :param url: 微博用户主页URL
        :return: 用户ID
        """
        try:
            # 处理URL格式：https://weibo.com/u/1234567890
            if '/u/' in url:
                user_id = url.split('/u/')[-1].split('?')[0]
                return user_id
                
            # 处理URL格式：https://weibo.com/n/用户名
            elif '/n/' in url:
                # 需要发送请求获取用户ID
                response = requests.get(url, headers=self.settings['DEFAULT_REQUEST_HEADERS'])
                if response.status_code == 200:
                    # 从响应中提取用户ID
                    match = re.search(r'CONFIG\[\'oid\'\]=\'(\d+)\'', response.text)
                    if match:
                        return match.group(1)
                        
            # 如果URL直接是数字ID
            elif url.isdigit():
                return url
                
            raise ValueError(f"无法从URL中提取用户ID: {url}")
            
        except Exception as e:
            raise ValueError(f"提取用户ID失败: {str(e)}")
        
    def run_spider(self, celebrity_info, start_date=None, end_date=None):
        """
        运行爬虫
        :param celebrity_info: 包含明星信息的字典 {'name': '明星名', 'url': '微博主页URL'}
        :param start_date: 开始日期，格式：YYYY-MM-DD
        :param end_date: 结束日期，格式：YYYY-MM-DD
        """
        if not self.settings['DEFAULT_REQUEST_HEADERS'].get('Cookie'):
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
                celebrity_name=celebrity_info['name']
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