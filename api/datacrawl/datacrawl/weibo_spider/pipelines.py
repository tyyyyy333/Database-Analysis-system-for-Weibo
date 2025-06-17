from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from api.database.models import WeiboUser, Post, Comment, Celebrity
import json
from api.datacleaner.cleaner import DataCleaner
import time

class WeiboPipeline:
    def __init__(self, db_config):
        self.db_config = db_config
        self.cleaner = DataCleaner(batch_size=32)
        self.user_items = []
        self.tweet_items = []
        self.comment_items = []
        self.batch_size = 100
        self.max_retries = 3
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.get('DATABASE'))
        
    def open_spider(self, spider):
        db_url = f"sqlite:///{self.db_config['database']}"
        self.engine = create_engine(db_url, connect_args={'check_same_thread': False})
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
    def close_spider(self, spider):
        try:
            # 处理剩余的items
            self._process_user_items()
            self._process_tweet_items()
            self._process_comment_items()
        except Exception as e:
            spider.logger.error(f'关闭爬虫时处理数据失败: {str(e)}')
            raise
        finally:
            self.session.close()
        
    def process_item(self, item, spider):
        try:
            if spider.name == 'user':
                self.user_items.append(item)
                if len(self.user_items) >= self.batch_size:
                    self._process_user_items()
                    
            elif spider.name == 'tweet':
                self.tweet_items.append(item)
                if len(self.tweet_items) >= self.batch_size:
                    self._process_tweet_items()
                    
            elif spider.name == 'comment':
                self.comment_items.append(item)
                if len(self.comment_items) >= self.batch_size:
                    self._process_comment_items()
                    
        except Exception as e:
            spider.logger.error(f'处理数据失败: {str(e)}')
            raise
            
        return item
        
    def _process_user_items(self):
        if not self.user_items:
            return
            
        for retry in range(self.max_retries):
            try:
                # 批量清洗用户数据
                cleaned_items = self.cleaner.clean_user_data_batch(self.user_items)
                
                # 批量创建微博用户对象
                weibo_users = [
                    WeiboUser(
                        weibo_id=item['weibo_id'],
                        nickname=item['nickname'],
                        verified=item['verified'],
                        verified_type=item.get('verified_type'),
                        followers_count=item['followers_count'],
                        following_count=item['following_count'],
                        statuses_count=item['statuses_count'],
                        gender=item.get('gender'),
                        location=item.get('location'),
                        created_at=item['created_at']
                    )
                    for item in cleaned_items
                ]
                
                # 使用事务
                with self.session.begin():
                    self.session.bulk_merge_mappings(WeiboUser, [user.__dict__ for user in weibo_users])
                
                self.user_items = []
                break
                
            except Exception as e:
                if retry == self.max_retries - 1:
                    raise
                self.session.rollback()
                time.sleep(1)  # 等待1秒后重试
            
    def _process_tweet_items(self):
        if not self.tweet_items:
            return
            
        for retry in range(self.max_retries):
            try:
                # 批量清洗微博数据
                cleaned_items = self.cleaner.clean_post_data_batch(self.tweet_items)
                
                # 批量创建微博对象
                posts = []
                for item in cleaned_items:
                    posts.append(Post(
                        post_id=item['post_id'],
                        celebrity_id=item['celebrity_id'],
                        content=item['content'],
                        created_at=item['created_at'],
                        reposts_count=item['reposts_count'],
                        comments_count=item['comments_count'],
                        likes=item['likes'],
                        is_deleted=item.get('is_deleted', 0),
                        sentiment_score=item.get('sentiment_score', 0.0)
                    ))
                
                # 使用事务
                with self.session.begin():
                    self.session.bulk_merge_mappings(Post, [post.__dict__ for post in posts])
                
                self.tweet_items = []
                break
                
            except Exception as e:
                if retry == self.max_retries - 1:
                    raise
                self.session.rollback()
                time.sleep(1)  # 等待1秒后重试
            
    def _process_comment_items(self):
        if not self.comment_items:
            return
            
        for retry in range(self.max_retries):
            try:
                # 批量清洗评论数据
                cleaned_items = self.cleaner.clean_comment_data_batch(self.comment_items)
                
                # 批量创建评论对象
                comments = [
                    Comment(
                        comment_id=item['comment_id'],
                        post_id=item['post_id'],
                        content=item['content'],
                        created_at=item['created_at'],
                        parent_id=item.get('parent_id')
                    )
                    for item in cleaned_items
                ]
                
                # 使用事务
                with self.session.begin():
                    self.session.bulk_merge_mappings(Comment, [comment.__dict__ for comment in comments])
                
                self.comment_items = []
                break
                
            except Exception as e:
                if retry == self.max_retries - 1:
                    raise
                self.session.rollback()
                time.sleep(1)  # 等待1秒后重试 