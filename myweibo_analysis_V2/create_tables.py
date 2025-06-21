#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库表创建脚本 - 入口文件
在运行爬虫之前执行此脚本来创建所有必要的数据库表
"""

import sys
import os
import importlib.util

def run_init_db():
    """运行weibospider目录中的数据库初始化脚本"""
    weibospider_dir = os.path.join(os.path.dirname(__file__), 'weibospider')
    init_db_script = os.path.join(weibospider_dir, 'init_db.py')
    
    if not os.path.exists(init_db_script):
        print("❌ 找不到 weibospider/init_db.py 文件")
        return False
    
    try:
        # 用importlib按文件路径导入
        spec = importlib.util.spec_from_file_location("init_db", init_db_script)
        init_db = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(init_db)
        return init_db.create_tables()
        
    except Exception as e:
        print(f"❌ 运行脚本时出错: {e}")
        return False

if __name__ == '__main__':
    print("🚀 开始创建数据库表...")
    print("📁 使用 weibospider/init_db.py 脚本")
    print("-" * 50)
    
    success = run_init_db()
    
    if success:
        print("-" * 50)
        print("🎉 数据库初始化完成！现在可以运行爬虫了。")
    else:
        print("-" * 50)
        print("💥 数据库初始化失败，请检查配置和数据库连接。") 