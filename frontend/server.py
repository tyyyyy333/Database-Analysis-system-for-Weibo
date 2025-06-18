from flask import Flask, send_from_directory, render_template, jsonify, request, redirect, url_for, g, session
import os
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
import sys
import os
import asyncio
import traceback
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from dotenv import load_dotenv
from flask_socketio import SocketIO, emit

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'api'))

from api.database.models import *
from werkzeug.security import generate_password_hash
from api.datacrawl.datacrawl.spider_runner import WeiboSpiderRunner
from api.analysis.sentiment.sentiment_analyzer import SentimentAnalyzer
from api.analysis.sentiment.sentiment_analyzer import PostSentimentAnalyzer
from api.analysis.sentiment.black_fan_analyzer import BlackFanAnalyzer
from api.analysis.heat.heat_analyzer import HeatAnalyzer
from api.analysis.fan_analysis import FanAnalyzer

app = Flask(__name__, 
    static_folder='.',
    template_folder='.'
)
socketio = SocketIO(app, cors_allowed_origins="*")

# 加载环境变量
load_dotenv()

# 设置session密钥
app.secret_key = os.urandom(24)

# 数据库配置
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'celebrity_sentiment.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

# 确保数据目录存在
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# 创建数据库连接URL
DATABASE_URL = f"sqlite:///{DB_PATH}"

# 数据库配置
def init_db():
    try:
        # 创建数据库引擎
        engine = create_engine(
            DATABASE_URL,
            connect_args={'check_same_thread': False}  # 允许多线程访问
        )
        
        # 创建所有表
        Base.metadata.create_all(engine)
        
        # 创建会话工厂
        session_factory = sessionmaker(bind=engine)
        Session = scoped_session(session_factory)
        
        # 测试数据库连接
        test_session = Session()
        test_session.execute(text('SELECT 1'))
        
        print("数据库连接成功")
        return engine, Session
    except Exception as e:
        print(f"数据库初始化失败: {str(e)}")
        print(traceback.format_exc())
        raise

# 初始化数据库
engine, Session = init_db()

# 请求前创建数据库会话
@app.before_request
def before_request():
    g.db = Session()

# 请求后关闭数据库会话
@app.teardown_request
def teardown_request(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# 使用内存存储明星数据
stars_data = []
next_id = 1

# 全局变量
analyzers = {}

# 创建线程池
thread_pool = ThreadPoolExecutor(max_workers=4)

# 初始化分析器实例
def init_analyzers():
    try:
        sentiment_analyzer = SentimentAnalyzer(DATABASE_URL)
        post_sentiment_analyzer = PostSentimentAnalyzer(DATABASE_URL)
        black_fan_analyzer = BlackFanAnalyzer(DATABASE_URL)
        heat_analyzer = HeatAnalyzer(DATABASE_URL)
        fan_analyzer = FanAnalyzer(DATABASE_URL)
        
        print("分析器初始化成功")
        return {
            'sentiment': sentiment_analyzer,
            'post_sentiment': post_sentiment_analyzer,
            'black_fan': black_fan_analyzer,
            'heat': heat_analyzer,
            'fan': fan_analyzer
        }
    except Exception as e:
        print(f"分析器初始化失败: {str(e)}")
        raise

analyzers = init_analyzers()

@app.route('/')
def index():
    return redirect(url_for('index_home'))

@app.route('/index_home')
def index_home():
    return send_from_directory('.', 'index_home.html')

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect('/home')
    return send_from_directory('.', 'index.html')

@app.route('/home')
def home():
    return send_from_directory('.', 'home.html')

@app.route('/star_detail.html')
def star_detail():
    return send_from_directory('.', 'star_detail.html')

@app.route('/star_dashboard')
def star_dashboard():
    return send_from_directory('.', 'star_dashboard.html')

@app.route('/settings')
def system_settings():
    return send_from_directory('.', 'system_settings.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'status': 'error', 'message': '用户名或密码不能为空'}), 400
    
    try:
        user = Session.query(User).filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                return jsonify({'status': 'error', 'message': '账户已被禁用'}), 403
                
            # 更新最后登录时间
            user.last_login = datetime.now()
            Session.commit()
            
            # 在session中保存用户信息
            session['user_id'] = user.id
            session['username'] = user.username
            
            return jsonify({
                'status': 'success',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                }
            })
        else:
            return jsonify({'status': 'error', 'message': '用户名或密码错误'}), 401
            
    except Exception as e:
        Session.rollback()
        return jsonify({'status': 'error', 'message': f'登录失败：{str(e)}'}), 500

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not all([username, password, email]):
        return jsonify({'status': 'error', 'message': '所有字段都是必填的'}), 400
    
    try:
        # 检查用户名是否已存在
        if Session.query(User).filter_by(username=username).first():
            return jsonify({'status': 'error', 'message': '用户名已存在'}), 400
            
        # 检查邮箱是否已存在
        if Session.query(User).filter_by(email=email).first():
            return jsonify({'status': 'error', 'message': '邮箱已被注册'}), 400
        
        # 创建新用户
        new_user = User(
            username=username,
            email=email,
            role='user',
            is_active=True
        )
        new_user.set_password(password)
        
        Session.add(new_user)
        Session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '注册成功',
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email,
                'role': new_user.role
            }
        })
            
    except Exception as e:
        Session.rollback()
        print(f"注册失败，错误详情: {str(e)}")  # 添加详细错误日志
        print(traceback.format_exc())  # 打印完整的错误堆栈
        return jsonify({'status': 'error', 'message': f'注册失败：{str(e)}'}), 500

@app.route('/api/stars', methods=['GET'])
def get_all_stars():
    """获取所有明星列表"""
    try:
        current_user_id = session.get('user_id')
        if not current_user_id:
            return jsonify({'error': '未登录'}), 401
            
        # 获取当前用户关注的所有明星
        user_celebrities = g.db.query(UserCelebrity).filter_by(user_id=current_user_id).all()
        celebrity_ids = [uc.celebrity_id for uc in user_celebrities]
        print(celebrity_ids)
        if not celebrity_ids:
            return jsonify([])
            
        # 查询明星信息
        celebrities = g.db.query(Celebrity).filter(Celebrity.weibo_id.in_(celebrity_ids)).all()
        
        # 构建响应数据
        stars = []
        for celebrity in celebrities:
            stars.append({
                'id': celebrity.weibo_id,
                'name': celebrity.name,
                'url': f'https://weibo.com/u/{celebrity.weibo_id}',
                'status': '正常',  # 这里可以根据实际情况设置状态
                'fans': 0,  # 这里可以从其他表获取实际数据
                'topics': 0,
                'alert_count': 0,
                'sentiment_score': 0
            })
            
        return jsonify(stars)
        
    except Exception as e:
        print(f"获取明星列表失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

def on_spider_complete(celebrity_info):
    """爬虫完成回调"""
    try:
        # 1. 运行情感分析
        sentiment_analyzer = SentimentAnalyzer(DB_PATH)
        sentiment_result = sentiment_analyzer.analyze_black_fan(celebrity_info['weibo_id'])
        if not sentiment_result:
            raise Exception("情感分析失败")
            
        # 2. 运行粉丝分析
        fan_analyzer = FanAnalyzer(DB_PATH)
        fan_result = fan_analyzer.analyze_fans(celebrity_info['weibo_id'])
        if not fan_result:
            raise Exception("粉丝分析失败")
            
        # 3. 运行黑粉分析
        black_fan_analyzer = BlackFanAnalyzer(DB_PATH)
        black_fan_result = black_fan_analyzer.analyze_black_fans(celebrity_info['weibo_id'])
        if not black_fan_result:
            raise Exception("黑粉分析失败")
            
        # 4. 运行热度分析
        heat_analyzer = HeatAnalyzer(DB_PATH)
        heat_result = heat_analyzer.update_heat_data(celebrity_info['weibo_id'])
        if not heat_result:
            raise Exception("热度分析失败")
            
        # 5. 通知前端更新
        socketio.emit('analysis_complete', {
            'celebrity_id': celebrity_info['weibo_id'],
            'status': 'success',
            'message': '数据分析完成',
            'data': {
                'sentiment': sentiment_result,
                'fan': fan_result,
                'black_fan': black_fan_result,
                'heat': heat_result
            }
        })
        
    except Exception as e:
        print(f"数据分析失败: {str(e)}")
        socketio.emit('analysis_complete', {
            'celebrity_id': celebrity_info['weibo_id'],
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/stars', methods=['POST'])
def add_star():
    """添加明星"""
    try:
        data = request.get_json()
        star_name = data.get('name')
        star_url = data.get('star_url')
        current_user_id = session.get('user_id')  # 从session获取user_id
        
        if not all([star_name, star_url, current_user_id]):
            print([star_name, star_url, current_user_id])
            return jsonify({'error': '缺少必要参数','message': '缺少必要参数'}), 400
            
        try:
            # 从URL中提取微博ID
            weibo_id = star_url.split('/')[-1]
            
            # 检查明星是否已存在
            existing_celebrity = g.db.query(Celebrity).filter_by(weibo_id=weibo_id).first()
            if existing_celebrity:
                # 检查用户是否已经关注了这个明星
                existing_relation = g.db.query(UserCelebrity).filter_by(
                    user_id=current_user_id,
                    celebrity_id=weibo_id
                ).first()
                
                if existing_relation:
                    return jsonify({
                        'status': 'error',
                        'error': '您已经关注了这个明星',
                        'message': '您已经关注了这个明星'
                    }), 401
                else:
                    user_celebrity = UserCelebrity(
                        user_id=current_user_id,
                        celebrity_id=weibo_id,
                        created_at=datetime.now()
                    )
                    g.db.add(user_celebrity)
                    g.db.commit()
                    
                    return jsonify({
                        'status': 'success',
                        'message': '成功关注已存在的明星',
                        'star_id': weibo_id
                    })
            
            # 创建明星记录
            celebrity = Celebrity(
                weibo_id=weibo_id,
                name=star_name,
                created_at=datetime.now()
            )
            g.db.add(celebrity)
            
            # 创建用户-明星关联
            user_celebrity = UserCelebrity(
                user_id=current_user_id,
                celebrity_id=weibo_id,
                created_at=datetime.now()
            )
            g.db.add(user_celebrity)
            
            # 提交事务
            g.db.commit()
            
            # 初始化爬虫
            spider_runner = WeiboSpiderRunner({
                'database': DB_PATH
            })
            
            # 设置微博cookie
            weibo_cookie = os.getenv('WEIBO_COOKIE')
            if not weibo_cookie:
                raise ValueError("未配置微博cookie，请在环境变量中设置WEIBO_COOKIE")
            spider_runner.set_cookie(weibo_cookie)
            
            # 设置完成回调
            spider_runner.set_complete_callback(on_spider_complete)
            
            # 设置爬取时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            # 更新内存中的明星数据
            global stars_data
            stars_data.append({
                'id': len(stars_data) + 1,
                'name': star_name,
                'url': star_url,
                'status': '爬取中',
                'fans': 0,
                'topics': 0,
                'alert_count': 0,
                'sentiment_score': 0
            })
            
            # 立即返回响应
            response = jsonify({
                'status': 'success',
                'message': '明星添加成功，开始爬取数据',
                'star_id': celebrity.weibo_id
            })
            
            # 在返回响应后启动爬虫
            def start_spider():
                try:
                    result = spider_runner.run_spider(
                        celebrity_info={
                            'name': star_name,
                            'url': star_url,
                            'weibo_id': celebrity.weibo_id
                        },
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d')
                    )
                    
                    if result and result.get('status') == 'error':
                        print(f"爬虫运行失败: {result.get('message')}")
                        socketio.emit('analysis_complete', {
                            'celebrity_id': celebrity.weibo_id,
                            'status': 'error',
                            'message': result.get('message')
                        })
                except Exception as e:
                    print(f"爬虫运行异常: {str(e)}")
                    socketio.emit('analysis_complete', {
                        'celebrity_id': celebrity.weibo_id,
                        'status': 'error',
                        'message': str(e)
                    })
            
            # 使用线程启动爬虫
            thread = threading.Thread(target=start_spider)
            thread.daemon = True
            thread.start()
            
            return response
            
        except Exception as e:
            g.db.rollback()
            raise e
            
    except Exception as e:
        print(f"添加明星失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stars/<star_id>', methods=['DELETE'])
def delete_star(star_id):
    """删除明星及其相关数据"""
    try:
        current_user_id = session.get('user_id')  # 从Flask session获取用户ID
        if not current_user_id:
            return jsonify({'error': '未登录'}), 401
            
        # 1. 获取要删除的明星信息
        star = g.db.query(Celebrity).filter(Celebrity.weibo_id == str(star_id)).first()
        if not star:
            return jsonify({'error': '明星不存在'}), 404
            
        # 2. 删除与该明星相关的所有数据
        # 2.1 获取相关的微博ID
        post_ids = [p.post_id for p in g.db.query(Post.post_id).filter(Post.celebrity_id == star.weibo_id).all()]
        
        if post_ids:
            # 2.2 获取相关的评论ID
            comment_ids = [c.comment_id for c in g.db.query(Comment.comment_id).filter(Comment.post_id.in_(post_ids)).all()]
            
            if comment_ids:
                # 2.3 删除评论相关的情感分析数据
                g.db.query(SentimentForComment).filter(SentimentForComment.comment_id.in_(comment_ids)).delete(synchronize_session=False)
            
            # 2.4 删除微博相关的情感分析数据
            g.db.query(SentimentForPost).filter(SentimentForPost.post_id.in_(post_ids)).delete(synchronize_session=False)
            
            # 2.5 删除评论数据
            g.db.query(Comment).filter(Comment.post_id.in_(post_ids)).delete(synchronize_session=False)
            
            # 2.6 删除微博数据
            g.db.query(Post).filter(Post.post_id.in_(post_ids)).delete(synchronize_session=False)
        
        # 2.7 删除热度数据
        g.db.query(HeatData).filter(HeatData.celebrity_id == star.weibo_id).delete(synchronize_session=False)
        
        # 2.8 删除黑粉分析数据
        g.db.query(BlackFanAnalysis).filter(BlackFanAnalysis.celebrity_id == star.weibo_id).delete(synchronize_session=False)
        
        # 2.9 删除黑粉数据
        g.db.query(BlackFan).filter(BlackFan.celebrity_id == star.weibo_id).delete(synchronize_session=False)
        
        # 2.10 删除用户-明星关联
        g.db.query(UserCelebrity).filter(UserCelebrity.celebrity_id == star.weibo_id).delete(synchronize_session=False)
        
        # 2.11 最后删除明星记录
        g.db.delete(star)
        
        # 提交事务
        g.db.commit()
        
        return jsonify({'message': '明星数据已成功删除'})
        
    except Exception as e:
        print(f"删除明星数据失败: {str(e)}")
        g.db.rollback()  # 发生错误时回滚事务
        return jsonify({'error': str(e)}), 500

@app.route('/api/stars/<int:star_id>', methods=['GET'])
def get_star_data(star_id):
    try:
        for star in stars_data:
            if star['id'] == star_id:
                return jsonify(star)
        return jsonify({'error': '未找到该明星'}), 404
    except Exception as e:
        return jsonify({'error': f'获取数据失败：{str(e)}'}), 500

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        # 清除session中的用户信息
        session.pop('user_id', None)
        session.pop('username', None)
        return jsonify({
            'status': 'success',
            'message': '登出成功'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'登出失败：{str(e)}'
        }), 500

# 获取明星基本信息
@app.route('/api/stars/<star_id>/basic')
def get_star_basic(star_id):
    try:
        star = Session.query(Celebrity).filter(Celebrity.weibo_id == star_id).first()
        if not star:
            return jsonify({'error': '明星不存在'}), 404
            
        # 获取黑粉数量
        black_fan_count = Session.query(BlackFan).filter(
            BlackFan.celebrity_id == star_id
        ).count()
        
        # 获取平均情感分数
        avg_sentiment = Session.query(
            func.avg(Post.sentiment_score)
        ).filter(
            Post.celebrity_id == star_id,
            Post.is_deleted == 0
        ).scalar() or 0.0
            
        return jsonify({
            'name': star.name,
            'weibo_url': f'https://weibo.com/u/{star.weibo_id}',
            'status': '正常',
            'introduction': f'微博粉丝数：{star.fans_count}',
            'fans_count': star.fans_count,
            'post_count': star.post_count,
            'black_fan_count': black_fan_count,
            'sentiment_score': round(float(avg_sentiment), 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 获取明星情感分析数据
@app.route('/api/stars/<star_id>/sentiment')
def get_star_sentiment(star_id):
    try:
        # 获取最近30天的情感分析数据
        sentiment_data = Session.query(SentimentForPost).join(Post).filter(
            Post.celebrity_id == star_id,
            Post.created_at >= datetime.now() - timedelta(days=30),
            Post.is_deleted == 0
        ).all()
        
        # 统计情感分布
        positive_count = sum(1 for s in sentiment_data if s.sentiment_category == 'positive')
        neutral_count = sum(1 for s in sentiment_data if s.sentiment_category == 'neutral')
        negative_count = sum(1 for s in sentiment_data if s.sentiment_category == 'negative')
        
        # 获取情感趋势
        trend_data = Session.query(
            func.date(Post.created_at).label('date'),
            func.avg(Post.sentiment_score).label('score')
        ).filter(
            Post.celebrity_id == star_id,
            Post.created_at >= datetime.now() - timedelta(days=30),
            Post.is_deleted == 0
        ).group_by(func.date(Post.created_at)).all()
        
        return jsonify({
            'positive_count': positive_count,
            'neutral_count': neutral_count,
            'negative_count': negative_count,
            'trend_dates': [str(d.date) for d in trend_data],
            'trend_scores': [float(d.score) for d in trend_data]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 获取明星黑粉分析数据
@app.route('/api/stars/<star_id>/hater')
def get_star_hater(star_id):
    try:
        # 获取黑粉分析数据
        black_fan_data = Session.query(BlackFanAnalysis).filter(
            BlackFanAnalysis.celebrity_id == star_id
        ).order_by(BlackFanAnalysis.analysis_time.desc()).first()
        
        if not black_fan_data:
            return jsonify({
                'total_count': 0,
                'active_count': 0,
                'growth_rate': 0,
                'influence_score': 0,
                'warnings': [],
                'activity_trend': {'dates': [], 'values': []},
                'sentiment_analysis': [0, 0, 0],
                'location_distribution': {}
            })
            
        analysis_results = json.loads(black_fan_data.analysis_results)
        
        return jsonify({
            'total_count': analysis_results.get('total_count', 0),
            'active_count': analysis_results.get('active_count', 0),
            'growth_rate': analysis_results.get('growth_rate', 0),
            'influence_score': analysis_results.get('influence_score', 0),
            'warnings': analysis_results.get('warnings', []),
            'activity_trend': analysis_results.get('activity_trend', {'dates': [], 'values': []}),
            'sentiment_analysis': analysis_results.get('sentiment_analysis', [0, 0, 0]),
            'location_distribution': analysis_results.get('location_distribution', {})
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 获取明星热度分析数据
@app.route('/api/stars/<star_id>/heat')
def get_star_heat(star_id):
    try:
        # 获取最近30天的热度数据
        heat_data = Session.query(HeatData).filter(
            HeatData.celebrity_id == star_id,
            HeatData.date >= datetime.now().date() - timedelta(days=30)
        ).order_by(HeatData.date).all()
        
        # 获取互动数据
        interaction_data = Session.query(
            func.sum(Post.comments_count).label('comment_count'),
            func.sum(Post.likes).label('like_count'),
            func.sum(Post.reposts).label('repost_count')
        ).filter(
            Post.celebrity_id == star_id,
            Post.created_at >= datetime.now() - timedelta(days=30),
            Post.is_deleted == 0
        ).first()
        
        return jsonify({
            'dates': [str(h.date) for h in heat_data],
            'heat_scores': [float(h.total_heat) for h in heat_data],
            'comment_count': int(interaction_data.comment_count or 0),
            'like_count': int(interaction_data.like_count or 0),
            'repost_count': int(interaction_data.repost_count or 0)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 