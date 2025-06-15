import json
import scrapy
from ..items import CommentItem
from .base import BaseSpider
from scrapy.exceptions import IgnoreRequest
import logging

class CommentSpider(BaseSpider):
    name = 'comment'
    
    def start_requests(self):
        # 首先获取用户的微博列表
        url = f'https://weibo.com/ajax/statuses/mymblog?uid={self.user_id}&page=1'
        yield scrapy.Request(
            url=url,
            callback=self.parse_tweets,
            errback=self.errback_httpbin,
            dont_filter=True
        )
        
    def parse_tweets(self, response):
        try:
            data = json.loads(response.text)
            if data.get('ok') == 1:
                tweets = data['data']['list']
                for tweet in tweets:
                    if not self.check_date(tweet['created_at']):
                        continue
                        
                    # 获取每条微博的评论
                    tweet_id = tweet['id']
                    comment_url = f'https://weibo.com/ajax/comments/show?id={tweet_id}&page=1'
                    yield scrapy.Request(
                        url=comment_url,
                        callback=self.parse_comments,
                        errback=self.errback_httpbin,
                        meta={'tweet_id': tweet_id, 'retry_times': 0},
                        dont_filter=True
                    )
                    
                # 处理下一页微博
                if data['data']['list'] and data['data']['page'] < data['data']['total']:
                    next_page = data['data']['page'] + 1
                    next_url = f'https://weibo.com/ajax/statuses/mymblog?uid={self.user_id}&page={next_page}'
                    yield scrapy.Request(
                        url=next_url,
                        callback=self.parse_tweets,
                        errback=self.errback_httpbin,
                        dont_filter=True
                    )
            else:
                self.logger.error(f"Failed to get tweets: {data.get('msg', 'Unknown error')}")
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in parse_tweets: {str(e)}")
            self.logger.debug(f"Response text: {response.text[:200]}")  # 只记录前200个字符
                
    def parse_comments(self, response):
        try:
            data = json.loads(response.text)
            if data.get('ok') == 1:
                comments = data['data']
                for comment in comments:
                    item = CommentItem()
                    item['_id'] = comment['id']
                    item['tweet_id'] = comment['mid']
                    item['user_id'] = comment['user']['id']
                    item['content'] = comment['text_raw']
                    item['created_at'] = self.parse_time(comment['created_at'])
                    item['like_count'] = comment['like_counts']
                    yield item
                    
                # 处理下一页评论
                if data['data'] and data['page'] < data['total']:
                    next_page = data['page'] + 1
                    tweet_id = data['data'][0]['mid']
                    next_url = f'https://weibo.com/ajax/comments/show?id={tweet_id}&page={next_page}'
                    yield scrapy.Request(
                        url=next_url,
                        callback=self.parse_comments,
                        errback=self.errback_httpbin,
                        meta={'tweet_id': tweet_id, 'retry_times': 0},
                        dont_filter=True
                    )
            else:
                self.logger.error(f"Failed to get comments: {data.get('msg', 'Unknown error')}")
                # 如果是权限问题，记录并跳过
                if data.get('msg') == '没有权限':
                    self.logger.warning(f"No permission to access comments for tweet {response.meta.get('tweet_id')}")
                    return
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in parse_comments: {str(e)}")
            self.logger.debug(f"Response text: {response.text[:200]}")  # 只记录前200个字符
            
            # 重试逻辑
            retry_times = response.meta.get('retry_times', 0)
            if retry_times < 3:  # 最多重试3次
                retry_times += 1
                self.logger.info(f"Retrying comment request (attempt {retry_times})")
                yield scrapy.Request(
                    url=response.url,
                    callback=self.parse_comments,
                    errback=self.errback_httpbin,
                    meta={'tweet_id': response.meta.get('tweet_id'), 'retry_times': retry_times},
                    dont_filter=True
                )
            else:
                self.logger.error(f"Max retries reached for URL: {response.url}")
    
    def errback_httpbin(self, failure):
        self.logger.error(f"Request failed: {failure.value}")
        # 如果是网络错误，可以在这里添加重试逻辑
        if hasattr(failure.value, 'response'):
            self.logger.error(f"Response status: {failure.value.response.status}")
            self.logger.error(f"Response headers: {failure.value.response.headers}")
            self.logger.error(f"Response body: {failure.value.response.text[:200]}")  # 只记录前200个字符 