#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库表创建脚本
在运行爬虫之前执行此脚本来创建所有必要的数据库表
"""

from flask import Flask
from sqlalchemy import inspect
from weibospider.models import db, User, Report, UserStar, WeiboUser, UserPost, WeiboFans, WeiboComments, KeywordPost
from weibospider.config import Config

def create_tables():
    """创建所有数据库表"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        try:
            # 创建所有表
            db.create_all()
            print("✅ 数据库表创建成功！")
            
            # 显示创建的表信息
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 已创建的表: {tables}")
            
            # 显示每个表的详细信息
            print("\n📊 表结构详情:")
            for table_name in tables:
                print(f"  - {table_name}")
                
        except Exception as e:
            print(f"❌ 创建表时出错: {e}")
            return False
    
    return True

if __name__ == '__main__':
    print("🚀 开始创建数据库表...")
    print(f"📡 数据库连接: {Config.SQLALCHEMY_DATABASE_URI}")
    print("-" * 50)
    
    success = create_tables()
    
    if success:
        print("-" * 50)
        print("🎉 数据库初始化完成！现在可以运行爬虫了。")
    else:
        print("-" * 50)
        print("💥 数据库初始化失败，请检查配置和数据库连接。") 