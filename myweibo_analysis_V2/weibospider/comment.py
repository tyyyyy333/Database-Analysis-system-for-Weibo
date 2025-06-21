
import requests
import json
from datetime import datetime
import csv
import time
import os

# 统计评论数量
count = 0
# 最大爬取数量
MAX_COMMENTS = 300

def add_count():
    global count
    count += 1

# 从txt文件获取cookie
def get_header():
    try:
        with open("cookie.txt", 'r') as f:
            cookie = f.read().strip()
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Cookie": cookie
        }
    except Exception as e:
        print(f"获取Cookie失败: {e}")
        return {}

# 提取url中的关键词
def get_keyword(url):
    parts = url.split('/')
    return parts[-2], url_to_mid(parts[-1])

# 解码
def decode_base62(b62_str):
    charset = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    base = 62
    num = 0
    for c in b62_str:
        num = num * base + charset.index(c)
    return num

def url_to_mid(url):
    result = ''
    for i in range(len(url), 0, -4):
        start = max(i - 4, 0)
        segment = url[start:i]
        num = str(decode_base62(segment))
        if start != 0:
            num = num.zfill(7)  # 除最后一段外都补满7位
        result = num + result
    return int(result)

# 根据UID返回博主的用户名
def get_name(uid):
    url = f"https://weibo.com/ajax/profile/info?custom={uid}"
    try:
        response = requests.get(url=url, headers=get_header())
        return json.loads(response.content.decode('utf-8'))['data']['user']['screen_name']
    except Exception as e:
        print(f"获取用户名失败: {e}")
        return "未知用户"

# 解析json数据并返回
def get_data(data):
    # 评论ID
    idstr = data['idstr']
    # 上级评论ID
    rootidstr = data.get('rootidstr', '')
    # 发表日期
    created_at = data['created_at']
    try:
        dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
        created_at = dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        created_at = ""
    # 用户名
    screen_name = data['user']['screen_name']
    # 用户ID
    user_id = data['user']['id']
    # 评论内容
    text_raw = data.get('text_raw', '')
    # 评论点赞数
    like = data.get('like_counts', 0)
    # 评论回复数量
    total_number = data.get('total_number', 0)
    # 评论IP
    com_source = data.get('source', '')[2:] if 'source' in data else ''
    # 粉丝等级
    fan = {
        '1': '铁粉',
        '2': '金粉',
        '3': '钻粉'
    }
    fansIcon = ''
    try:
        icon_url = data['user']['fansIcon']['icon_url']
        fansIcon = f"{fan[icon_url[-7]]}{icon_url[-5]}"
    except:
        pass

    # 获取用户信息
    # 粉丝
    followers_count = data['user'].get('followers_count', 0)
    # 关注
    friends_count = data['user'].get('friends_count', 0)
    # 转赞评
    total_cnt = ''
    try:
        total_cnt = data['user']['status_total_counter']['total_cnt']
        total_cnt = int(total_cnt.replace(",", ""))
    except:
        pass
    # 简介
    description = data['user'].get('description', '')
    # 是否认证
    verified = '是' if data['user'].get('verified', False) else '否'
    # 性别
    gender = data['user'].get('gender', '未知')
    if gender == 'm':
        gender = '男'
    elif gender == 'f':
        gender = '女'
    # 会员等级
    svip = data['user'].get('svip', '')

    return idstr, rootidstr, created_at, user_id, screen_name, text_raw, like, total_number, com_source, fansIcon, followers_count, friends_count, total_cnt, description, verified, gender, svip

# 返回评论数据
def get_information(uid, mid, max_id, fetch_level):
    global count
    
    # 达到最大数量时停止
    if count >= MAX_COMMENTS:
        return

    if max_id == '':
        url = f"https://weibo.com/ajax/statuses/buildComments?flow=1&is_reload=1&id={mid}&is_show_bulletin=2&is_mix=0&count=20&uid={uid}&fetch_level={fetch_level}&locale=zh-CN"
    else:
        url = f"https://weibo.com/ajax/statuses/buildComments?flow=1&is_reload=1&id={mid}&is_show_bulletin=2&is_mix=0&max_id={max_id}&count=20&uid={uid}&fetch_level={fetch_level}&locale=zh-CN"

    try:
        resp = requests.get(url=url, headers=get_header())
        resp.raise_for_status()  # 检查请求是否成功
        resp_data = json.loads(resp.content.decode('utf-8'))
        datas = resp_data.get('data', [])
    except Exception as e:
        print(f"请求失败: {e}")
        return

    for data in datas:
        # 达到最大数量时停止
        if count >= MAX_COMMENTS:
            return

        add_count()
        
        # 每爬取100条数据，等待5秒，防止反爬干扰
        if count % 100 == 0:
            print(f"已爬取到{count}条数据，防止爬取过快，等待5秒......")
            time.sleep(5)

        idstr, rootidstr, created_at, user_id, screen_name, text_raw, like, total_number, com_source, fansIcon, followers_count, friends_count, total_cnt, description, verified, gender, svip = get_data(data)
        if fetch_level == 0:
            rootidstr = ''
        csv_writer.writerow([count, idstr, rootidstr, user_id, created_at, screen_name, gender, text_raw, like, total_number, fansIcon, com_source, description, verified, svip, followers_count, friends_count, total_cnt])
        
        # 判断是否存在二级评论
        if total_number > 0 and fetch_level == 0 and count < MAX_COMMENTS:
            get_information(uid, idstr, 0, 1)
    
    print(f"当前爬取:{count}条")
    
    # 下一条索引
    max_id = resp_data.get('max_id', 0)
    if max_id != 0 and count < MAX_COMMENTS:    
        get_information(uid, mid, max_id, fetch_level)


if __name__ == "__main__":
    # 统计爬虫运行时间
    start = time.time()

    url = "https://weibo.com/6290114447/PwlQ17pIq"
    uid, mid = get_keyword(url)
    
    # 创建保存数据的目录（上一级目录的output文件夹）
    save_dir = '../output/'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"已创建目录: {save_dir}")
    
    # 创建CSV文件并写入表头
    print(f"\n创建csv表中...\n表名：{get_name(uid)}_{url.split('/')[-1]}_评论(Min版)....")
    try:
        csv_path = f'{save_dir}{get_name(uid)}_{url.split("/")[-1]}_评论(Min版).csv'
        with open(csv_path, mode='w', newline='', encoding='utf-8-sig') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(['序号', '评论标识号', '上级评论', '用户标识符', '时间', '用户名', '性别', '评论内容', '评论点赞数', '评论回复数', '粉丝牌', '评论IP', '用户简介', '是否认证', '会员等级', '用户粉丝数', '用户关注数', '用户转赞评数'])
            get_information(uid, mid, '', 0)
    except Exception as e:
        print(f"写入CSV文件出错: {e}")
    
    print(f"评论爬取完成，共计{count}条，耗时{(time.time()-start)/60:.2f}分")