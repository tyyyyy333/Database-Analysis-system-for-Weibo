from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
import os
from dotenv import load_dotenv

# 加载环境变量配置
load_dotenv()

# 数据库连接配置
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME', 'celebrity_sentiment')

# 创建数据库连接URL
DATABASE_URL = f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)

# 创建数据库会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 数据库会话上下文管理器
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 初始化数据库表结构
def init_db():
    from .models import Base
    Base.metadata.create_all(bind=engine)

# 数据库操作管理类
class DatabaseManager:
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    # 添加单个对象
    def add(self, obj):
        self.db.add(obj)
        self.db.commit()
        return obj
    
    # 批量添加对象
    def add_all(self, objs):
        self.db.add_all(objs)
        self.db.commit()
        return objs
    
    # 删除对象
    def delete(self, obj):
        self.db.delete(obj)
        self.db.commit()
    
    # 提交事务
    def commit(self):
        self.db.commit()
    
    # 回滚事务
    def rollback(self):
        self.db.rollback()

if __name__ == "__main__":
    # 测试配置
    test_config = {
        'database_url': 'mysql://root:123456@localhost/celebrity_sentiment'
    }
    
    # 创建数据库工具实例
    db = DatabaseManager()
    
    try:
        # 测试数据库连接
        print("\n测试数据库连接:")
        with db as session:
            print("数据库连接成功!")
        
        # 测试查询示例
        print("\n测试查询示例:")
        with db as session:
            # 查询所有明星
            celebrities = session.db.query(Celebrity).all()
            print(f"数据库中的明星数量: {len(celebrities)}")
            
            # 查询最近的帖子
            recent_posts = session.db.query(Post).order_by(Post.created_at.desc()).limit(5).all()
            print(f"\n最近的5条帖子:")
            for post in recent_posts:
                print(f"- {post.content[:50]}...")
            
            # 测试事务
            print("\n测试事务:")
            try:
                with session.db as session:
                    # 创建测试数据
                    test_celebrity = Celebrity(
                        name="测试明星",
                        weibo_id="test123",
                        description="这是一个测试账号"
                    )
                    session.add(test_celebrity)
                    # 这里故意不提交，测试回滚
                    raise Exception("测试回滚")
            except Exception as e:
                print(f"事务回滚成功: {str(e)}")
    
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
    finally:
        # 关闭数据库连接
        db.db.close() 