from scrapy import Request
from datetime import datetime
from ..items import UserItem
from .base import BaseSpider

class UserSpider(BaseSpider):
    name = 'user'
    
    def __init__(self, user_id=None, celebrity_name=None, *args, **kwargs):
        super(UserSpider, self).__init__(*args, **kwargs)
        self.user_id = user_id
        self.celebrity_name = celebrity_name
        self.start_urls = [f'https://weibo.com/ajax/profile/info?uid={user_id}']
        
    def parse(self, response):
        try:
            data = response.json()
            if data.get('ok') == 1 and data.get('data'):
                user_info = data['data']['user']
                item = UserItem()
                item['user_id'] = user_info.get('id')
                item['nickname'] = user_info.get('screen_name')
                item['followers_count'] = user_info.get('followers_count', 0)
                item['friends_count'] = user_info.get('friends_count', 0)
                item['statuses_count'] = user_info.get('statuses_count', 0)
                item['verified'] = user_info.get('verified', False)
                item['verified_reason'] = user_info.get('verified_reason', '')
                item['description'] = user_info.get('description', '')
                item['gender'] = user_info.get('gender', '')
                item['location'] = user_info.get('location', '')
                item['created_at'] = datetime.now()
                yield item
            else:
                self.logger.error(f'获取用户信息失败: {data}')
        except Exception as e:
            self.logger.error(f'解析用户信息失败: {str(e)}') 