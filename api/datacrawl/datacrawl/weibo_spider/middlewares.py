import random
from scrapy import signals
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware

class IPProxyMiddleware:
    def __init__(self):
        self.proxy_list = [
            # 这里添加您的代理IP列表
            # 'http://ip:port',
            # 'http://username:password@ip:port',
        ]
        
    def process_request(self, request, spider):
        if self.proxy_list:
            proxy = random.choice(self.proxy_list)
            request.meta['proxy'] = proxy
            print(f"使用代理: {proxy}")
            
class UserAgentMiddleware:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        ]
        
        # 添加更多浏览器特征
        self.default_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }

    def process_request(self, request, spider):
        user_agent = random.choice(self.user_agents)
        request.headers['User-Agent'] = user_agent
        
        # 设置其他请求头
        for key, value in self.default_headers.items():
            if key not in request.headers:
                request.headers[key] = value
                
        # 添加Referer
        if 'weibo.com' in request.url:
            request.headers['Referer'] = 'https://weibo.com/'
            
        # 添加Origin
        if 'ajax' in request.url:
            request.headers['Origin'] = 'https://weibo.com'
            request.headers['X-Requested-With'] = 'XMLHttpRequest'

class ProxyMiddleware:
    def __init__(self, proxy_list):
        self.proxy_list = proxy_list

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.getlist('PROXY_LIST'))

    def process_request(self, request, spider):
        if self.proxy_list:
            proxy = random.choice(self.proxy_list)
            request.meta['proxy'] = proxy
            spider.logger.debug(f'Using proxy: {proxy}')

    def process_exception(self, request, exception, spider):
        # 如果代理请求失败，尝试使用其他代理
        if 'proxy' in request.meta:
            proxy = request.meta['proxy']
            if proxy in self.proxy_list:
                self.proxy_list.remove(proxy)
            if self.proxy_list:
                new_proxy = random.choice(self.proxy_list)
                request.meta['proxy'] = new_proxy
                spider.logger.debug(f'Switching to new proxy: {new_proxy}')
                return request 