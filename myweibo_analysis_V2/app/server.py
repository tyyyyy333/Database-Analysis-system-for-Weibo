from flask import Flask, send_from_directory, render_template, jsonify, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
import json
from datetime import datetime
from models import db, User, Report, UserStar, WeiboUser, UserPost, WeiboFans, WeiboComments, KeywordPost
import logging
import mysql.connector
from sqlalchemy import text, bindparam
from sqlalchemy.sql import func
from api import user_bp, star_bp, report_bp
from config import Config

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
    static_folder='.',
    template_folder='.'
)
app.config.from_object(Config)

# 初始化数据库
db.init_app(app)

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 创建数据库表
with app.app_context():
    try:
        db.create_all()
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库表创建失败: {str(e)}")

# 使用内存存储明星数据
stars_data = []
next_id = 1

@app.route('/')
def index():
    return redirect(url_for('index_home'))

@app.route('/index_home')
def index_home():
    return send_from_directory('.', 'index_home.html')

@app.route('/login')
def login_page():
    return send_from_directory('.', 'index.html')

@app.route('/home')
@login_required
def home():
    return send_from_directory('.', 'home.html')

@app.route('/star/config')
@login_required
def star_config():
    return send_from_directory('.', 'star_config.html')

@app.route('/star/<star_id>')
@login_required
def star_detail(star_id):
    return send_from_directory('.', 'star_detail.html')

@app.route('/star_dashboard')
@login_required
def star_dashboard():
    import os; print(os.path.abspath('../frontend/star_dashboard.html'))
    return send_from_directory('.', 'star_dashboard.html')

@app.route('/settings')
@login_required
def system_settings():
    return send_from_directory('.', 'system_settings.html')

@app.route('/report_dashboard')
@login_required
def report_dashboard():
    return send_from_directory('.', 'report_dashboard.html')

@app.route('/report_detail')
@login_required
def report_detail():
    return send_from_directory('.', 'report_detail.html')


@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# 在文件开头的数据库初始化部分添加时区设置
# 找到数据库初始化代码，添加以下内容：

# 设置数据库时区
def init_db():
    with app.app_context():
        db.session.execute(text("SET time_zone = '+08:00'"))
        db.session.commit()

# 在应用启动时调用
if __name__ == '__main__':
    init_db()
    app.register_blueprint(user_bp)
    app.register_blueprint(star_bp)
    app.register_blueprint(report_bp)
    app.run(debug=True, port=5000) 