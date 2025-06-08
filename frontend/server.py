from flask import Flask, send_from_directory, render_template, jsonify, request, redirect, url_for
import os
import json
from datetime import datetime

app = Flask(__name__, 
    static_folder='.',
    template_folder='.'
)

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
def home():
    return send_from_directory('.', 'home.html')

@app.route('/star/config')
def star_config():
    return send_from_directory('.', 'star_config.html')

@app.route('/star/<star_id>')
def star_detail(star_id):
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
    
    if username and password:
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': '登录失败'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username and password:
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': '注册失败'}), 400

@app.route('/api/stars', methods=['GET'])
def get_all_stars():
    return jsonify(stars_data)

@app.route('/api/stars', methods=['POST'])
def save_star_config():
    global next_id
    try:
        data = request.get_json()
        name = data.get('name')
        url = data.get('url')
        introduction = data.get('introduction', '')
        
        if not name or not url:
            return jsonify({'error': '名称和URL不能为空'}), 400
            
        # 创建新明星数据
        new_star = {
            'id': next_id,
            'name': name,
            'url': url,
            'introduction': introduction,
            'status': '正常',
            'fans': 0,
            'topics': 0,
            'alert_count': 0,
            'sentiment_score': 0,
            'events': []
        }
        
        stars_data.append(new_star)
        next_id += 1
        
        return jsonify({'message': '添加成功', 'id': new_star['id']})
    except Exception as e:
        return jsonify({'error': f'添加失败：{str(e)}'}), 500

@app.route('/api/stars/<int:star_id>', methods=['DELETE'])
def delete_star(star_id):
    global stars_data
    try:
        # 找到要删除的明星
        star_to_delete = None
        for star in stars_data:
            if star['id'] == star_id:
                star_to_delete = star
                break
                
        if not star_to_delete:
            return jsonify({'error': '未找到该明星'}), 404
            
        # 从列表中移除
        stars_data.remove(star_to_delete)
        return jsonify({'message': '删除成功'})
    except Exception as e:
        return jsonify({'error': f'删除失败：{str(e)}'}), 500

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

if __name__ == '__main__':
    app.run(debug=True, port=5000) 