#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化爬虫入口脚本
从根目录运行，自动执行weibospider目录中的爬虫任务
"""

import os
import sys
import subprocess
import platform
from datetime import datetime

def main():
    """主函数"""
    # 切换到weibospider目录
    weibospider_dir = os.path.join(os.path.dirname(__file__), 'weibospider')
    
    if not os.path.exists(weibospider_dir):
        print("❌ 找不到 weibospider 目录")
        return
    
    # 检查auto_spider.py是否存在
    auto_spider_script = os.path.join(weibospider_dir, 'auto_spider.py')
    if not os.path.exists(auto_spider_script):
        print("❌ 找不到 weibospider/auto_spider.py 文件")
        return
    
    print("🚀 启动自动化爬虫任务")
    print(f"📁 工作目录: {os.path.abspath(weibospider_dir)}")
    print("-" * 50)
    
    try:
        # 切换到weibospider目录并运行脚本，使用更兼容的编码设置
        if platform.system() == 'Windows':
            result = subprocess.run([sys.executable, 'auto_spider.py'], 
                                  cwd=weibospider_dir, 
                                  capture_output=True, 
                                  text=True, 
                                  encoding='cp936',
                                  errors='ignore')
        else:
            result = subprocess.run([sys.executable, 'auto_spider.py'], 
                                  cwd=weibospider_dir, 
                                  capture_output=True, 
                                  text=True, 
                                  encoding='utf-8',
                                  errors='ignore')
        
        # 输出结果
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✅ 自动化爬虫任务完成!")
        else:
            print(f"\n❌ 自动化爬虫任务失败，退出码: {result.returncode}")
            
        # 7. 输出结果
        print(f"\n{'='*60}")
        print(f"爬虫任务完成!")
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"输出目录: {os.path.abspath('output')}")
        print(f"{'='*60}")

        # 8. 自动导入数据库
        print("\n开始自动导入 output 目录数据到数据库...")
        import_script = os.path.join('weibospider', 'import_output_to_db.py')
        if os.path.exists(import_script):
            try:
                if platform.system() == 'Windows':
                    result = subprocess.run([sys.executable, import_script],
                                           cwd=os.path.dirname(os.path.abspath(__file__)),
                                           capture_output=True,
                                           text=True,
                                           encoding='cp936',
                                           errors='ignore')
                else:
                    result = subprocess.run([sys.executable, import_script],
                                           cwd=os.path.dirname(os.path.abspath(__file__)),
                                           capture_output=True,
                                           text=True,
                                           encoding='utf-8',
                                           errors='ignore')
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                if result.returncode == 0:
                    print("\n✅ 数据导入数据库完成!")
                else:
                    print(f"\n❌ 数据导入失败，退出码: {result.returncode}")
            except Exception as e:
                print(f"❌ 运行数据导入脚本时出错: {e}")
        else:
            print(f"❌ 找不到 {import_script} 文件，无法导入数据库")
            
    except Exception as e:
        print(f"❌ 运行自动化爬虫时出错: {e}")

if __name__ == '__main__':
    main() 