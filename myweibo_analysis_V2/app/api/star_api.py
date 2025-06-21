from flask import Blueprint, request, jsonify, send_from_directory
from flask_login import login_required, current_user
from sqlalchemy import text, bindparam, func
from models import db, UserStar, WeiboUser, UserPost, WeiboFans, WeiboComments, KeywordPost, Report
from datetime import datetime
import logging

star_bp = Blueprint('star', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

@star_bp.route('/stars', methods=['GET'])
@login_required
def get_all_stars():
    try:
        user_stars = UserStar.query.filter_by(user_id=current_user.id).all()
        star_ids = [us.star_id for us in user_stars]
        if not star_ids:
            return jsonify({'status': 'success', 'stars': []})
        stars = WeiboUser.query.filter(WeiboUser.id.in_(star_ids)).all()
        stars_data = [{
            'id': s.id,
            'nick_name': s.nick_name,
            'description': s.description,
            'follower_count': s.follower_count,
            'friends_count': s.friends_count,
            'gender': s.gender,
            'location': s.location,
            'profession': s.profession
        } for s in stars]
        return jsonify({'status': 'success', 'stars': stars_data})
    except Exception as e:
        import traceback
        logger.error(f"获取明星列表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': '获取明星列表失败'}), 500

@star_bp.route('/stars/search', methods=['GET'])
def search_stars():
    try:
        name = request.args.get('name')
        if not name:
            return jsonify({'status': 'error', 'message': '请提供明星名称'})
        stars = WeiboUser.query.filter(WeiboUser.nick_name.like(f'%{name}%')).limit(10).all()
        star_list = [{
            'id': s.id,
            'nick_name': s.nick_name,
            'description': s.description,
            'follower_count': s.follower_count,
            'friends_count': s.friends_count,
            'gender': s.gender,
            'location': s.location,
            'profession': s.profession
        } for s in stars]
        return jsonify({'status': 'success', 'stars': star_list})
    except Exception as e:
        logger.error(f"搜索明星失败: {str(e)}")
        return jsonify({'status': 'error', 'message': '搜索明星失败'})

@star_bp.route('/stars', methods=['POST'])
@login_required
def save_star_config():
    try:
        data = request.get_json()
        star_id = data.get('id')
        if not star_id:
            return jsonify({'status': 'error', 'message': '明星ID不能为空'}), 400
        existing_star = UserStar.query.filter_by(user_id=current_user.id, star_id=star_id).first()
        if existing_star:
            return jsonify({'status': 'error', 'message': '已经关注该明星'}), 400
        star_info = WeiboUser.query.filter_by(id=star_id).first()
        if not star_info:
            return jsonify({'status': 'error', 'message': '未找到该明星'}), 404
        new_star = UserStar(user_id=current_user.id, star_id=star_id)
        db.session.add(new_star)
        db.session.commit()
        return jsonify({'status': 'success', 'message': '添加成功', 'star': {
                'id': star_info.id,
                'nick_name': star_info.nick_name,
                'description': star_info.description,
                'follower_count': star_info.follower_count,
                'friends_count': star_info.friends_count,
                'gender': star_info.gender,
                'location': star_info.location,
                'profession': star_info.profession
        }})
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加明星失败: {str(e)}")
        return jsonify({'status': 'error', 'message': '添加失败，请稍后重试'}), 500

@star_bp.route('/stars/<int:star_id>', methods=['DELETE'])
@login_required
def delete_star(star_id):
    try:
        user_star = UserStar.query.filter_by(user_id=current_user.id, star_id=star_id).first()
        if not user_star:
            return jsonify({'status': 'error', 'message': '未找到该明星'}), 404
        db.session.delete(user_star)
        db.session.commit()
        return jsonify({'status': 'success', 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除明星失败: {str(e)}")
        return jsonify({'status': 'error', 'message': '删除失败，请稍后重试'}), 500

@star_bp.route('/stars/<star_id>', methods=['GET'])
def get_star_data(star_id):
    try:
        star_info = WeiboUser.query.filter_by(id=star_id).first()
        if not star_info:
            return jsonify({'error': '未找到该明星'}), 404
        return jsonify({
            'id': star_info.id,
            'nick_name': star_info.nick_name,
            'description': star_info.description,
            'follower_count': star_info.follower_count,
            'friends_count': star_info.friends_count,
            'gender': star_info.gender,
            'location': star_info.location,
            'profession': star_info.profession
        })
    except Exception as e:
        logger.error(f"获取明星详情失败: {str(e)}")
        return jsonify({'error': f'获取数据失败：{str(e)}'}), 500

@star_bp.route('/stars/<star_id>/heat', methods=['GET'])
def get_star_heat(star_id):
    try:
        query = text("""
            SELECT DATE(created_at) as date, 
                   SUM(reposts_count) as reposts, 
                   SUM(comments_count) as comments, 
                   SUM(attitudes_count) as likes
            FROM user_post 
            WHERE user_id = :star_id 
            AND created_at >= DATE_SUB(NOW(), INTERVAL 10 DAY)
            GROUP BY DATE(created_at)
            ORDER BY date
        """).bindparams(bindparam('star_id', star_id))
        result = db.session.execute(query)
        heat_data = []
        for row in result:
            heat_score = row.reposts + row.comments + row.likes
            heat_data.append({
                'date': row.date.strftime('%Y-%m-%d'),
                'heat_score': heat_score
            })
        return jsonify({
            'status': 'success',
            'heat_data': heat_data
        })
    except Exception as e:
        logger.error(f"获取微博热度失败: {str(e)}")
        return jsonify({'status': 'error', 'message': '获取微博热度失败'}), 500

@star_bp.route('/stars/<star_id>/activity', methods=['GET'])
def get_star_activity(star_id):
    try:
        query = text("""
            SELECT 
                DATE(p.created_at) AS date,
                COUNT(c.mblog_id) AS comment_count,
                SUM(
                    CASE
                        WHEN c.fan_badge LIKE '铁粉%' THEN 1
                        WHEN c.fan_badge LIKE '金粉%' THEN 2
                        WHEN c.fan_badge LIKE '钻粉%' THEN 3
                        ELSE 0
                    END
                ) AS activity_score
            FROM user_post p
            LEFT JOIN weibo_comments c ON c.mblog_id = p.mblogid
            WHERE p.user_id = :star_id
              AND p.created_at >= DATE_SUB(NOW(), INTERVAL 10 DAY)
            GROUP BY DATE(p.created_at)
            ORDER BY date
        """)
        result = db.session.execute(query, {"star_id": str(star_id)})
        activity_data = []
        for row in result:
            activity_data.append({
                'date': row.date.strftime('%Y-%m-%d'),
                'comment_count': row.comment_count,
                'activity_score': row.activity_score or 0
            })
        return jsonify({
            'status': 'success',
            'activity_data': activity_data
        })
    except Exception as e:
        logger.error(f"获取粉丝活跃度失败: {str(e)}")
        return jsonify({'status': 'error', 'message': f'获取粉丝活跃度失败: {str(e)}'}), 500

@star_bp.route('/stars/<star_id>/gender', methods=['GET'])
def get_star_gender(star_id):
    try:
        gender_data = (db.session.query(WeiboFans.gender, func.count().label('count'))
            .filter(WeiboFans.follower_id == star_id, WeiboFans.gender.in_(['男', '女']))
            .group_by(WeiboFans.gender)
            .all())
        gender_data = [{'name': row.gender, 'value': row.count} for row in gender_data]
        return jsonify({'status': 'success', 'gender_data': gender_data})
    except Exception as e:
        logger.error(f"获取粉丝性别比例失败: {str(e)}")
        return jsonify({'status': 'error', 'message': '获取粉丝性别比例失败'}), 500

@star_bp.route('/stars/<star_id>/region', methods=['GET'])
def get_star_region(star_id):
    try:
        region_data = (db.session.query(WeiboFans.region, func.count().label('count'))
            .filter(WeiboFans.follower_id == star_id, WeiboFans.region.notin_(['其他', '海外']))
            .group_by(WeiboFans.region)
            .all())
        region_data = [{'name': row.region, 'value': row.count} for row in region_data if row.region is not None]
        return jsonify({'status': 'success', 'region_data': region_data})
    except Exception as e:
        logger.error(f"获取粉丝地域比例失败: {str(e)}")
        return jsonify({'status': 'error', 'message': '获取粉丝地域比例失败'}), 500

@star_bp.route('/stars/count', methods=['GET'])
@login_required
def get_stars_count():
    try:
        count = UserStar.query.filter_by(user_id=current_user.id).count()
        return jsonify({
            'status': 'success',
            'count': count
        })
    except Exception as e:
        logger.error(f"获取明星数量失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '获取明星数量失败'
        }), 500

@star_bp.route('/stars/<star_id>/negative_events', methods=['GET'])
def get_negative_events(star_id):
    try:
        result = (KeywordPost.query
            .filter(KeywordPost.keyword_id == star_id, KeywordPost.sentiment_score != 0)
            .order_by(KeywordPost.sentiment_score.asc())
            .limit(10)
            .all())
        events = [{
                'content': row.content,
                'sentiment_score': row.sentiment_score,
            'created_at': row.created_at.strftime('%Y-%m-%d %H:%M:%S') if row.created_at else None
        } for row in result]
        return jsonify({'status': 'success', 'events': events})
    except Exception as e:
        logger.error(f"获取负面事件失败: {str(e)}")
        return jsonify({'status': 'error', 'message': '获取负面事件失败'}), 500

@star_bp.route('/stars/<star_id>/popular_events', methods=['GET'])
def get_popular_events(star_id):
    try:
        result = (KeywordPost.query
            .filter(KeywordPost.keyword_id == star_id)
            .order_by(KeywordPost.attitudes_count.desc())
            .limit(5)
            .all())
        events = [{
                'content': row.content,
                'attitudes_count': row.attitudes_count,
            'created_at': row.created_at.strftime('%Y-%m-%d %H:%M:%S') if row.created_at else None
        } for row in result]
        return jsonify({'status': 'success', 'events': events})
    except Exception as e:
        logger.error(f"获取热门事件失败: {str(e)}")
        return jsonify({'status': 'error', 'message': '获取热门事件失败'}), 500

@star_bp.route('/stars/<star_id>/alert_count', methods=['GET'])
def get_alert_count(star_id):
    try:
        query = text("""
            WITH alert_count AS (
                SELECT COUNT(*) as alert_count
                FROM keyword_post 
                WHERE keyword_id = :star_id
                AND sentiment_score < 0.05
                AND sentiment_score != 0
            ),
            avg_sentiment AS (
                SELECT AVG(sentiment_score) as avg_sentiment
                FROM keyword_post 
                WHERE keyword_id = :star_id
                AND sentiment_score != 0
            )
            SELECT 
                ac.alert_count,
                COALESCE(avs.avg_sentiment, 0) as avg_sentiment
            FROM alert_count ac
            CROSS JOIN avg_sentiment avs
        """).bindparams(bindparam('star_id', star_id))
        result = db.session.execute(query)
        row = result.fetchone()
        avg_sentiment = row.avg_sentiment if row.avg_sentiment is not None else 0
        avg_sentiment_100 = avg_sentiment * 100
        return jsonify({
            'status': 'success',
            'alert_count': row.alert_count,
            'avg_sentiment': round(avg_sentiment_100, 1)
        })
    except Exception as e:
        logger.error(f"获取预警数失败: {str(e)}")
        return jsonify({'status': 'error', 'message': '获取预警数失败'}), 500

@star_bp.route('/stars/total_alerts', methods=['GET'])
@login_required
def get_total_alerts():
    try:
        logger.info(f"开始获取用户 {current_user.id} 的预警总数")
        query = text("""
            SELECT COUNT(*) as alert_count
            FROM keyword_post kp
            INNER JOIN user_stars us ON kp.keyword_id = us.star_id
            WHERE us.user_id = :user_id
            AND kp.sentiment_score < 0.05
            AND kp.sentiment_score != 0
        """).bindparams(bindparam('user_id', current_user.id))
        result = db.session.execute(query)
        row = result.fetchone()
        alert_count = row.alert_count if row else 0
        logger.info(f"用户 {current_user.id} 的预警总数: {alert_count}")
        return jsonify({
            'status': 'success',
            'alert_count': alert_count
        })
    except Exception as e:
        logger.error(f"获取总预警数失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '获取总预警数失败'
        }), 500

@star_bp.route('/stars/<star_id>/fan_demographics', methods=['GET'])
@login_required
def get_fan_demographics(star_id):
    try:
        logger.info(f"开始获取明星 {star_id} 的粉丝画像数据")
        gender_query = text("""
            SELECT 
                CASE 
                    WHEN gender = '男' THEN '男'
                    WHEN gender = '女' THEN '女'
                    ELSE '未知'
                END as gender,
                COUNT(*) as count
            FROM weibo_fans
            WHERE follower_id = :star_id
            GROUP BY gender
        """).bindparams(bindparam('star_id', star_id))
        region_query = text("""
            SELECT 
                CASE 
                    WHEN region LIKE '%北京%' THEN '北京'
                    WHEN region LIKE '%江苏%' THEN '江苏'
                    WHEN region LIKE '%广东%' THEN '广东'
                    WHEN region = '其他' OR region = '海外' THEN NULL
                    ELSE region
                END as region,
                COUNT(*) as count
            FROM weibo_fans
            WHERE follower_id = :star_id
            AND region NOT IN ('其他', '海外')
            GROUP BY 
                CASE 
                    WHEN region LIKE '%北京%' THEN '北京'
                    WHEN region LIKE '%江苏%' THEN '江苏'
                    WHEN region LIKE '%广东%' THEN '广东'
                    WHEN region = '其他' OR region = '海外' THEN NULL
                    ELSE region
                END
            ORDER BY count DESC
            LIMIT 10
        """).bindparams(bindparam('star_id', star_id))
        gender_result = db.session.execute(gender_query)
        region_result = db.session.execute(region_query)
        gender_data = [{'name': row.gender, 'value': row.count} for row in gender_result]
        region_data = [{'name': row.region, 'value': row.count} for row in region_result if row.region is not None]
        logger.info(f"获取到性别数据: {gender_data}")
        logger.info(f"获取到地域数据: {region_data}")
        return jsonify({
            'status': 'success',
            'gender_data': gender_data,
            'region_data': region_data
        })
    except Exception as e:
        logger.error(f"获取粉丝画像数据失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '获取粉丝画像数据失败'
        }), 500

@star_bp.route('/stars/low_sentiment', methods=['GET'])
@login_required
def get_low_sentiment_stars():
    try:
        query = text("""
            SELECT DISTINCT w.id, w.nick_name, 
                   AVG(kp.sentiment_score) * 100 as avg_sentiment
            FROM weibo_user w
            INNER JOIN user_stars us ON w.id = us.star_id
            INNER JOIN keyword_post kp ON w.id = kp.keyword_id
            WHERE us.user_id = :user_id 
            AND kp.sentiment_score > 0
            GROUP BY w.id, w.nick_name
            HAVING AVG(kp.sentiment_score) * 100 < 65
            ORDER BY avg_sentiment ASC
            LIMIT 10
        """).bindparams(bindparam('user_id', current_user.id))
        result = db.session.execute(query)
        low_sentiment_stars = []
        for row in result:
            low_sentiment_stars.append({
                'star_id': row.id,
                'star_name': row.nick_name,
                'avg_sentiment': round(row.avg_sentiment, 2)
            })
        return jsonify({
            'status': 'success',
            'stars': low_sentiment_stars
        })
    except Exception as e:
        logger.error(f"获取低情感得分明星失败: {str(e)}")
        return jsonify({'status': 'error', 'message': '获取低情感得分明星失败'}), 500 