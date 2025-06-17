-- 预警规则表
CREATE TABLE IF NOT EXISTS alert_rules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    rule_name VARCHAR(100),
    alert_level ENUM('high', 'medium', 'low'),
    heat_threshold FLOAT,
    duration_hours INT,
    message_template TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    updated_at DATETIME
);

-- 预警通知配置表
CREATE TABLE IF NOT EXISTS alert_notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    rule_id INT,
    notification_type ENUM('email', 'sms', 'webhook'),
    notification_config JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (rule_id) REFERENCES alert_rules(id)
);

-- 预警处理记录表
CREATE TABLE IF NOT EXISTS alert_handlings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    alert_id INT,
    handler_id INT,
    status ENUM('pending', 'processing', 'resolved', 'ignored'),
    handling_notes TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (alert_id) REFERENCES heat_alerts(id),
    FOREIGN KEY (handler_id) REFERENCES users(id)
);

-- 监控对象表
CREATE TABLE IF NOT EXISTS monitoring_targets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    target_type ENUM('celebrity', 'topic'),
    target_id INT,
    priority ENUM('high', 'medium', 'low'),
    monitoring_keywords TEXT,
    start_time DATETIME,
    end_time DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    updated_at DATETIME
);

-- 创建索引
CREATE INDEX idx_alert_rules_level ON alert_rules(alert_level);
CREATE INDEX idx_alert_rules_active ON alert_rules(is_active);
CREATE INDEX idx_alert_notifications_rule ON alert_notifications(rule_id);
CREATE INDEX idx_alert_notifications_type ON alert_notifications(notification_type);
CREATE INDEX idx_alert_handlings_alert ON alert_handlings(alert_id);
CREATE INDEX idx_alert_handlings_status ON alert_handlings(status);
CREATE INDEX idx_monitoring_targets_type ON monitoring_targets(target_type);
CREATE INDEX idx_monitoring_targets_active ON monitoring_targets(is_active); 
 
 