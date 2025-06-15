from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    weibo_id = Column(String(50), unique=True, index=True)
    nickname = Column(String(100))
    verified = Column(Boolean, default=False)
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    posts = relationship("Post", back_populates="user")
    comments = relationship("Comment", back_populates="user")

class Post(Base):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    weibo_id = Column(String(50), unique=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    content = Column(Text)
    created_at = Column(DateTime)
    reposts_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    attitudes_count = Column(Integer, default=0)
    read_count = Column(Integer, default=0)
    source = Column(String(100))
    pictures = Column(Text)  # JSON字符串存储图片URL
    video_url = Column(String(500))
    
    user = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")

class Comment(Base):
    __tablename__ = 'comments'
    
    id = Column(Integer, primary_key=True)
    weibo_id = Column(String(50), unique=True, index=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    content = Column(Text)
    created_at = Column(DateTime)
    like_count = Column(Integer, default=0)
    sentiment_score = Column(Float)  # 情感分析分数
    is_black_fan = Column(Boolean, default=False)  # 黑粉标记
    
    post = relationship("Post", back_populates="comments")
    user = relationship("User", back_populates="comments") 