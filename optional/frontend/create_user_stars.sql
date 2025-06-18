USE weibo;

CREATE TABLE IF NOT EXISTS user_stars (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    star_id VARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_star (user_id, star_id)
); 