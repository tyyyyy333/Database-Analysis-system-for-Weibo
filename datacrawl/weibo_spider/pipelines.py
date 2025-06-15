from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from models import User, Post, Comment
import json

class WeiboPipeline:
    def __init__(self, db_config):
        self.db_config = db_config
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.get('DATABASE'))
        
    def open_spider(self, spider):
        db_url = f"mysql+pymysql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        self.engine = create_engine(db_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
    def close_spider(self, spider):
        self.session.close()
        
    def process_item(self, item, spider):
        try:
            if spider.name == 'user':
                user = User(
                    weibo_id=item['_id'],
                    nickname=item['nick_name'],
                    verified=item['verified'],
                    followers_count=item['followers_count'],
                    following_count=item['following_count'],
                    posts_count=item['statuses_count'],
                    updated_at=datetime.now()
                )
                self.session.merge(user)
                
            elif spider.name == 'tweet':
                post = Post(
                    weibo_id=item['_id'],
                    user_id=item['user_id'],
                    content=item['content'],
                    created_at=item['created_at'],
                    reposts_count=item['retweet_count'],
                    comments_count=item['comment_count'],
                    attitudes_count=item['like_count'],
                    read_count=item.get('read_count', 0),
                    source=item.get('source', ''),
                    pictures=json.dumps(item.get('pictures', []), ensure_ascii=False),
                    video_url=item.get('video_url', '')
                )
                self.session.merge(post)
                
            elif spider.name == 'comment':
                comment = Comment(
                    weibo_id=item['_id'],
                    post_id=item['tweet_id'],
                    user_id=item['user_id'],
                    content=item['content'],
                    created_at=item['created_at'],
                    like_count=item['like_count']
                )
                self.session.merge(comment)
                
            self.session.commit()
            
        except Exception as e:
            self.session.rollback()
            raise e
            
        return item 