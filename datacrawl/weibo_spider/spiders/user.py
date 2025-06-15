import json
import scrapy
from ..items import UserItem
from .base import BaseSpider

class UserSpider(BaseSpider):
    name = 'user'
    
    def start_requests(self):
        url = f'https://weibo.com/ajax/profile/info?uid={self.user_id}'
        yield scrapy.Request(url=url, callback=self.parse)
        
    def parse(self, response):
        data = json.loads(response.text)
        if data.get('ok') == 1:
            user_info = data['data']['user']
            item = UserItem()
            item['_id'] = user_info['id']
            item['nick_name'] = user_info['screen_name']
            item['verified'] = user_info['verified']
            item['verified_type'] = user_info.get('verified_type', -1)
            item['followers_count'] = user_info['followers_count']
            item['following_count'] = user_info['friends_count']
            item['statuses_count'] = user_info['statuses_count']
            item['gender'] = user_info.get('gender', '')
            item['location'] = user_info.get('location', '')
            yield item 