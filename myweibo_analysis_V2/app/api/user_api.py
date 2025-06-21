from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from models import db, User
import logging

user_bp = Blueprint('user', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'status': 'error', 'message': '用户名和密码不能为空'}), 400
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)
        user.last_login = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'success', 'user': user.to_dict()})
    return jsonify({'status': 'error', 'message': '用户名或密码错误'}), 401

@user_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        logger.debug(f"注册请求数据: {data}")
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        if not username or not password or not email:
            logger.warning("注册失败：缺少必要字段")
            return jsonify({'status': 'error', 'message': '所有字段都是必填的'}), 400
        if User.query.filter_by(username=username).first():
            logger.warning(f"注册失败：用户名 {username} 已存在")
            return jsonify({'status': 'error', 'message': '用户名已存在'}), 400
        if User.query.filter_by(email=email).first():
            logger.warning(f"注册失败：邮箱 {email} 已被注册")
            return jsonify({'status': 'error', 'message': '邮箱已被注册'}), 400
        user = User(username=username, email=email)
        user.set_password(password)
        try:
            db.session.add(user)
            db.session.commit()
            logger.info(f"用户 {username} 注册成功")
            login_user(user)
            return jsonify({'status': 'success', 'user': user.to_dict()})
        except Exception as e:
            db.session.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            return jsonify({'status': 'error', 'message': f'注册失败：{str(e)}'}), 500
    except Exception as e:
        logger.error(f"注册过程发生错误: {str(e)}")
        return jsonify({'status': 'error', 'message': f'注册失败：{str(e)}'}), 500

@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'status': 'success'})

@user_bp.route('/user')
@login_required
def get_current_user():
    return jsonify(current_user.to_dict())

@user_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    try:
        data = request.get_json()
        username = data.get('username')
        new_password = data.get('password')
        if not username or not new_password:
            return jsonify({'status': 'error', 'message': '用户名和新密码不能为空'}), 400
        if username != current_user.username:
            return jsonify({'status': 'error', 'message': '用户名与当前登录用户不匹配'}), 400
        current_user.set_password(new_password)
        db.session.commit()
        logger.info(f"用户 {username} 密码修改成功")
        return jsonify({'status': 'success', 'message': '密码修改成功'})
    except Exception as e:
        logger.error(f"密码修改失败: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'密码修改失败：{str(e)}'}), 500 