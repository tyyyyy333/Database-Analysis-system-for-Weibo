import json
import scrapy
from ..items import TweetItem
from .base import BaseSpider

class TweetSpider(BaseSpider):
    name = 'tweet'
    
    def start_requests(self):
        url = f'https://weibo.com/ajax/statuses/mymblog?uid={self.user_id}&page=1'
        yield scrapy.Request(url=url, callback=self.parse)
        
    def parse(self, response):
        data = json.loads(response.text)
        if data.get('ok') == 1:
            tweets = data['data']['list']
            for tweet in tweets:
                if not self.check_date(tweet['created_at']):
                    continue
                    
                item = TweetItem()
                item['_id'] = tweet['id']
                item['user_id'] = self.user_id
                item['content'] = tweet['text_raw']
                item['created_at'] = self.parse_time(tweet['created_at'])
                item['retweet_count'] = tweet['reposts_count']
                item['comment_count'] = tweet['comments_count']
                item['like_count'] = tweet['attitudes_count']
                item['read_count'] = tweet.get('reads_count', 0)
                item['source'] = tweet.get('source', '')
                item['is_long'] = tweet.get('isLongText', False)
                
                # 处理图片
                pictures = []
                if 'pic_ids' in tweet:
                    for pic_id in tweet['pic_ids']:
                        pictures.append(f'https://wx1.sinaimg.cn/orj960/{pic_id}')
                item['pictures'] = pictures
                
                # 处理视频
                if 'page_info' in tweet and tweet['page_info'].get('type') == 'video':
                    item['video_url'] = tweet['page_info']['media_info']['stream_url']
                else:
                    item['video_url'] = ''
                    
                yield item
                
            # 处理下一页
            if data['data']['list'] and data['data']['page'] < data['data']['total']:
                next_page = data['data']['page'] + 1
                next_url = f'https://weibo.com/ajax/statuses/mymblog?uid={self.user_id}&page={next_page}'
                yield scrapy.Request(url=next_url, callback=self.parse) 