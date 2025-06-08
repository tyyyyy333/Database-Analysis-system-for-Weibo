-- 报告模板表
CREATE TABLE report_templates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    template_name VARCHAR(100) NOT NULL COMMENT '模板名称',
    report_type ENUM('daily', 'weekly', 'monthly') NOT NULL COMMENT '报告类型',
    content TEXT NOT NULL COMMENT '模板内容',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_template_type (report_type),
    INDEX idx_template_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报告模板表';

-- 报告记录表
CREATE TABLE report_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    template_id INT NOT NULL COMMENT '模板ID',
    report_time DATETIME NOT NULL COMMENT '报告时间',
    content TEXT NOT NULL COMMENT '报告内容',
    data JSON COMMENT '报告数据',
    charts JSON COMMENT '图表数据',
    predictions JSON COMMENT '预测数据',
    status ENUM('pending', 'generated', 'sent', 'failed') DEFAULT 'pending' COMMENT '报告状态',
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES report_templates(id),
    INDEX idx_report_time (report_time),
    INDEX idx_report_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报告记录表';

-- 报告接收人表
CREATE TABLE report_recipients (
    id INT PRIMARY KEY AUTO_INCREMENT,
    template_id INT NOT NULL COMMENT '模板ID',
    name VARCHAR(50) NOT NULL COMMENT '接收人姓名',
    email VARCHAR(100) NOT NULL COMMENT '邮箱地址',
    phone VARCHAR(20) COMMENT '手机号码',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES report_templates(id),
    INDEX idx_recipient_template (template_id),
    INDEX idx_recipient_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报告接收人表';

-- 报告发送日志表
CREATE TABLE report_send_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    report_id INT NOT NULL COMMENT '报告ID',
    recipient_id INT NOT NULL COMMENT '接收人ID',
    send_time DATETIME NOT NULL COMMENT '发送时间',
    send_status ENUM('success', 'failed') NOT NULL COMMENT '发送状态',
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES report_records(id),
    FOREIGN KEY (recipient_id) REFERENCES report_recipients(id),
    INDEX idx_send_report (report_id),
    INDEX idx_send_time (send_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报告发送日志表';

-- 报告生成任务表
CREATE TABLE report_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    template_id INT NOT NULL COMMENT '模板ID',
    task_name VARCHAR(100) NOT NULL COMMENT '任务名称',
    schedule_type ENUM('daily', 'weekly', 'monthly') NOT NULL COMMENT '调度类型',
    schedule_time TIME NOT NULL COMMENT '调度时间',
    schedule_day INT COMMENT '调度日期（周几或每月几号）',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    last_run_time DATETIME COMMENT '上次运行时间',
    next_run_time DATETIME COMMENT '下次运行时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES report_templates(id),
    INDEX idx_task_schedule (schedule_type, schedule_time),
    INDEX idx_task_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报告生成任务表';

-- 报告生成日志表
CREATE TABLE report_task_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_id INT NOT NULL COMMENT '任务ID',
    report_id INT COMMENT '生成的报告ID',
    start_time DATETIME NOT NULL COMMENT '开始时间',
    end_time DATETIME COMMENT '结束时间',
    status ENUM('success', 'failed') NOT NULL COMMENT '执行状态',
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES report_tasks(id),
    FOREIGN KEY (report_id) REFERENCES report_records(id),
    INDEX idx_task_log_task (task_id),
    INDEX idx_task_log_time (start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报告生成日志表'; 