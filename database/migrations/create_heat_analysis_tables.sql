-- 热度分析结果表
CREATE TABLE IF NOT EXISTS heat_analysis_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    celebrity_id INT,
    topic VARCHAR(255),
    total_heat FLOAT,
    average_heat FLOAT,
    heat_distribution JSON,
    heat_trend JSON,
    created_at DATETIME,
    FOREIGN KEY (celebrity_id) REFERENCES celebrities(id)
);

-- 热度分析微博表
CREATE TABLE IF NOT EXISTS heat_analysis_posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    analysis_id INT,
    post_id INT,
    content TEXT,
    heat FLOAT,
    created_at DATETIME,
    FOREIGN KEY (analysis_id) REFERENCES heat_analysis_results(id),
    FOREIGN KEY (post_id) REFERENCES posts(id)
);

-- 创建索引
CREATE INDEX idx_heat_analysis_celebrity ON heat_analysis_results(celebrity_id);
CREATE INDEX idx_heat_analysis_topic ON heat_analysis_results(topic);
CREATE INDEX idx_heat_analysis_created_at ON heat_analysis_results(created_at);
CREATE INDEX idx_heat_analysis_posts_analysis ON heat_analysis_posts(analysis_id);
CREATE INDEX idx_heat_analysis_posts_post ON heat_analysis_posts(post_id); 