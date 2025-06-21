from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import text, bindparam
from models import db, Report
import logging

report_bp = Blueprint('report', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

# 这里补充迁移所有报告相关API（如获取报告列表、创建、删除、下载、详情、统计等）
# 请将server.py中所有以 /api/reports 和 /api/report_detail 开头的接口迁移到此处，并用@report_bp.route装饰 

@report_bp.route('/reports', methods=['GET'])
@login_required
def get_reports():
    try:
        query = text("""
            SELECT r.user_id, r.star_id, r.create_date, r.follower_count, r.following_count, 
                   r.hot_weibo, r.comments, r.bad_content, w.nick_name as star_nick_name
            FROM report r
            LEFT JOIN weibo_user w ON r.star_id = w.id
            WHERE r.user_id = :user_id
            ORDER BY r.create_date DESC
        """).bindparams(bindparam('user_id', current_user.id))
        result = db.session.execute(query)
        reports = []
        for row in result:
            reports.append({
                'user_id': row.user_id,
                'star_id': row.star_id,
                'star_nick_name': row.star_nick_name,
                'create_date': row.create_date.isoformat() if row.create_date else None,
                'follower_count': row.follower_count,
                'following_count': row.following_count,
                'hot_weibo': row.hot_weibo,
                'comments': row.comments,
                'bad_content': row.bad_content
            })
        return jsonify({'status': 'success', 'reports': reports})
    except Exception as e:
        logger.error(f"获取报告列表失败: {str(e)}")
        return jsonify({'status': 'error', 'message': '获取报告列表失败'}), 500

@report_bp.route('/reports', methods=['POST'])
@login_required
def create_report():
    try:
        data = request.get_json()
        star_id = data.get('star_id')
        if not star_id:
            return jsonify({'status': 'error', 'message': '明星ID不能为空'}), 400
        existing_report = Report.query.filter_by(user_id=current_user.id, star_id=star_id).first()
        if existing_report:
            return jsonify({'status': 'error', 'message': '该明星已在您的关注列表中'}), 400
        query = text("""
            SELECT id, nick_name, follower_count, friends_count, description
            FROM weibo_user 
            WHERE id = :star_id
        """).bindparams(bindparam('star_id', star_id))
        result = db.session.execute(query)
        star = result.fetchone()
        if not star:
            return jsonify({'status': 'error', 'message': '明星不存在'}), 404
        hot_weibo_query = text("""
            SELECT content, mblogid, attitudes_count
            FROM user_post 
            WHERE user_id = :star_id 
            ORDER BY attitudes_count DESC 
            LIMIT 1
        """).bindparams(bindparam('star_id', star_id))
        hot_weibo_result = db.session.execute(hot_weibo_query)
        hot_weibo = hot_weibo_result.fetchone()
        comments = []
        if hot_weibo:
            comments_query = text("""
                SELECT user_id, content, likes
                FROM weibo_comments 
                WHERE mblog_id = :mblog_id 
                ORDER BY likes DESC 
                LIMIT 5
            """).bindparams(bindparam('mblog_id', hot_weibo.mblogid))
            comments_result = db.session.execute(comments_query)
            comments = [{
                'user_id': row.user_id,
                'content': row.content,
                'likes': row.likes
            } for row in comments_result]
        bad_content_query = text("""
            SELECT content, sentiment_score * 100 as sentiment_score, keyword_id
            FROM keyword_post 
            WHERE keyword_id = :star_id 
            AND sentiment_score > 0
            ORDER BY sentiment_score ASC 
            LIMIT 5
        """).bindparams(bindparam('star_id', star_id))
        bad_content_result = db.session.execute(bad_content_query)
        bad_content = [{
            'content': row.content,
            'sentiment_score': round(row.sentiment_score, 2),
            'keyword_id': row.keyword_id
        } for row in bad_content_result]
        report = Report(
            user_id=current_user.id,
            star_id=star_id,
            follower_count=star.follower_count,
            following_count=star.friends_count,
            hot_weibo=hot_weibo.content if hot_weibo else '',
            comments=comments,
            bad_content=bad_content
        )
        db.session.add(report)
        db.session.commit()
        logger.info(f"用户 {current_user.username} 创建报告: {star.nick_name}")
        return jsonify({'status': 'success', 'message': '报告创建成功', 'report': report.to_dict()})
    except Exception as e:
        logger.error(f"创建报告失败: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'创建报告失败：{str(e)}'}), 500

@report_bp.route('/reports/<star_id>', methods=['DELETE'])
@login_required
def delete_report(star_id):
    try:
        report = Report.query.filter_by(user_id=current_user.id, star_id=star_id).first()
        if not report:
            return jsonify({'status': 'error', 'message': '报告不存在'}), 404
        db.session.delete(report)
        db.session.commit()
        logger.info(f"用户 {current_user.username} 删除报告: {star_id}")
        return jsonify({'status': 'success', 'message': '报告删除成功'})
    except Exception as e:
        logger.error(f"删除报告失败: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'删除报告失败：{str(e)}'}), 500

@report_bp.route('/reports/<star_id>/download', methods=['GET'])
@login_required
def download_report(star_id):
    try:
        report = Report.query.filter_by(user_id=current_user.id, star_id=star_id).first()
        if not report:
            return jsonify({'status': 'error', 'message': '报告不存在'}), 404
        logger.info(f"用户 {current_user.username} 下载报告: {star_id}")
        return jsonify({'status': 'success', 'message': '报告下载成功'})
    except Exception as e:
        logger.error(f"下载报告失败: {str(e)}")
        return jsonify({'status': 'error', 'message': f'下载报告失败：{str(e)}'}), 500

@report_bp.route('/report_detail/<star_id>')
@login_required
def get_report_detail(star_id):
    try:
        report_query = text("""
            SELECT r.user_id, r.star_id, r.create_date, r.follower_count, r.following_count, 
                   r.hot_weibo, r.comments, r.bad_content, w.nick_name as star_nick_name
            FROM report r
            LEFT JOIN weibo_user w ON r.star_id = w.id
            WHERE r.user_id = :user_id AND r.star_id = :star_id
        """).bindparams(bindparam('user_id', current_user.id), bindparam('star_id', star_id))
        result = db.session.execute(report_query)
        report_row = result.fetchone()
        if not report_row:
            return jsonify({'status': 'error', 'message': '报告不存在'}), 404
        hot_weibo_query = text("""
            SELECT content, mblogid, attitudes_count
            FROM user_post 
            WHERE user_id = :star_id 
            ORDER BY attitudes_count DESC 
            LIMIT 1
        """).bindparams(bindparam('star_id', star_id))
        hot_weibo_result = db.session.execute(hot_weibo_query)
        hot_weibo = hot_weibo_result.fetchone()
        comments = []
        if hot_weibo:
            comments_query = text("""
                SELECT user_id, content, likes
                FROM weibo_comments 
                WHERE mblog_id = :mblog_id 
                ORDER BY likes DESC 
                LIMIT 5
            """).bindparams(bindparam('mblog_id', hot_weibo.mblogid))
            comments_result = db.session.execute(comments_query)
            comments = [{
                'user_id': row.user_id,
                'content': row.content,
                'likes': row.likes
            } for row in comments_result]
        bad_content_query = text("""
            SELECT content, sentiment_score * 100 as sentiment_score, keyword_id
            FROM keyword_post 
            WHERE keyword_id = :star_id 
            AND sentiment_score > 0
            ORDER BY sentiment_score ASC 
            LIMIT 5
        """).bindparams(bindparam('star_id', star_id))
        bad_content_result = db.session.execute(bad_content_query)
        bad_content = [{
            'content': row.content,
            'sentiment_score': round(row.sentiment_score, 2),
            'keyword_id': row.keyword_id
        } for row in bad_content_result]
        report_data = {
            'user_id': report_row.user_id,
            'star_id': report_row.star_id,
            'star_nick_name': report_row.star_nick_name,
            'create_date': report_row.create_date.isoformat() if report_row.create_date else None,
            'follower_count': report_row.follower_count,
            'following_count': report_row.following_count,
            'hot_weibo': hot_weibo.content if hot_weibo else None,
            'hot_weibo_mblogid': hot_weibo.mblogid if hot_weibo else None,
            'hot_weibo_attitudes': hot_weibo.attitudes_count if hot_weibo else None,
            'comments': comments,
            'bad_content': bad_content
        }
        return jsonify({'status': 'success', 'report': report_data})
    except Exception as e:
        logger.error(f"获取报告详情失败: {str(e)}")
        return jsonify({'status': 'error', 'message': f'获取报告详情失败：{str(e)}'}), 500

@report_bp.route('/reports/count', methods=['GET'])
@login_required
def get_reports_count():
    try:
        query = text("""
            SELECT COUNT(*) as count
            FROM report
            WHERE user_id = :user_id
        """).bindparams(bindparam('user_id', current_user.id))
        result = db.session.execute(query)
        count = result.fetchone().count
        return jsonify({'status': 'success', 'count': count})
    except Exception as e:
        logger.error(f"获取报告数量失败: {str(e)}")
        return jsonify({'status': 'error', 'message': '获取报告数量失败'}), 500 