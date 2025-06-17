import json
import scrapy
from ..items import TweetItem
from .base import BaseSpider
from datetime import datetime
from scrapy import Request

class TweetSpider(BaseSpider):
    name = 'tweet'
    allowed_domains = ['weibo.com']
    
    def __init__(self, user_id=None, celebrity_name=None, start_date=None, end_date=None, *args, **kwargs):
        super(TweetSpider, self).__init__(*args, **kwargs)
        self.user_id = user_id
        self.celebrity_name = celebrity_name
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
        self.start_urls = [f'https://weibo.com/ajax/statuses/mymblog?uid={user_id}&page=1']
        
    def parse(self, response):
        try:
            data = response.json()
            if data.get('ok') == 1 and data.get('data'):
                tweets = data['data']['list']
                for tweet in tweets:
                    created_at = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S %z %Y')
                    
                    # 检查日期范围
                    if self.start_date and created_at < self.start_date:
                        continue
                    if self.end_date and created_at > self.end_date:
                        continue
                        
                    item = TweetItem()
                    item['tweet_id'] = tweet['id']
                    item['user_id'] = self.user_id
                    item['celebrity_name'] = self.celebrity_name
                    item['content'] = tweet['text_raw']
                    item['reposts_count'] = tweet.get('reposts_count', 0)
                    item['comments_count'] = tweet.get('comments_count', 0)
                    item['attitudes_count'] = tweet.get('attitudes_count', 0)
                    item['created_at'] = created_at
                    item['source'] = tweet.get('source', '')
                    item['is_retweet'] = tweet.get('retweeted_status') is not None
                    item['pics'] = [pic['large']['url'] for pic in tweet.get('pics', [])]
                    item['crawl_time'] = datetime.now()
                    yield item
                    
                # 处理分页
                if data['data'].get('since_id'):
                    next_page = f'https://weibo.com/ajax/statuses/mymblog?uid={self.user_id}&page=1&since_id={data["data"]["since_id"]}'
                    yield Request(url=next_page, callback=self.parse)
                    
        except Exception as e:
            self.logger.error(f'解析微博失败: {str(e)}')
            
    def _extract_number(self, text):
        """从文本中提取数字"""
        if not text:
            return 0
        try:
            return int(''.join(filter(str.isdigit, text)))
        except:
            return 0 