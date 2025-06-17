import json
import scrapy
from ..items import CommentItem
from .base import BaseSpider
from scrapy.exceptions import IgnoreRequest
import logging
from datetime import datetime
from scrapy import Request

class CommentSpider(BaseSpider):
    name = 'comment'
    allowed_domains = ['weibo.com']
    
    def __init__(self, user_id=None, celebrity_name=None, *args, **kwargs):
        super(CommentSpider, self).__init__(*args, **kwargs)
        self.user_id = user_id
        self.celebrity_name = celebrity_name
        self.start_urls = [f'https://weibo.com/ajax/statuses/mymblog?uid={user_id}&page=1']
        
    def parse(self, response):
        try:
            data = response.json()
            if data.get('ok') == 1 and data.get('data'):
                tweets = data['data']['list']
                for tweet in tweets:
                    tweet_id = tweet['id']
                    comment_url = f'https://weibo.com/ajax/comments/show?id={tweet_id}&page=1'
                    yield Request(url=comment_url, callback=self.parse_comments)
                    
                # 处理分页
                if data['data'].get('since_id'):
                    next_page = f'https://weibo.com/ajax/statuses/mymblog?uid={self.user_id}&page=1&since_id={data["data"]["since_id"]}'
                    yield Request(url=next_page, callback=self.parse)
                    
        except Exception as e:
            self.logger.error(f'获取微博列表失败: {str(e)}')
            
    def parse_comments(self, response):
        try:
            data = response.json()
            if data.get('ok') == 1 and data.get('data'):
                comments = data['data']
                for comment in comments:
                    item = CommentItem()
                    item['comment_id'] = comment['id']
                    item['tweet_id'] = comment['mid']
                    item['user_id'] = comment['user']['id']
                    item['nickname'] = comment['user']['screen_name']
                    item['content'] = comment['text_raw']
                    item['created_at'] = datetime.strptime(comment['created_at'], '%a %b %d %H:%M:%S %z %Y')
                    item['likes_count'] = comment.get('like_counts', 0)
                    item['source'] = comment.get('source', '')
                    yield item
                    
                # 处理评论分页
                if data.get('max_id'):
                    next_page = f'https://weibo.com/ajax/comments/show?id={item["tweet_id"]}&page=1&max_id={data["max_id"]}'
                    yield Request(url=next_page, callback=self.parse_comments)
                    
        except Exception as e:
            self.logger.error(f'解析评论失败: {str(e)}')
            
    def _extract_number(self, text):
        """从文本中提取数字"""
        if not text:
            return 0
        try:
            return int(''.join(filter(str.isdigit, text)))
        except:
            return 0

    def errback_httpbin(self, failure):
        self.logger.error(f"Request failed: {failure.value}")
        # 如果是网络错误，可以在这里添加重试逻辑
        if hasattr(failure.value, 'response'):
            self.logger.error(f"Response status: {failure.value.response.status}")
            self.logger.error(f"Response headers: {failure.value.response.headers}")
            self.logger.error(f"Response body: {failure.value.response.text[:200]}")  # 只记录前200个字符 