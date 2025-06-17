from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Enum, JSON, ForeignKey, Boolean, text, Date, ForeignKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    role = Column(String(10), default='user')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)
    
    # 关联关系 - 用户关注的明星
    monitored_celebrities = relationship("Celebrity", 
                                       secondary="user_celebrity",
                                       back_populates="monitoring_users")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 用户-明星关联表
class UserCelebrity(Base):
    __tablename__ = 'user_celebrity'
    
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    celebrity_id = Column(String(50), ForeignKey('celebrity.weibo_id'), primary_key=True)
    created_at = Column(DateTime)
    
    # 关联关系
    user = relationship("User", overlaps="monitored_celebrities")
    celebrity = relationship("Celebrity", overlaps="monitoring_users")

# 明星基本信息表
class Celebrity(Base):
    __tablename__ = 'celebrity'
    
    weibo_id = Column(String(50), primary_key=True)
    name = Column(String(50), nullable=False)
    category = Column(String(50))
    fans_count = Column(Integer, default=0)
    post_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    monitoring_users = relationship("User", 
                                  secondary="user_celebrity",
                                  back_populates="monitored_celebrities",
                                  overlaps="user,celebrity")
    posts = relationship("Post", back_populates="celebrity")
    black_fans = relationship("BlackFan", back_populates="celebrity")
    black_fan_analysis = relationship("BlackFanAnalysis", back_populates="celebrity")
    heat_data = relationship("HeatData", back_populates="celebrity")

# 微博内容表
class Post(Base):
    __tablename__ = 'post'
    
    post_id = Column(String(50), primary_key=True)
    celebrity_id = Column(String(50), ForeignKey('celebrity.weibo_id'))
    content = Column(Text)
    likes = Column(Integer, default=0)
    reposts = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    created_at = Column(DateTime)
    is_deleted = Column(Integer, default=0)
    sentiment_score = Column(Float, default=0.0)  # 添加情感分数列，0表示中性
    
    # 关联关系
    celebrity = relationship("Celebrity", back_populates="posts")
    comments = relationship("Comment", back_populates="post")
    sentiment = relationship("SentimentForPost", back_populates="post", uselist=False)

# 评论信息表
class Comment(Base):
    __tablename__ = 'comment'
    
    comment_id = Column(String(50), primary_key=True)
    post_id = Column(String(50), ForeignKey('post.post_id'))
    content = Column(Text)
    created_at = Column(DateTime)
    parent_id = Column(String(50), nullable=True)
    
    # 关联关系
    post = relationship("Post", back_populates="comments")
    sentiment = relationship("SentimentForComment", back_populates="comment", uselist=False)

# 评论情感分析结果表
class SentimentForComment(Base):
    __tablename__ = 'sentiment_for_comment'
    
    comment_id = Column(String(50), ForeignKey('comment.comment_id'), primary_key=True)
    sentiment_category = Column(Enum('positive', 'negative', 'neutral'))
    emotion_intensity = Column(Float)
    analyzed_by = Column(Integer, ForeignKey('users.id'))
    
    # 关联关系
    comment = relationship("Comment", back_populates="sentiment")
    analyzer = relationship("User", backref="analyzed_comments")

# 微博情感分析结果表
class SentimentForPost(Base):
    __tablename__ = 'sentiment_for_post'
    
    post_id = Column(String(50), ForeignKey('post.post_id'), primary_key=True)
    sentiment_category = Column(Enum('positive', 'negative', 'neutral'))
    emotion_intensity = Column(Float)
    analyzed_by = Column(Integer, ForeignKey('users.id'))
    
    # 关联关系
    post = relationship("Post", back_populates="sentiment")
    analyzer = relationship("User", backref="analyzed_posts")
    
# 黑粉表
class BlackFan(Base):
    __tablename__ = 'black_fans'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    celebrity_id = Column(String(50), ForeignKey('celebrity.weibo_id'), nullable=False)
    black_fan_score = Column(Float, nullable=False)  # 黑粉分数
    comment_count = Column(Integer, default=0)      # 评论数量
    last_active = Column(DateTime)                  # 最后活跃时间
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联关系
    celebrity = relationship("Celebrity", back_populates="black_fans")

# 黑粉分析结果表
class BlackFanAnalysis(Base):
    __tablename__ = 'black_fan_analysis'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    celebrity_id = Column(String(50), ForeignKey('celebrity.weibo_id'), nullable=False)
    analysis_time = Column(DateTime, nullable=False)
    analysis_results = Column(JSON, nullable=False)  # 分析结果（JSON格式）
    
    # 关联关系
    celebrity = relationship("Celebrity", back_populates="black_fan_analysis")

# 热度数据表
class HeatData(Base):
    """热度数据表"""
    __tablename__ = 'heat_data'
    
    date = Column(Date, primary_key=True, index=True)  # 日期作为主键
    celebrity_id = Column(String(50), primary_key=True, index=True)  # 明星ID作为联合主键
    post_count = Column(Integer, default=0)  # 微博数量
    comment_count = Column(Integer, default=0)  # 评论数量
    like_count = Column(Integer, default=0)  # 点赞数量
    repost_count = Column(Integer, default=0)  # 转发数量
    total_heat = Column(Float, default=0.0)  # 总热度值
    heat_change = Column(Float, default=0.0)  # 热度变化值（相比前一天）
    
    # 关联关系
    celebrity = relationship("Celebrity", back_populates="heat_data")
    
    __table_args__ = (
        ForeignKeyConstraint(['celebrity_id'], ['celebrity.weibo_id']),
    )

if __name__ == "__main__":
   pass