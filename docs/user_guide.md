# 微博舆情分析系统使用指南

## 1. 系统概述

本系统是一个基于Python的微博舆情分析系统，主要功能包括：
- 数据采集：自动采集微博数据
- 数据清洗：对采集的数据进行清洗和预处理
- 情感分析：分析微博内容的情感倾向
- 热度分析：计算微博内容的热度
- 预警监控：监控异常舆情
- 黑粉识别：识别和分析黑粉行为
- 报告生成：生成分析报告

## 2. 系统架构

### 2.1 系统调用链
```
main.py (主程序)
├── 初始化系统
│   ├── 加载配置 (config.py)
│   ├── 初始化日志 (utils/logger.py)
│   ├── 初始化数据库连接 (utils/db_utils.py)
│   └── 初始化Redis连接 (utils/redis_utils.py)
│
├── 启动定时任务
│   ├── 数据采集任务 (datacrawl/crawler.py)
│   ├── 数据清洗任务 (data_processing/data_cleaner.py)
│   ├── 情感分析任务 (sentiment/sentiment_analyzer.py)
│   ├── 热度分析任务 (analysis/heat_analyzer.py)
│   ├── 预警检查任务 (analysis/alert_checker.py)
│   ├── 黑粉分析任务 (analysis/black_fan_analyzer.py)
│   └── 报告生成任务 (report/report_generator.py)
│
└── 启动Web服务
    └── API接口 (api/app.py)
```

### 2.2 数据流转过程
```
数据采集 (crawler.py)
    ↓
数据清洗 (data_cleaner.py)
    ↓
情感分析 (sentiment_analyzer.py)
    ↓
热度分析 (heat_analyzer.py)
    ↓
预警检查 (alert_checker.py)
    ↓
黑粉分析 (black_fan_analyzer.py)
    ↓
报告生成 (report_generator.py)
```

### 2.3 报告生成流程
```
report_generator.py
├── 数据收集 (data_collector.py)
│   ├── 热度数据
│   ├── 情感数据
│   ├── 预警数据
│   ├── 黑粉数据
│   └── 典型评论
│
├── 图表生成 (chart_generator.py)
│   ├── 热度趋势图
│   ├── 情感分布图
│   ├── 预警统计图
│   ├── 热度箱线图
│   └── 话题热度图
│
├── 预测分析 (prediction_model.py)
│   ├── 热度预测
│   ├── 情感预测
│   └── 预警预测
│
└── 报告发送 (report_sender.py)
    ├── 邮件发送
    ├── 状态更新
    └── 发送记录
```

### 2.4 数据库表关系
```
weibo_posts
    ↓
weibo_comments
    ↓
sentiment_analysis
    ↓
heat_analysis
    ↓
alert_records
    ↓
black_fan_analysis
    ↓
report_records
```

### 2.5 API接口结构
```
api/app.py
├── 数据查询接口
│   ├── 舆情概览
│   ├── 情感分析
│   ├── 热度分析
│   ├── 预警信息
│   └── 黑粉分析
│
├── 报告管理接口
│   ├── 模板管理
│   ├── 报告生成
│   ├── 报告查询
│   └── 发送管理
│
└── 系统管理接口
    ├── 用户管理
    ├── 配置管理
    └── 日志查询
```

## 2. 环境要求

- Python 3.8+
- MySQL 5.7+
- Redis 6.0+
- 其他依赖包（见requirements.txt）

## 3. 安装部署

### 3.1 克隆代码
```bash
git clone [项目地址]
cd [项目目录]
```

### 3.2 安装依赖
```bash
pip install -r requirements.txt
```

### 3.3 配置数据库
1. 创建MySQL数据库
2. 执行数据库迁移脚本：
```bash
mysql -u [用户名] -p [数据库名] < database/migrations/create_tables.sql
mysql -u [用户名] -p [数据库名] < database/migrations/create_report_tables.sql
```

### 3.4 配置系统
1. 复制配置文件模板：
```bash
cp config/config.example.py config/config.py
```

2. 修改配置文件：
- 数据库连接信息
- Redis连接信息
- 微博API配置
- 邮件服务器配置
- 其他系统参数

## 4. 使用说明

### 4.1 启动系统
```bash
python main.py
```

### 4.2 数据采集
1. 配置采集任务：
   - 在`config/config.py`中设置采集参数
   - 配置采集频率和范围
   - 设置代理IP池（如需要）

2. 启动采集：
   - 系统会自动按配置的时间间隔进行数据采集
   - 可以在日志中查看采集状态

### 4.3 查看分析结果
1. 访问Web界面：
   - 打开浏览器访问：http://localhost:5000
   - 使用配置的管理员账号登录

2. 查看数据：
   - 舆情概览
   - 情感分析
   - 热度分析
   - 预警信息
   - 黑粉分析

### 4.4 报告管理
1. 配置报告模板：
   - 在Web界面中配置报告模板
   - 设置报告类型（日报/周报/月报）
   - 配置报告内容

2. 配置报告接收人：
   - 添加报告接收人信息
   - 设置接收频率
   - 配置接收方式（邮件/短信）

3. 查看报告：
   - 在Web界面查看历史报告
   - 下载报告文件
   - 查看报告发送状态

## 5. 注意事项

### 5.1 数据采集
- 遵守微博的爬虫规则
- 合理设置采集频率
- 注意IP限制问题
- 定期检查采集状态

### 5.2 系统维护
- 定期备份数据库
- 监控系统资源使用
- 检查日志文件
- 更新系统配置

### 5.3 性能优化
- 根据数据量调整数据库配置
- 优化采集策略
- 调整分析参数
- 合理设置预警阈值

## 6. 常见问题

### 6.1 数据采集问题
Q: 采集速度很慢怎么办？
A: 检查网络连接，调整采集频率，使用代理IP

Q: 采集数据不完整怎么办？
A: 检查采集配置，查看错误日志，调整重试策略

### 6.2 系统运行问题
Q: 系统启动失败怎么办？
A: 检查配置文件，查看错误日志，确认依赖安装

Q: 内存占用过高怎么办？
A: 调整数据库配置，优化查询语句，增加内存限制

### 6.3 报告生成问题
Q: 报告未按时生成怎么办？
A: 检查定时任务配置，查看任务日志，确认模板配置

Q: 报告发送失败怎么办？
A: 检查邮件服务器配置，确认接收人信息，查看发送日志

## 7. 联系支持

如遇到问题，请通过以下方式获取支持：
- 提交Issue
- 发送邮件至：[支持邮箱]
- 查看在线文档：[文档地址]

## 8. 更新日志

### v1.0.0 (2024-03-xx)
- 初始版本发布
- 实现基础功能
- 完成系统框架

### 待开发功能
- 数据采集模块优化
- 前端界面完善
- 性能优化
- 更多分析模型 