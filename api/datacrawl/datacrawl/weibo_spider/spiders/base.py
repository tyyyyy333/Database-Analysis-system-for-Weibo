import scrapy
from datetime import datetime, timedelta
import json
import re

class BaseSpider(scrapy.Spider):
    def __init__(self, user_id=None, start_date=None, end_date=None, *args, **kwargs):
        super(BaseSpider, self).__init__(*args, **kwargs)
        self.user_id = user_id
        self.start_date = start_date
        self.end_date = end_date
        
    def parse_time(self, date_str):
        """解析微博时间字符串"""
        if re.match(r'\d{1,2}分钟前', date_str):
            minutes = re.match(r'(\d{1,2})分钟前', date_str).group(1)
            date = datetime.now() - timedelta(minutes=int(minutes))
        elif re.match(r'\d{1,2}小时前', date_str):
            hours = re.match(r'(\d{1,2})小时前', date_str).group(1)
            date = datetime.now() - timedelta(hours=int(hours))
        elif re.match(r'昨天', date_str):
            date = datetime.now() - timedelta(days=1)
        elif re.match(r'\d{1,2}天前', date_str):
            days = re.match(r'(\d{1,2})天前', date_str).group(1)
            date = datetime.now() - timedelta(days=int(days))
        else:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        return date.strftime('%Y-%m-%d %H:%M:%S')
        
    def check_date(self, date_str):
        """检查日期是否在指定范围内"""
        if not self.start_date and not self.end_date:
            return True
            
        date = datetime.strptime(self.parse_time(date_str), '%Y-%m-%d %H:%M:%S')
        
        if self.start_date and self.end_date:
            return self.start_date <= date <= self.end_date
        elif self.start_date:
            return date >= self.start_date
        elif self.end_date:
            return date <= self.end_date
            
        return True 