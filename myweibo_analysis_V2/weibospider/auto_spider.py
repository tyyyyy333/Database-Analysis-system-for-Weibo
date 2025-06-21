#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化爬虫脚本
读取weibo_user.txt文件中的用户ID，自动运行相关爬虫
"""

import os
import sys
import subprocess
import time
from datetime import datetime
import json

def read_user_ids(file_path='weibo_user.txt'):
    """读取用户ID文件，格式：姓名 ID"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            user_data = []
            for line_num, line in enumerate(f.readlines(), 1):
                line = line.strip()
                if line and not line.startswith('#'):  # 跳过空行和注释行
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[0]
                        user_id = parts[1]
                        user_data.append((name, user_id))
                    else:
                        print(f"Warning: 第{line_num}行格式错误: {line}")
            
            # 提取用户ID列表
            user_ids = [user_id for name, user_id in user_data]
            
            print(f"从 {file_path} 读取到 {len(user_ids)} 个用户:")
            for name, user_id in user_data:
                print(f"   - {name}: {user_id}")
            
            return user_ids
    except FileNotFoundError:
        print(f"Error: 找不到文件: {file_path}")
        return []
    except Exception as e:
        print(f"Error: 读取文件时出错: {e}")
        return []

def update_spider_file(spider_file, user_ids):
    """更新爬虫文件中的user_ids"""
    try:
        with open(spider_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找并替换user_ids
        if 'user_ids = [' in content:
            # 构建新的user_ids字符串
            new_user_ids = "['" + "','".join(user_ids) + "']"
            
            # 替换user_ids行
            import re
            pattern = r"user_ids = \[.*?\]"
            new_content = re.sub(pattern, f"user_ids = {new_user_ids}", content)
            
            # 写回文件
            with open(spider_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"已更新 {spider_file} 中的用户ID")
            return True
        else:
            print(f"Warning: 在 {spider_file} 中未找到 user_ids 配置")
            return False
            
    except Exception as e:
        print(f"Error: 更新 {spider_file} 时出错: {e}")
        return False

def run_spider(spider_name, output_dir='output'):
    """运行指定的爬虫"""
    import platform
    import os
    import subprocess
    try:
        print(f"开始运行爬虫: {spider_name}")
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        # 运行爬虫命令，强制cwd为weibospider目录
        weibospider_dir = os.path.dirname(os.path.abspath(__file__))
        cmd = ['python', 'run_spider.py', spider_name]
        if platform.system() == 'Windows':
            result = subprocess.run(cmd, cwd=weibospider_dir, capture_output=True, text=True, encoding='cp936', errors='ignore')
        else:
            result = subprocess.run(cmd, cwd=weibospider_dir, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            print(f"Success: {spider_name} 运行成功")
            if result.stdout:
                print(f"输出: {result.stdout}")
        else:
            print(f"Error: {spider_name} 运行失败")
            if result.stderr:
                print(f"错误: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error: 运行 {spider_name} 时出错: {e}")
        return False

def read_names(file_path='weibo_user.txt'):
    """读取姓名列表"""
    names = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 1:
                        names.append(parts[0])
        print(f"从 {file_path} 读取到 {len(names)} 个姓名: {names}")
    except Exception as e:
        print(f"Error: 读取姓名时出错: {e}")
    return names

def read_name_id_map(file_path='weibo_user.txt'):
    """读取姓名和ID的映射"""
    name_id_map = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2:
                        name_id_map[parts[0]] = parts[1]
    except Exception as e:
        print(f"Error: 读取姓名ID映射时出错: {e}")
    return name_id_map

def update_keyword_spider_file(spider_file, keywords, name_id_map):
    """更新爬虫文件中的keywords和name_id_map"""
    try:
        with open(spider_file, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'keywords = [' in content:
            new_keywords = "['" + "','".join(keywords) + "']"
            import re
            pattern = r"keywords = \[.*?\]"
            new_content = re.sub(pattern, f"keywords = {new_keywords}", content)
            # 写入 name_id_map
            if 'name_id_map =' in new_content:
                pattern2 = r"name_id_map = \{.*?\}\n"
                new_content = re.sub(pattern2, f"name_id_map = {json.dumps(name_id_map, ensure_ascii=False)}\n", new_content)
            else:
                new_content = "name_id_map = " + json.dumps(name_id_map, ensure_ascii=False) + "\n" + new_content
            with open(spider_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"已更新 {spider_file} 中的 keywords 和 name_id_map")
            return True
        else:
            print(f"Warning: 在 {spider_file} 中未找到 keywords 配置")
            return False
    except Exception as e:
        print(f"Error: 更新 {spider_file} 时出错: {e}")
        return False

def main():
    """主函数"""
    print("开始自动化爬虫任务")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    # 1. 读取用户ID
    user_ids = read_user_ids()
    if not user_ids:
        print("Error: 没有读取到用户ID，程序退出")
        return
    
    # 2. 定义需要更新的爬虫文件
    spider_files = [
        'spiders/user.py',
        'spiders/fan.py', 
        'spiders/tweet_by_user_id.py'
    ]
    
    # 3. 更新爬虫文件中的用户ID
    print("\n更新爬虫文件中的用户ID...")
    for spider_file in spider_files:
        if os.path.exists(spider_file):
            update_spider_file(spider_file, user_ids)
        else:
            print(f"Warning: 文件不存在: {spider_file}")
    
    # 4. 先运行 tweet_by_user_id 爬虫
    print("\n========== 调试 tweet_by_user_id 爬虫 ==========")
    print("准备运行 tweet_by_user_id 爬虫...")
    tweet_debug_success = run_spider('tweet_by_user_id')
    print(f"tweet_by_user_id 爬虫运行结果: {tweet_debug_success}")
    print("========== tweet_by_user_id 调试结束 ==========")
    
    # 5. 运行其他爬虫
    print("\n开始运行其他爬虫...")
    spiders_to_run = ['user', 'fan']
    
    success_count = 0
    for spider in spiders_to_run:
        print(f"\n{'='*50}")
        print(f"运行爬虫: {spider}")
        print(f"{'='*50}")
        
        if run_spider(spider):
            success_count += 1
        
        # 爬虫之间稍作休息
        if spider != spiders_to_run[-1]:  # 不是最后一个爬虫
            print("等待5秒后运行下一个爬虫...")
            time.sleep(5)
    
    # 6. 处理关键词爬虫
    print("\n处理关键词爬虫...")
    names = read_names()
    name_id_map = read_name_id_map()
    keyword_spider_file = 'spiders/tweet_by_keyword.py'
    if os.path.exists(keyword_spider_file):
        update_keyword_spider_file(keyword_spider_file, names, name_id_map)
        print("运行 tweet_by_keyword 爬虫...")
        run_spider('tweet_by_keyword')
    else:
        print(f"Warning: 文件不存在: {keyword_spider_file}")
    
    # 7. 输出结果
    print(f"\n{'='*60}")
    print(f"爬虫任务完成!")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"成功运行: {success_count}/2 个爬虫 + tweet_by_user_id + 关键词爬虫")
    print(f"输出目录: {os.path.abspath('output')}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main() 