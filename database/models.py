from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# 明星基本信息表
class Celebrity(Base):
    __tablename__ = 'celebrity'
    
    weibo_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    agency = Column(String(100))
    represent = Column(String(100))
    fan_size = Column(Integer)
    last_update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    posts = relationship("Post", back_populates="celebrity")

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
    
    celebrity = relationship("Celebrity", back_populates="posts")
    comments = relationship("Comment", back_populates="post")
    topics = relationship("Topic", secondary="post_topic", back_populates="posts")
    sentiment = relationship("SentimentForPost", back_populates="post", uselist=False)

# 评论信息表
class Comment(Base):
    __tablename__ = 'comment'
    
    comment_id = Column(String(50), primary_key=True)
    post_id = Column(String(50), ForeignKey('post.post_id'))
    fan_id = Column(Integer, ForeignKey('user.fan_id'))
    content = Column(Text)
    created_at = Column(DateTime)
    parent_id = Column(String(50), nullable=True)
    
    post = relationship("Post", back_populates="comments")
    fan = relationship("User", back_populates="comments")
    sentiment = relationship("SentimentForComment", back_populates="comment", uselist=False)

# 用户信息表
class User(Base):
    __tablename__ = 'user'
    
    fan_id = Column(Integer, primary_key=True)
    nickname = Column(String(100))
    gender = Column(Enum('male', 'female', 'unknown'))
    location = Column(String(100))
    fan_class = Column(Enum('loyal', 'casual', 'against'))
    fan_level = Column(Integer, default=0)
    
    comments = relationship("Comment", back_populates="fan")

# 话题信息表
class Topic(Base):
    __tablename__ = 'topic'
    
    name = Column(String(50), primary_key=True)
    emo_intensity = Column(Integer)
    emo_class = Column(Enum('positive', 'negative', 'neutral'))
    created_at = Column(DateTime)
    
    posts = relationship("Post", secondary="post_topic", back_populates="topics")
    heat_indices = relationship("TopicHeatIndex", back_populates="topic")

# 微博-话题关联表
class PostTopic(Base):
    __tablename__ = 'post_topic'
    
    post_id = Column(String(50), ForeignKey('post.post_id'), primary_key=True)
    topic_id = Column(String(50), ForeignKey('topic.name'), primary_key=True)

# 评论情感分析结果表
class SentimentForComment(Base):
    __tablename__ = 'sentiment_for_comment'
    
    comment_id = Column(String(50), ForeignKey('comment.comment_id'), primary_key=True)
    sentiment_category = Column(Enum('positive', 'negative', 'neutral'))
    emotion_intensity = Column(Float)
    
    comment = relationship("Comment", back_populates="sentiment")

# 微博情感分析结果表
class SentimentForPost(Base):
    __tablename__ = 'sentiment_for_post'
    
    post_id = Column(String(50), ForeignKey('post.post_id'), primary_key=True)
    sentiment_category = Column(Enum('positive', 'negative', 'neutral'))
    emotion_intensity = Column(Float)
    
    post = relationship("Post", back_populates="sentiment")

# 话题热度追踪表
class TopicHeatIndex(Base):
    __tablename__ = 'topic_heat_index'
    
    topic_name = Column(String(50), ForeignKey('topic.name'), primary_key=True)
    created_at = Column(DateTime, primary_key=True)
    comments_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    reposts_count = Column(Integer, default=0)
    
    topic = relationship("Topic", back_populates="heat_indices")

if __name__ == "__main__":
    # 测试配置
    test_config = {
        'database_url': 'mysql://root:123456@localhost/celebrity_sentiment'
    }
    
    # 创建数据库工具实例
    db = DatabaseManager()
    
    try:
        # 测试模型创建
        print("\n测试模型创建:")
        with db as session:
            # 创建测试明星
            test_celebrity = Celebrity(
                name="测试明星",
                weibo_id="test123",
                description="这是一个测试账号"
            )
            session.add(test_celebrity)
            session.commit()
            print("创建明星成功!")
            
            # 创建测试帖子
            test_post = Post(
                weibo_id="post123",
                content="这是一条测试帖子",
                likes=100,
                reposts=50,
                comments=30,
                created_at=datetime.now(),
                celebrity=test_celebrity
            )
            session.add(test_post)
            session.commit()
            print("创建帖子成功!")
            
            # 创建测试评论
            test_comment = Comment(
                weibo_id="comment123",
                content="这是一条测试评论",
                likes=10,
                created_at=datetime.now(),
                post=test_post
            )
            session.add(test_comment)
            session.commit()
            print("创建评论成功!")
            
            # 创建测试用户
            test_user = User(
                weibo_id="user123",
                nickname="测试用户",
                gender="男",
                location="北京",
                followers_count=1000,
                following_count=500
            )
            session.add(test_user)
            session.commit()
            print("创建用户成功!")
            
            # 创建测试话题
            test_topic = Topic(
                name="测试话题",
                description="这是一个测试话题",
                post_count=100,
                read_count=10000
            )
            session.add(test_topic)
            session.commit()
            print("创建话题成功!")
            
            # 测试关系查询
            print("\n测试关系查询:")
            celebrity = session.query(Celebrity).filter_by(name="测试明星").first()
            if celebrity:
                print(f"明星名称: {celebrity.name}")
                print(f"帖子数量: {len(celebrity.posts)}")
                for post in celebrity.posts:
                    print(f"- 帖子内容: {post.content}")
                    print(f"  评论数量: {len(post.comments)}")
    
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
    finally:
        # 关闭数据库连接
        db.close() 