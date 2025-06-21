from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Report(db.Model):
    __tablename__ = 'report'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, primary_key=True)
    star_id = db.Column(db.String(255), primary_key=True, comment='明星ID')
    create_date = db.Column(db.DateTime, default=datetime.utcnow, comment='记录创建时间')
    follower_count = db.Column(db.Integer, comment='粉丝数量')
    following_count = db.Column(db.Integer, comment='关注数量')
    hot_weibo = db.Column(db.Text, comment='热门微博内容')
    comments = db.Column(db.JSON, comment='热门评论列表')
    bad_content = db.Column(db.JSON, comment='恶意事件微博ID列表')
    
    user = db.relationship('User', backref=db.backref('reports', lazy=True))
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'star_id': self.star_id,
            'create_date': self.create_date.isoformat() if self.create_date else None,
            'follower_count': self.follower_count,
            'following_count': self.following_count,
            'hot_weibo': self.hot_weibo,
            'comments': self.comments,
            'bad_content': self.bad_content
        }

class UserStar(db.Model):
    __tablename__ = 'user_stars'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    star_id = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('stars', lazy=True, cascade="all, delete-orphan"))
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'star_id', name='unique_user_star'),
    )

class WeiboUser(db.Model):
    __tablename__ = 'weibo_user'
    id = db.Column(db.String(50), primary_key=True)
    nick_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    follower_count = db.Column(db.Integer, default=0)
    friends_count = db.Column(db.Integer, default=0)
    gender = db.Column(db.String(2), default='未知')
    location = db.Column(db.String(100))
    profession = db.Column(db.String(50))
    # created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 

class UserPost(db.Model):
    __tablename__ = 'user_post'
    id = db.Column(db.String(255), primary_key=True)
    mblogid = db.Column(db.String(255), unique=True)
    created_at = db.Column(db.DateTime)
    location = db.Column(db.String(255))
    reposts_count = db.Column(db.Integer)
    comments_count = db.Column(db.Integer)
    attitudes_count = db.Column(db.Integer)
    content = db.Column(db.Text)
    user_id = db.Column(db.String(255))
    keyword_id = db.Column(db.String(255))

class WeiboFans(db.Model):
    __tablename__ = 'weibo_fans'
    fan_id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    following_count = db.Column(db.Integer, default=0)
    followers_count = db.Column(db.Integer, default=0)
    gender = db.Column(db.String(10))
    region = db.Column(db.String(100))
    follower_id = db.Column(db.String(255), nullable=False, index=True)

class WeiboComments(db.Model):
    __tablename__ = 'weibo_comments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, nullable=False)
    comment_time = db.Column(db.DateTime, nullable=False)
    gender = db.Column(db.String(10))
    content = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    replies = db.Column(db.Integer, default=0)
    fan_badge = db.Column(db.String(50))
    comment_ip = db.Column(db.String(100))
    celebrity_id = db.Column(db.BigInteger, nullable=False)
    mblog_id = db.Column(db.String(255), nullable=False)

class KeywordPost(db.Model):
    __tablename__ = 'keyword_post'
    id = db.Column(db.String(255), primary_key=True)
    mblogid = db.Column(db.String(255), unique=True)
    created_at = db.Column(db.DateTime)
    location = db.Column(db.String(255))
    reposts_count = db.Column(db.Integer)
    comments_count = db.Column(db.Integer)
    attitudes_count = db.Column(db.Integer)
    content = db.Column(db.Text)
    user_id = db.Column(db.String(255))
    keyword = db.Column(db.String(255))
    keyword_id = db.Column(db.String(255))
    sentiment_score = db.Column(db.Float) 