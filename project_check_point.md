# 项目功能检查点（Project Check Point）

本文件用于细致记录本项目每个文件的功能、主要函数、已实现与待实现的功能，以及各模块之间的关联。

---

## 目录结构与模块说明

（1）config/ 配置模块
（2）database/ 数据库模型与工具
（3）datacrawl/ 数据采集与清洗
（4）data_processing/ 数据预处理
（5）sentiment/ 情感分析
（6）analysis/ 热度与可视化分析
（7）report/ 报告生成与发送
（8）ai_analysis/ 智能分析
（9）api/ 后端接口
（10）utils/ 工具类
（11）templates/ 报告模板
（12）docs/ 文档

---

## 1. config/ 配置模块
### report_config.py
- **功能**：统一管理数据库、SMTP、报告、预测、图表、日志、定时任务等配置。
- **主要函数**：
  - `get_config()`：获取完整配置字典。
- **已实现**：全部配置项及环境变量支持。
- **待实现**：无。

### settings.py
- **功能**：系统全局设置。
- **主要函数**：配置常量、路径等。
- **已实现**：基础配置。
- **待实现**：如需支持多环境切换，可扩展。

---

## 2. database/ 数据库模型与工具
### models.py
- **功能**：ORM模型定义（明星、微博、评论、用户、话题等）。
- **主要函数/类**：
  - 各表ORM类（Celebrity, Post, Comment, User, Topic等）
- **已实现**：基础表结构、关系映射。
- **待实现**：如需支持更多分析结果表，可扩展。

### db_utils.py
- **功能**：数据库连接与操作工具。
- **主要函数/类**：
  - `DatabaseUtils`：连接、查询、事务管理等。
- **已实现**：基本操作。
- **待实现**：批量导入、复杂事务支持。

### migrations/
- **功能**：数据库表结构迁移SQL。
- **主要文件**：
  - `create_report_tables.sql`：报告相关表
  - `create_alert_management_tables.sql`：预警相关表
  - `create_sentiment_analysis_tables.sql`：情感分析表
  - `create_heat_analysis_tables.sql`：热度分析表
- **已实现**：表结构定义。
- **待实现**：如需新表，需补充。

---

## 3. datacrawl/ 数据采集与清洗
### crawler.py
- **功能**：微博等平台数据采集（待实现）。
- **主要函数**：采集主流程、调度、异常处理。
- **已实现**：文件已创建。
- **待实现**：采集逻辑、接口、调度。

---

## 4. data_processing/ 数据预处理
### data_cleaner.py
- **功能**：评论、用户、微博等数据清洗、无效评论过滤、时间格式化、BERT语义判断。
- **主要函数/类**：
  - `DataCleaner`：
    - `clean_comment`：清洗单条评论
    - `is_meaningful_comment`：判断评论有效性
    - `format_timestamp`：时间标准化
    - `clean_user_data`/`clean_post_data`/`clean_comment_data`：批量清洗
- **已实现**：全部核心清洗逻辑。
- **待实现**：如需支持更多平台或自定义规则可扩展。

---

## 5. sentiment/ 情感分析
### sentiment_analyzer.py
- **功能**：基于BERT的情感分类、黑粉识别、情感强度计算。
- **主要函数/类**：
  - `SentimentAnalyzer`：
    - `analyze_sentiment`：文本情感分析
    - `analyze_black_fan`：黑粉识别
    - `analyze_public_opinion`：舆论水平分析
- **已实现**：情感分析、黑粉识别、可视化集成。
- **待实现**：模型优化、批量分析、结果导出。

### black_fan_analyzer.py
- **功能**：黑粉数据分析与可视化（黑粉排名、地域分布、性别比例等）。
- **主要函数/类**：
  - `BlackFanAnalyzer`：
    - `analyze_black_fan_ranking`：黑粉排名分析
    - `analyze_black_fan_location`：黑粉地域分布分析
    - `analyze_black_fan_gender`：黑粉性别比例分析
- **已实现**：黑粉排名、地域、性别分析。
- **待实现**：更多黑粉特征分析、可视化图表。

---

## 6. analysis/ 热度与可视化分析
### heat_analyzer.py
- **功能**：微博/明星/话题热度计算、趋势分析、预警。
- **主要函数/类**：
  - `HeatAnalyzer`：
    - `calculate_post_heat`/`calculate_celebrity_heat`/`analyze_topic_heat`
- **已实现**：热度计算、趋势分析。
- **待实现**：多平台热度、预测。

### heat_visualizer.py
- **功能**：热度相关图表生成。
- **主要函数**：趋势图、分布图等。
- **已实现**：部分图表。
- **待实现**：更多可视化类型。

### heat_alerter.py
- **功能**：热度预警推送。
- **主要函数**：预警检测、推送。
- **已实现**：文件已创建。
- **待实现**：逻辑实现。

### sentiment_visualizer.py
- **功能**：情感分析结果可视化。
- **主要函数**：饼图、折线图等。
- **已实现**：文件已创建。
- **待实现**：逻辑实现。

---

## 7. report/ 报告生成与发送
### report_generator.py
- **功能**：集成数据采集、图表、预测、发送，自动生成报告。
- **主要函数/类**：
  - `ReportGenerator`：
    - `generate_report`：生成并发送报告
    - `_collect_report_data`/`_generate_charts`/`_generate_predictions` 等
- **已实现**：主流程、集成各子模块。
- **待实现**：多模板、多格式支持。

### report_sender.py
- **功能**：报告邮件发送、状态记录。
- **主要函数/类**：
  - `ReportSender`：
    - `send_report`：发送报告
- **已实现**：邮件发送、日志。
- **待实现**：多渠道推送。

### report_scheduler.py
- **功能**：定时任务调度。
- **主要函数/类**：
  - `ReportScheduler`：
    - `start`/`stop`/`generate_report_now`
- **已实现**：定时调度。
- **待实现**：任务监控、失败重试。

### data_collector.py
- **功能**：报告数据采集。
- **主要函数/类**：
  - `ReportDataCollector`：
    - `collect_heat_data`/`collect_sentiment_data`/`collect_alert_data` 等
- **已实现**：数据采集。
- **待实现**：多平台、多维度。

### chart_generator.py
- **功能**：报告图表生成。
- **主要函数/类**：
  - `ChartGenerator`：
    - `generate_heat_trend_chart`/`generate_sentiment_distribution_chart` 等
- **已实现**：部分图表。
- **待实现**：更多图表类型。

### prediction_model.py
- **功能**：热度/情感趋势预测。
- **主要函数/类**：
  - `PredictionModel`：
    - `predict_heat_trend`/`predict_sentiment_trend`/`predict_alert_probability`
- **已实现**：基础预测。
- **待实现**：模型优化、深度学习。

---

## 8. ai_analysis/ 智能分析
### ai_analyzer.py
- **功能**：AI大模型分析、自然语言问答。
- **主要函数/类**：
  - `AIAnalyzer`：
    - `analyze_trend`/`analyze_sentiment`/`analyze_fans`/`compare_celebrities`
- **已实现**：智能分析主流程。
- **待实现**：知识库集成、上下文记忆。

### chat_interface.py
- **功能**：Streamlit聊天界面。
- **主要函数/类**：
  - `ChatInterface`：
    - `run`/`_parse_user_input`/`_generate_response`
- **已实现**：基本聊天与分析。
- **待实现**：多轮对话、权限管理。

---

## 9. api/ 后端接口
### alert_management.py
- **功能**：预警管理API。
- **主要接口**：规则、通知、处理、监控对象、统计等RESTful接口。
- **已实现**：接口定义。
- **待实现**：权限、接口测试。

---

## 10. utils/ 工具类
### scheduler.py
- **功能**：通用定时任务工具。
- **主要函数**：任务调度、定时执行。
- **已实现**：基础调度。
- **待实现**：任务监控。

### email_sender.py
- **功能**：邮件发送工具。
- **主要函数**：邮件发送。
- **已实现**：文件已创建。
- **待实现**：逻辑实现。

---

## 11. templates/ 报告模板
### daily.html/weekly.html/monthly.html
- **功能**：日报、周报、月报HTML模板。
- **已实现**：模板结构与样式。
- **待实现**：自定义模板、富文本。

---

## 12. docs/ 文档
### TODO.md
- **功能**：开发任务清单。
- **已实现**：任务分解。
- **待实现**：持续更新。

---

## 13. models/ 模型管理
### model_manager.py
- **功能**：本地/远程模型统一管理。
- **主要函数/类**：
  - `ModelManager`：模型加载、缓存、版本管理。
- **已实现**：基础管理。
- **待实现**：多模型、自动清理。

---

# 模块间关联与主程序设计建议
- 数据采集（datacrawl）→ 数据清洗（data_processing）→ 数据入库（database）
- 数据分析（sentiment/analysis/ai_analysis）→ 结果存储（database）→ 可视化与报告（report/templates）
- 预警与报告（analysis/report/api）→ 通知推送（utils）
- 主程序建议以调度/定时任务为入口，串联各模块自动化运行

---

# 系统运行流程与模块合作说明
1. **数据采集阶段**  
   - `datacrawl/crawler.py` 负责从微博等平台采集数据，调用 `data_processing/data_cleaner.py` 进行数据清洗，清洗后的数据通过 `database/db_utils.py` 存入数据库。

2. **数据分析阶段**  
   - `sentiment/sentiment_analyzer.py` 对评论进行情感分析，识别黑粉，并调用 `sentiment/black_fan_analyzer.py` 进行黑粉排名、地域、性别等分析。
   - `analysis/heat_analyzer.py` 计算热度，`analysis/heat_visualizer.py` 生成热度图表，`analysis/heat_alerter.py` 进行预警推送。

3. **报告生成阶段**  
   - `report/report_generator.py` 集成数据采集、图表生成、预测模型，调用 `report/data_collector.py` 获取数据，`report/chart_generator.py` 生成图表，`report/prediction_model.py` 进行趋势预测，最终通过 `report/report_sender.py` 发送报告。

4. **定时任务与调度**  
   - `report/report_scheduler.py` 负责定时调度报告生成任务，调用 `utils/scheduler.py` 进行任务管理。

5. **前端与用户交互**  
   - 前端通过 `api/alert_management.py` 等接口与后端交互，展示数据可视化结果，管理预警规则，查看报告等。

---

如需细化到每个函数的参数、返回值和调用关系，可进一步补充。请确认本结构是否满足你的需求，或指定需要更详细的部分！ 