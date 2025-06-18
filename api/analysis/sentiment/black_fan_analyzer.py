import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
import numpy as np

class BlackFanAnalyzer:
    """黑粉分析器，用于分析黑粉群体的特征"""
    
    def __init__(self, db_url: str):
        """初始化黑粉分析器
        
        Args:
            db_url: 数据库连接URL
        """
        self.logger = logging.getLogger(__name__)
        self.engine = create_engine(db_url)
        self.timewindow = 7
        # 创建保存目录
        self.save_dir = os.path.join('static', 'analysis', 'black_fans')
        os.makedirs(self.save_dir, exist_ok=True)
        
        # 确保分析结果表存在
        self._ensure_analysis_table()
        
    def _ensure_analysis_table(self) -> None:
        """确保分析结果表存在"""
        try:
            with self.engine.connect() as conn:
                # 检查表是否存在
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='black_fan_analysis';
                """)).scalar()
                
                if not result:
                    # 创建表
                    conn.execute(text("""
                        CREATE TABLE black_fan_analysis (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            celebrity_id VARCHAR(50) NOT NULL,
                            analysis_time TIMESTAMP NOT NULL,
                            analysis_results TEXT NOT NULL,
                            FOREIGN KEY (celebrity_id) REFERENCES celebrity(weibo_id)
                        )
                    """))
                    conn.commit()
                    self.logger.info("创建black_fan_analysis表成功")
                    
        except Exception as e:
            # 如果表不存在，会抛出异常，此时创建表
            if "no such table" in str(e):
                with self.engine.connect() as conn:
                    conn.execute(text("""
                        CREATE TABLE black_fan_analysis (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            celebrity_id VARCHAR(50) NOT NULL,
                            analysis_time TIMESTAMP NOT NULL,
                            analysis_results TEXT NOT NULL,
                            FOREIGN KEY (celebrity_id) REFERENCES celebrity(weibo_id)
                        )
                    """))
                    conn.commit()
                    self.logger.info("创建black_fan_analysis表成功")
            else:
                self.logger.error(f"创建black_fan_analysis表失败: {str(e)}")

    def analyze_black_fans(self, celebrity_id: int) -> Dict[str, Any]:
        """分析指定明星的黑粉群体
        
        Args:
            celebrity_id: 明星ID
            
        Returns:
            Dict: 分析结果
        """
        try:
            # 1. 获取黑粉数据
            black_fans = self._get_black_fans(celebrity_id)
            if not black_fans:
                return {
                    "status": "error",
                    "message": "未找到黑粉数据"
                }
                
            # 2. 分析黑粉特征
            analysis_results = {
                "total_count": len(black_fans),
                "score_distribution": self._analyze_score_distribution(black_fans),
                "activity_analysis": self._analyze_activity(black_fans),
                "top_black_fans": self._get_top_black_fans(black_fans),
                "trend_analysis": self._analyze_trend(black_fans),
                "gender_distribution": self._analyze_gender_distribution(black_fans),
                "location_distribution": self._analyze_location_distribution(black_fans),
                "time_distribution": self._analyze_time_distribution(black_fans),
                "sentiment_trend": self._analyze_sentiment_trend(black_fans),
                "risk_level": self._analyze_risk_level(black_fans)
            }
            
            # 3. 保存分析结果
            self._save_analysis_results(analysis_results, celebrity_id)
            
            return {
                "status": "success",
                "data": analysis_results
            }
            
        except Exception as e:
            self.logger.error(f"黑粉分析失败: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    def _get_black_fans(self, celebrity_id: int) -> List[Dict]:
        """获取黑粉数据
        
        Args:
            celebrity_id: 明星ID
            
        Returns:
            List[Dict]: 黑粉数据列表
        """
        
        query = """
            SELECT bf.*, wu.nickname, wu.gender, wu.location
            FROM black_fans bf
            JOIN weibo_users wu ON bf.user_id = wu.weibo_id
            WHERE bf.celebrity_id = :celebrity_id
            ORDER BY bf.black_fan_score DESC
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(
                text(query),
                {'celebrity_id': celebrity_id}
            ).fetchall()
            
        return [dict(row) for row in result]
        
    def _analyze_score_distribution(self, black_fans: List[Dict]) -> Dict[str, Any]:
        """分析黑粉分数分布
        
        Args:
            black_fans: 黑粉数据列表
            
        Returns:
            Dict: 分数分布分析结果
        """
        scores = [bf['black_fan_score'] for bf in black_fans]
        
        return {
            "mean": sum(scores) / len(scores),
            "median": sorted(scores)[len(scores) // 2],
            "max": max(scores),
            "min": min(scores),
            "distribution": {
                "high": len([s for s in scores if s >= 0.8]),
                "medium": len([s for s in scores if 0.5 <= s < 0.8]),
                "low": len([s for s in scores if s < 0.5])
            }
        }

    def _analyze_activity(self, black_fans: List[Dict]) -> Dict[str, Any]:
        """分析黑粉活跃度
        
        Args:
            black_fans: 黑粉数据列表
            
        Returns:
            Dict: 活跃度分析结果
        """
        comment_counts = [bf['comment_count'] for bf in black_fans]
        
        # 计算活跃度等级
        activity_levels = {
            "very_active": len([c for c in comment_counts if c >= 50]),  # 评论数 >= 50
            "active": len([c for c in comment_counts if 20 <= c < 50]),  # 评论数 20-49
            "inactive": len([c for c in comment_counts if c < 20])       # 评论数 < 20
        }
        
        # 计算活跃度分数 (0-1)
        max_comments = max(comment_counts) if comment_counts else 0
        activity_scores = [count / max_comments if max_comments > 0 else 0 for count in comment_counts]
        
        return {
            "levels": activity_levels,
            "average_activity": float(np.mean(activity_scores)),
            "activity_metrics": {
                "total_comments": sum(comment_counts),
                "average_comments": float(np.mean(comment_counts)),
                "median_comments": float(np.median(comment_counts)),
                "max_comments": max(comment_counts) if comment_counts else 0,
                "min_comments": min(comment_counts) if comment_counts else 0
            },
            "activity_distribution": {
                "bins": [0, 10, 20, 50, 100, float('inf')],
                "counts": np.histogram(comment_counts, bins=[0, 10, 20, 50, 100, float('inf')])[0].tolist()
            }
        }

    def _get_top_black_fans(self, black_fans: List[Dict], limit: int = 20) -> List[Dict]:
        """获取最活跃的黑粉
        
        Args:
            black_fans: 黑粉数据列表
            limit: 返回数量限制
            
        Returns:
            List[Dict]: 最活跃的黑粉列表
        """
        return sorted(
            black_fans,
            key=lambda x: (x['black_fan_score'], x['comment_count']),
            reverse=True
        )[:limit]
        
    def _analyze_trend(self, black_fans: List[Dict]) -> List[Dict]:
        """分析黑粉趋势
        
        Args:
            black_fans: 黑粉数据列表
            
        Returns:
            List[Dict]: 趋势数据
        """
        # 按最后活跃时间分组统计
        trend_data = []
        for days in range(self.timewindow, 0, -1):
            date = datetime.now() - timedelta(days=days)
            count = len([
                bf for bf in black_fans
                if bf['last_active'].date() == date.date()
            ])
            trend_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "count": count
            })
            
        return trend_data
        
    def _analyze_gender_distribution(self, black_fans: List[Dict]) -> Dict[str, int]:
        """分析黑粉性别分布
        
        Args:
            black_fans: 黑粉数据列表
            
        Returns:
            Dict[str, int]: 性别分布数据
        """
        gender_counts = {}
        for bf in black_fans:
            gender = bf['gender'] or 'unknown'
            gender_counts[gender] = gender_counts.get(gender, 0) + 1
        return gender_counts
        
    def _analyze_location_distribution(self, black_fans: List[Dict]) -> Dict[str, int]:
        """分析黑粉地域分布
        
        Args:
            black_fans: 黑粉数据列表
            
        Returns:
            Dict[str, int]: 地域分布数据
        """
        location_counts = {}
        for bf in black_fans:
            location = bf['location'] or 'unknown'
            location_counts[location] = location_counts.get(location, 0) + 1
        return location_counts
        
    def _analyze_time_distribution(self, black_fans: List[Dict]) -> Dict[str, Any]:
        """分析黑粉活跃时间分布
        
        Args:
            black_fans: 黑粉数据列表
            
        Returns:
            Dict: 时间分布分析结果
        """
        hour_distribution = {i: 0 for i in range(24)}
        weekday_distribution = {i: 0 for i in range(7)}
        
        for bf in black_fans:
            hour = bf['last_active'].hour
            weekday = bf['last_active'].weekday()
            hour_distribution[hour] += 1
            weekday_distribution[weekday] += 1
            
        return {
            "hour_distribution": [
                {"hour": hour, "count": count}
                for hour, count in hour_distribution.items()
            ],
            "weekday_distribution": [
                {"weekday": weekday, "count": count}
                for weekday, count in weekday_distribution.items()
            ]
        }
        
    
    def _analyze_sentiment_trend(self, black_fans: List[Dict]) -> List[Dict]:
        """分析情感趋势
        
        Args:
            black_fans: 黑粉数据列表
            
        Returns:
            List[Dict]: 情感趋势数据
        """
        # 这里需要从评论表中获取情感数据
        query = """
            SELECT DATE(c.created_at) as date,
                   AVG(c.sentiment_score) as avg_sentiment,
                   COUNT(*) as comment_count
            FROM comments c
            WHERE c.user_id IN :user_ids
            GROUP BY DATE(c.created_at)
            ORDER BY date DESC
            LIMIT 30
        """
        
        user_ids = [bf['user_id'] for bf in black_fans]
        
        with self.engine.connect() as conn:
            result = conn.execute(
                text(query),
                {'user_ids': tuple(user_ids)}
            ).fetchall()
            
        return [
            {
                "date": row['date'].strftime("%Y-%m-%d"),
                "avg_sentiment": float(row['avg_sentiment']),
                "comment_count": row['comment_count']
            }
            for row in result
        ]
        
    def _analyze_risk_level(self, black_fans: List[Dict]) -> Dict[str, Any]:
        """分析风险等级
        
        Args:
            black_fans: 黑粉数据列表
            
        Returns:
            Dict: 风险等级分析结果
        """
        risk_scores = []
        for bf in black_fans:
            # 计算综合风险分数
            score = (
                bf['black_fan_score'] * 0.4 +  # 黑粉分数权重
                (bf['comment_count'] / 100) * 0.3 +  # 评论频率权重
                (1 / (datetime.now() - bf['last_active']).days if (datetime.now() - bf['last_active']).days > 0 else 1) * 0.3  # 活跃度权重
            )
            risk_scores.append(score)
            
        risk_levels = {
            "high": len([s for s in risk_scores if s >= 0.8]),
            "medium": len([s for s in risk_scores if 0.5 <= s < 0.8]),
            "low": len([s for s in risk_scores if s < 0.5])
        }
        
        return {
            "risk_levels": risk_levels,
            "average_risk": float(np.mean(risk_scores)),
            "risk_distribution": {
                "bins": [0, 0.2, 0.4, 0.6, 0.8, 1.0],
                "counts": np.histogram(risk_scores, bins=5)[0].tolist()
            }
        }
        
    def _save_analysis_results(self, analysis_results: Dict[str, Any], celebrity_id: int) -> None:
        """保存分析结果
        
        Args:
            analysis_results: 分析结果
            celebrity_id: 明星ID
        """
        try:
            # 准备保存数据
            save_data = {
                'celebrity_id': celebrity_id,
                'analysis_time': datetime.now().isoformat(),
                'results': analysis_results
            }
            
            # 保存到JSON文件
            save_path = os.path.join(self.save_dir, f'analysis_{celebrity_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
                
            # 保存到数据库
            with self.engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO black_fan_analysis 
                        (celebrity_id, analysis_time, analysis_results)
                        VALUES 
                        (:celebrity_id, :analysis_time, :analysis_results)
                    """),
                    {
                        'celebrity_id': celebrity_id,
                        'analysis_time': datetime.now(),
                        'analysis_results': json.dumps(analysis_results)
                    }
                )
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"保存分析结果失败: {str(e)}")
 
 