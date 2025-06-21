from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

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