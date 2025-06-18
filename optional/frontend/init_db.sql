-- 使用数据库
USE weibo;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(512) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建用户关注明星表
CREATE TABLE IF NOT EXISTS user_stars (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    star_id VARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_star (user_id, star_id)
);

-- 创建微博用户表（如果还没有的话）
CREATE TABLE IF NOT EXISTS weibo_user (
    id VARCHAR(50) PRIMARY KEY,
    nick_name VARCHAR(100) NOT NULL,
    description TEXT,
    follower_count INT DEFAULT 0,
    friends_count INT DEFAULT 0,
    gender CHAR(1),
    location VARCHAR(100),
    profession VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
); 