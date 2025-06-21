#!/usr/bin/env python
# encoding: utf-8

import json
from scrapy import Spider
from scrapy.http import Request
from spiders.common import parse_user_info


class UserSpider(Spider):
    """
    微博用户信息爬虫
    """
    name = "user"
    base_url = "https://weibo.cn"

    def start_requests(self):
        """
        爬虫入口
        """
        print("UserSpider start_requests called")
        # 这里user_ids可替换成实际待采集的数据
        user_ids = ['6290114447']
        print("user_ids:", user_ids)
        urls = [f'https://weibo.com/ajax/profile/info?uid={user_id}' for user_id in user_ids]
        for url in urls:
            print("yield url:", url)
            yield Request(url, callback=self.parse)

    def parse(self, response, **kwargs):
        """
        网页解析
        """
        print("UserSpider parse called, url:", response.url)
        try:
            data = json.loads(response.text)
            item = parse_user_info(data['data']['user'])
            url = f"https://weibo.com/ajax/profile/detail?uid={item['_id']}"
            print("yield item (basic):", item)
            yield Request(url, callback=self.parse_detail, meta={'item': item})
        except Exception as e:
            print("Error in parse:", e)

    @staticmethod
    def parse_detail(response):
        """
        解析详细数据
        """
        item = response.meta['item']
        try:
            data = json.loads(response.text)['data']
            item['birthday'] = data.get('birthday', '')
            if 'created_at' not in item:
                item['created_at'] = data.get('created_at', '')
            item['desc_text'] = data.get('desc_text', '')
            item['ip_location'] = data.get('ip_location', '')
            item['sunshine_credit'] = data.get('sunshine_credit', {}).get('level', '')
            item['label_desc'] = [label['name'] for label in data.get('label_desc', [])]
            if 'company' in data:
                item['company'] = data['company']
            if 'education' in data:
                item['education'] = data['education']
            print("yield item (detail):", item)
            yield item
        except Exception as e:
            print("Error in parse_detail:", e)
            print("item so far:", item)
