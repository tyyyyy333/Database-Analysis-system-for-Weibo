import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any
import logging

class BlackFanAnalyzer:
    def __init__(self, db_utils):
        self.db_utils = db_utils
        self.logger = logging.getLogger(__name__)

    def analyze_black_fan_ranking(self, limit: int = 10) -> Dict[str, Any]:
        """
        分析黑粉排名（按评论数量、情感强度等）
        """
        try:
            query = """
            SELECT user_id, COUNT(*) as comment_count, AVG(sentiment_score) as avg_sentiment
            FROM comments
            WHERE is_black_fan = 1
            GROUP BY user_id
            ORDER BY comment_count DESC
            LIMIT %s
            """
            results = self.db_utils.execute_query(query, (limit,))
            return {"ranking": results}
        except Exception as e:
            self.logger.error(f"Error in analyze_black_fan_ranking: {e}")
            return {"ranking": []}

    def analyze_black_fan_location(self) -> Dict[str, Any]:
        """
        分析黑粉地域分布
        """
        try:
            query = """
            SELECT location, COUNT(*) as count
            FROM users
            WHERE user_id IN (SELECT DISTINCT user_id FROM comments WHERE is_black_fan = 1)
            GROUP BY location
            ORDER BY count DESC
            """
            results = self.db_utils.execute_query(query)
            return {"location_distribution": results}
        except Exception as e:
            self.logger.error(f"Error in analyze_black_fan_location: {e}")
            return {"location_distribution": []}

    def analyze_black_fan_gender(self) -> Dict[str, Any]:
        """
        分析黑粉性别比例
        """
        try:
            query = """
            SELECT gender, COUNT(*) as count
            FROM users
            WHERE user_id IN (SELECT DISTINCT user_id FROM comments WHERE is_black_fan = 1)
            GROUP BY gender
            """
            results = self.db_utils.execute_query(query)
            return {"gender_distribution": results}
        except Exception as e:
            self.logger.error(f"Error in analyze_black_fan_gender: {e}")
            return {"gender_distribution": []}

    def analyze_black_fan_activity(self) -> Dict[str, Any]:
        """
        分析黑粉活跃度（评论频率、时间分布等）
        """
        try:
            query = """
            SELECT DATE(created_at) as date, COUNT(*) as comment_count
            FROM comments
            WHERE is_black_fan = 1
            GROUP BY DATE(created_at)
            ORDER BY date
            """
            results = self.db_utils.execute_query(query)
            return {"activity_trend": results}
        except Exception as e:
            self.logger.error(f"Error in analyze_black_fan_activity: {e}")
            return {"activity_trend": []}

    def analyze_black_fan_content(self, limit: int = 10) -> Dict[str, Any]:
        """
        分析黑粉评论内容（关键词、情感强度等）
        """
        try:
            query = """
            SELECT content, sentiment_score
            FROM comments
            WHERE is_black_fan = 1
            ORDER BY sentiment_score ASC
            LIMIT %s
            """
            results = self.db_utils.execute_query(query, (limit,))
            return {"content_analysis": results}
        except Exception as e:
            self.logger.error(f"Error in analyze_black_fan_content: {e}")
            return {"content_analysis": []}

    def visualize_black_fan_ranking(self, data: Dict[str, Any], output_path: str) -> None:
        """
        可视化黑粉排名
        """
        try:
            df = pd.DataFrame(data["ranking"])
            plt.figure(figsize=(10, 6))
            sns.barplot(x="user_id", y="comment_count", data=df)
            plt.title("黑粉排名（按评论数量）")
            plt.xlabel("用户ID")
            plt.ylabel("评论数量")
            plt.savefig(output_path)
            plt.close()
        except Exception as e:
            self.logger.error(f"Error in visualize_black_fan_ranking: {e}")

    def visualize_black_fan_location(self, data: Dict[str, Any], output_path: str) -> None:
        """
        可视化黑粉地域分布
        """
        try:
            df = pd.DataFrame(data["location_distribution"])
            plt.figure(figsize=(12, 6))
            sns.barplot(x="location", y="count", data=df)
            plt.title("黑粉地域分布")
            plt.xlabel("地域")
            plt.ylabel("数量")
            plt.xticks(rotation=45)
            plt.savefig(output_path)
            plt.close()
        except Exception as e:
            self.logger.error(f"Error in visualize_black_fan_location: {e}")

    def visualize_black_fan_gender(self, data: Dict[str, Any], output_path: str) -> None:
        """
        可视化黑粉性别比例
        """
        try:
            df = pd.DataFrame(data["gender_distribution"])
            plt.figure(figsize=(8, 8))
            plt.pie(df["count"], labels=df["gender"], autopct="%1.1f%%")
            plt.title("黑粉性别比例")
            plt.savefig(output_path)
            plt.close()
        except Exception as e:
            self.logger.error(f"Error in visualize_black_fan_gender: {e}")

    def visualize_black_fan_activity(self, data: Dict[str, Any], output_path: str) -> None:
        """
        可视化黑粉活跃度趋势
        """
        try:
            df = pd.DataFrame(data["activity_trend"])
            plt.figure(figsize=(12, 6))
            sns.lineplot(x="date", y="comment_count", data=df)
            plt.title("黑粉活跃度趋势")
            plt.xlabel("日期")
            plt.ylabel("评论数量")
            plt.xticks(rotation=45)
            plt.savefig(output_path)
            plt.close()
        except Exception as e:
            self.logger.error(f"Error in visualize_black_fan_activity: {e}")

    def visualize_black_fan_content(self, data: Dict[str, Any], output_path: str) -> None:
        """
        可视化黑粉评论内容情感分布
        """
        try:
            df = pd.DataFrame(data["content_analysis"])
            plt.figure(figsize=(10, 6))
            sns.histplot(df["sentiment_score"], bins=20)
            plt.title("黑粉评论情感分布")
            plt.xlabel("情感得分")
            plt.ylabel("数量")
            plt.savefig(output_path)
            plt.close()
        except Exception as e:
            self.logger.error(f"Error in visualize_black_fan_content: {e}") 