#!/usr/bin/env python
# encoding: utf-8

import datetime
import json
import re
from scrapy import Spider, Request
from spiders.common import parse_tweet_info, parse_long_tweet

try:
    name_id_map
except NameError:
    name_id_map = {"单依纯": "6290114447"}

class TweetSpiderByKeyword(Spider):
    """
    关键词搜索采集
    """
    name = "tweet_spider_by_keyword"
    base_url = "https://s.weibo.com/"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 记录每个关键词已采集的推文数量
        self.keyword_counts = {}
        # 设置每个关键词的最大采集数量
        self.max_per_keyword = 500

    def start_requests(self):
        """
        爬虫入口
        """
        # 这里keywords可替换成实际待采集的数据
        keywords = ['单依纯']
        # 这里的时间可替换成实际需要的时间段
        start_time = datetime.datetime(year=2025, month=6, day=14, hour=0)
        end_time = datetime.datetime(year=2025, month=6, day=15, hour=23)
        # 是否按照小时进行切分，数据量更大; 对于非热门关键词**不需要**按照小时切分
        is_split_by_hour = True
        for keyword in keywords:
            keyword_id = name_id_map.get(keyword, '')
            # 初始化关键词计数
            self.keyword_counts[keyword] = 0
            if not is_split_by_hour:
                _start_time = start_time.strftime("%Y-%m-%d-%H")
                _end_time = end_time.strftime("%Y-%m-%d-%H")
                url = f"https://s.weibo.com/weibo?q={keyword}&timescope=custom%3A{_start_time}%3A{_end_time}&page=1"
                yield Request(url, callback=self.parse, meta={'keyword': keyword, 'keyword_id': keyword_id})
            else:
                time_cur = start_time
                while time_cur < end_time:
                    _start_time = time_cur.strftime("%Y-%m-%d-%H")
                    _end_time = (time_cur + datetime.timedelta(hours=1)).strftime("%Y-%m-%d-%H")
                    url = f"https://s.weibo.com/weibo?q={keyword}&timescope=custom%3A{_start_time}%3A{_end_time}&page=1"
                    yield Request(url, callback=self.parse, meta={'keyword': keyword, 'keyword_id': keyword_id})
                    time_cur = time_cur + datetime.timedelta(hours=1)

    def parse(self, response, **kwargs):
        """
        网页解析
        """
        keyword = response.meta['keyword']
        # 检查是否已达到最大数量
        if self.keyword_counts[keyword] >= self.max_per_keyword:
            self.logger.info(f"关键词 '{keyword}' 已达到最大采集数量 {self.max_per_keyword}，停止爬取")
            return
            
        html = response.text
        if '<p>抱歉，未找到相关结果。</p>' in html:
            self.logger.info(f'no search result. url: {response.url}')
            return
        tweets_infos = re.findall('<div class="from"\s+>(.*?)</div>', html, re.DOTALL)
        for tweets_info in tweets_infos:
            tweet_ids = re.findall(r'weibo\.com/\d+/(.+?)\?refer_flag=1001030103_" ', tweets_info)
            for tweet_id in tweet_ids:
                # 再次检查是否已达到最大数量
                if self.keyword_counts[keyword] >= self.max_per_keyword:
                    self.logger.info(f"关键词 '{keyword}' 已达到最大采集数量 {self.max_per_keyword}，停止爬取")
                    return
                    
                url = f"https://weibo.com/ajax/statuses/show?id={tweet_id}"
                yield Request(url, callback=self.parse_tweet, meta=response.meta, priority=10)
        next_page = re.search('<a href="(.*?)" class="next">下一页</a>', html)
        if next_page:
            url = "https://s.weibo.com" + next_page.group(1)
            yield Request(url, callback=self.parse, meta=response.meta)

    def parse_tweet(self, response):
        """
        解析推文
        """
        keyword = response.meta['keyword']
        # 检查是否已达到最大数量
        if self.keyword_counts[keyword] >= self.max_per_keyword:
            self.logger.info(f"关键词 '{keyword}' 已达到最大采集数量 {self.max_per_keyword}，停止爬取")
            return
            
        data = json.loads(response.text)
        item = parse_tweet_info(data)
        item['keyword'] = keyword
        item['keyword_id'] = response.meta.get('keyword_id', '')
        
        # 增加计数
        self.keyword_counts[keyword] += 1
        self.logger.info(f"关键词 '{keyword}' 已采集 {self.keyword_counts[keyword]}/{self.max_per_keyword} 条数据")
        
        if item['isLongText']:
            url = "https://weibo.com/ajax/statuses/longtext?id=" + item['mblogid']
            yield Request(url, callback=parse_long_tweet, meta={'item': item}, priority=20)
        else:
            yield item    
