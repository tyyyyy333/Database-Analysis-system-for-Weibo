-- 情感分析结果表
CREATE TABLE IF NOT EXISTS sentiment_analysis_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    celebrity_id INT,
    post_id INT,
    sentiment_distribution JSON,
    average_sentiment FLOAT,
    sentiment_trend JSON,
    black_fan_ratio FLOAT,
    created_at DATETIME,
    FOREIGN KEY (celebrity_id) REFERENCES celebrities(id),
    FOREIGN KEY (post_id) REFERENCES posts(id)
);

-- 情感分析评论表
CREATE TABLE IF NOT EXISTS sentiment_analysis_comments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    analysis_id BIGINT,
    comment_content TEXT,
    user_nickname VARCHAR(100),
    sentiment VARCHAR(20),
    strength FLOAT,
    created_at DATETIME,
    is_positive BOOLEAN,
    FOREIGN KEY (analysis_id) REFERENCES sentiment_analysis_results(id)
);

-- 创建索引
CREATE INDEX idx_sentiment_analysis_celebrity ON sentiment_analysis_results(celebrity_id);
CREATE INDEX idx_sentiment_analysis_post ON sentiment_analysis_results(post_id);
CREATE INDEX idx_sentiment_analysis_created_at ON sentiment_analysis_results(created_at);
CREATE INDEX idx_sentiment_comments_analysis ON sentiment_analysis_comments(analysis_id); 