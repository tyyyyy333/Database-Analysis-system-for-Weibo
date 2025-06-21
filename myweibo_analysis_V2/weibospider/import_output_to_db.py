import os
import json
from snownlp import SnowNLP
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker
from config import Config
import csv
from sqlalchemy.dialects.mysql import insert as mysql_insert

# 数据库连接配置
DB_URI = Config.SQLALCHEMY_DATABASE_URI
engine = create_engine(DB_URI)
Session = sessionmaker(bind=engine)
session = Session()
metadata = MetaData()

def get_table(table_name):
    return Table(table_name, metadata, autoload_with=engine)

def insert_many(table, data_list):
    if not data_list:
        return
    with engine.begin() as conn:
        if table.name in ('weibo_fans', 'keyword_post', 'user_post', 'weibo_user'):
            # 用 MySQL 的 INSERT IGNORE 跳过重复主键或唯一索引
            stmt = mysql_insert(table).prefix_with('IGNORE')
            conn.execute(stmt, data_list)
        else:
            conn.execute(table.insert(), data_list)

def process_fan_file(filepath):
    table = get_table('weibo_fans')
    data_dict = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            fan_info = data.get('fan_info', {})
            row = {
                'fan_id': data.get('_id'),
                'name': fan_info.get('nick_name'),
                'following_count': fan_info.get('friends_count', 0),
                'followers_count': fan_info.get('followers_count', 0),
                'gender': fan_info.get('gender'),
                'region': fan_info.get('location'),
                'follower_id': data.get('follower_id'),
            }
            if row['fan_id']:
                data_dict[row['fan_id']] = row  # 后出现的覆盖前面的
    data_list = list(data_dict.values())
    insert_many(table, data_list)
    print(f"导入 {filepath} 到 weibo_fans 完成，共{len(data_list)}条")

def process_keyword_post_file(filepath):
    table = get_table('keyword_post')
    data_list = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            content = data.get('content', '')
            # 情感分析
            try:
                s = SnowNLP(content)
                data['sentiment_score'] = float(s.sentiments)
            except Exception:
                data['sentiment_score'] = None
            # 保证 id 字段存在
            if 'id' not in data or not data['id']:
                data['id'] = data.get('mblogid')
            data_list.append(data)
    insert_many(table, data_list)
    print(f"导入 {filepath} 到 keyword_post 完成，共{len(data_list)}条")

def process_user_file(filepath):
    table = get_table('weibo_user')
    data_list = []
    def map_gender(g):
        if g in ('f', 'female', '女'):
            return '女'
        elif g in ('m', 'male', '男'):
            return '男'
        else:
            return '未知'
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            # _id 字段映射为 id
            if 'id' not in data and '_id' in data:
                data['id'] = data['_id']
            # profession 对应 verified_reason
            if 'verified_reason' in data:
                data['profession'] = data['verified_reason']
            # gender 统一映射
            data['gender'] = map_gender(data.get('gender'))
            # 必须有 id 字段
            if not data.get('id'):
                continue
            data_list.append(data)
    insert_many(table, data_list)
    print(f"导入 {filepath} 到 weibo_user 完成，共{len(data_list)}条")

def process_user_post_file(filepath):
    table = get_table('user_post')
    data_list = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            # 保证 id 字段存在
            if 'id' not in data or not data['id']:
                data['id'] = data.get('mblogid')
            data_list.append(data)
    insert_many(table, data_list)
    print(f"导入 {filepath} 到 user_post 完成，共{len(data_list)}条")

def load_celebrity_map(txt_path='weibo_user.txt'):
    """读取 weibo_user.txt，返回 明星名->id 映射字典"""
    celeb_map = {}
    if os.path.exists(txt_path):
        with open(txt_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2:
                    celeb_map[parts[0]] = parts[1]
    return celeb_map

def process_comment_csv_file(filepath):
    """
    导入评论csv到 weibo_comments 表。
    自动从文件名提取 mblog_id（如: 时代少年团队长-马嘉祺_PwsW62Q5H_评论(Min版).csv，mblog_id=PwsW62Q5H）。
    明星名自动查 weibo_user.txt 映射 celebrity_id，支持部分匹配。
    只要文件名包含"评论"即可。
    """
    import re
    table = get_table('weibo_comments')
    filename = os.path.basename(filepath)
    # 匹配最后一个下划线和"评论"之间的内容为 mblog_id
    m = re.search(r'_([\w\d]+)_评论', filename)
    if not m:
        print(f"文件名不符合规则，跳过: {filename}")
        return
    mblog_id = m.group(1)
    # 明星名为第一个下划线前的部分
    celebrity_name = filename.split('_')[0] if '_' in filename else ''
    # 自动查 celebrity_id，支持部分匹配
    celeb_map = load_celebrity_map(os.path.join(os.path.dirname(__file__), 'weibo_user.txt'))
    celebrity_id = None
    for name, cid in celeb_map.items():
        if name in celebrity_name:
            celebrity_id = cid
            break
    if not celebrity_id:
        print(f"未找到明星id，跳过: {filename} (明星名: {celebrity_name})")
        return
    data_list = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader, None)  # 跳过标题行
        for row in reader:
            try:
                data = {
                    'user_id': int(row[3]) if row[3] else None,
                    'comment_time': row[4],
                    'gender': row[6],
                    'content': row[7],
                    'likes': int(row[8]) if row[8] else 0,
                    'replies': int(row[9]) if row[9] else 0,
                    'fan_badge': row[10],
                    'comment_ip': row[11],
                    'celebrity_id': celebrity_id,  # 自动补全
                    'mblog_id': mblog_id
                }
                data_list.append(data)
            except Exception as e:
                print(f"跳过行: {row}, 错误: {e}")
    insert_many(table, data_list)
    print(f"导入 {filepath} 到 weibo_comments 完成，共{len(data_list)}条")

def main():
    output_dir = 'output'
    for filename in os.listdir(output_dir):
        filepath = os.path.join(output_dir, filename)
        if filename.startswith('fan_') and filename.endswith('.jsonl'):
            process_fan_file(filepath)
        elif filename.startswith('tweet_spider_by_keyword') and filename.endswith('.jsonl'):
            process_keyword_post_file(filepath)
        elif filename.startswith('user_') and filename.endswith('.jsonl'):
            process_user_file(filepath)
        elif filename.startswith('tweet_spider_by_user_id') and filename.endswith('.jsonl'):
            process_user_post_file(filepath)
        elif filename.endswith('评论(Min版).csv'):
            process_comment_csv_file(filepath)
        # 可按需添加更多类型

if __name__ == '__main__':
    main() 