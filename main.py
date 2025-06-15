from config.database import DB_CONFIG
from datacrawl import WeiboSpiderRunner
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from models import Base

def init_database():
    """初始化数据库"""
    db_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

def run_weibo_crawler(celebrity_ids, cookie, start_date=None, end_date=None):
    """
    运行微博爬虫
    :param celebrity_ids: 明星微博ID列表
    :param cookie: 微博cookie
    :param start_date: 开始日期，格式：'YYYY-MM-DD'
    :param end_date: 结束日期，格式：'YYYY-MM-DD'
    """
    # 初始化数据库
    init_database()
    
    # 创建爬虫实例
    spider_runner = WeiboSpiderRunner(DB_CONFIG)
    
    # 设置cookie
    spider_runner.set_cookie(cookie)
    
    # 如果没有指定日期，默认使用最近一周（从当前日期往前推7天）
    if not start_date or not end_date:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
    
    print(f"开始爬取从 {start_date} 到 {end_date} 的数据")
    
    # 运行爬虫
    spider_runner.run_spider(
        celebrity_ids=celebrity_ids,
        start_date=start_date,
        end_date=end_date
    )

if __name__ == "__main__":
    # 示例明星用户ID列表
    CELEBRITY_IDS = [
        '5598574734',  # 示例ID
    ]
    
    # 设置时间范围为最近一周（从当前日期往前推7天）
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    # 注释掉全局变量，避免干扰
    # START_DATE = '2025-06-06'
    # END_DATE = '2025-06-13'
    
    # 这里需要填入您的微博cookie
    COOKIE = 'SCF=AoHgunIyEQU-9G7wGnZPgq6E8bWLL6QmweB6bOkL8mlCGetok_Ho9vedMnwxAPl_39VJCoQ2Zx5UVp2fZ2QOteU.; SUB=_2A25FTVDRDeRhGeBP6VoR9irOzD-IHXVmI-wZrDV8PUNbmtAbLWHxkW9NRWat8Ct3B2Lr8HL8DbUhECwSZlo5_BU8; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWMBRXAjSepCmsCGYHvg84W5JpX5KzhUgL.Foqpeon7SoBES0e2dJLoI02LxKqL1heLBoeLxKBLB.BLBK5LxK-L1K-LBKqLxKqL1h.L12BLxKqL1h5LB-8kdN9a; ALF=02_1752214913; ariaDefaultTheme=default; ariaFixed=true; ariaReadtype=1; ariaMouseten=null; ariaStatus=false; XSRF-TOKEN=3Rg23Y8Fh96b5dBvS50h3FEV; _s_tentry=weibo.com; Apache=9111354679924.004.1749880808947; SINAGLOBAL=9111354679924.004.1749880808947; ULV=1749880808953:1:1:1:9111354679924.004.1749880808947:; WBPSESS=g82Sj9YE-TKAkLUPlqSBQ-1W98F1zrWmyy4Oakz-5yZ6pLe6xcr8AgT-mFuQOJkTqr1wVjPTtZMtXlpLO1l9lXBHSqlJy7KuPzA7TWVmemUTjRER5w9i3NsvC2gLJd5ZUO6enbLimTA8KlGdp9HTNg=='
    
    run_weibo_crawler(
        celebrity_ids=CELEBRITY_IDS, 
        cookie=COOKIE,
        start_date=start_date,
        end_date=end_date
    ) 