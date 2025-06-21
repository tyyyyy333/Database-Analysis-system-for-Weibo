import datetime
import json
import re

from scrapy import Spider
from scrapy.http import Request
from spiders.common import parse_tweet_info, parse_long_tweet

import pymysql
from pymysql.cursors import DictCursor


class TweetSpiderByUserID(Spider):
    """
    用户推文数据采集
    """
    name = "tweet_spider_by_user_id"

    def start_requests(self):
        """
        爬虫入口
        """
        print("tweet_by_user_id start_requests called")
        # 这里user_ids可替换成实际待采集的数据
        user_ids = ['6290114447']
        print("user_ids:", user_ids)
        # 这里的时间替换成实际需要的时间段，如果要采集用户全部推文 is_crawl_specific_time_span 设置为False
        is_crawl_specific_time_span = True
        
        # 设置时间范围：当前时间前30天到当前时间
        end_time = datetime.datetime.now()
        start_time = end_time - datetime.timedelta(days=30)
        
        print(f"爬取时间范围: {start_time.strftime('%Y-%m-%d')} 到 {end_time.strftime('%Y-%m-%d')}")
        
        for user_id in user_ids:
            url = f"https://weibo.com/ajax/statuses/searchProfile?uid={user_id}&page=1&hasori=1&hastext=1&haspic=1&hasvideo=1&hasmusic=1&hasret=1"
            print("yield url:", url)
            if not is_crawl_specific_time_span:
                # 在meta中传递user_id
                yield Request(url, callback=self.parse, meta={'user_id': user_id, 'page_num': 1})
            else:
                # 切分成10天进行
                tmp_start_time = start_time
                while tmp_start_time <= end_time:
                    tmp_end_time = tmp_start_time + datetime.timedelta(days=10)
                    tmp_end_time = min(tmp_end_time, end_time)
                    tmp_url = url + f'&starttime={int(tmp_start_time.timestamp())}&endtime={int(tmp_end_time.timestamp())}'
                    print("yield url (with time):", tmp_url)
                    # 在meta中传递user_id
                    yield Request(tmp_url, callback=self.parse, meta={'user_id': user_id, 'page_num': 1})
                    tmp_start_time = tmp_end_time + datetime.timedelta(days=1)

    def parse(self, response, **kwargs):
        """
        网页解析
        """
        print("DEBUG: parse called, url:", response.url, "status:", response.status)
        print("DEBUG: response.text (first 200):", response.text[:200])
        try:
            data = json.loads(response.text)
            tweets = data['data']['list']
            print("DEBUG: tweets count:", len(tweets))
            for tweet in tweets:
                item = parse_tweet_info(tweet)
                # 从meta中获取user_id并添加到item中
                item['user_id'] = response.meta['user_id']
                del item['user']
                print("DEBUG: yield item:", str(item)[:200])
                if item['isLongText']:
                    url = "https://weibo.com/ajax/statuses/longtext?id=" + item['mblogid']
                    # 在meta中传递user_id和item
                    yield Request(url, callback=parse_long_tweet, meta={'item': item, 'user_id': response.meta['user_id']})
                else:
                    # 输出包含user_id的item
                    yield item
            if tweets:
                user_id, page_num = response.meta['user_id'], response.meta['page_num']
                url = response.url.replace(f'page={page_num}', f'page={page_num + 1}')
                yield Request(url, callback=self.parse, meta={'user_id': user_id, 'page_num': page_num + 1})
        except Exception as e:
            print("DEBUG: Error in tweet_by_user_id parse:", e)
            print("DEBUG: response.text (full):", response.text)