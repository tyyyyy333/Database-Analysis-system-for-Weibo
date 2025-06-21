# MyWeibo Analysis 项目说明

## 注：所有功能实现均在myweibo_analysis_V2文件夹下，以下说明也均是基于myweibo_analysis_V2

## 项目结构

```
myweibo_analysis_V2/
├── app/                  # Web服务与前端
│   ├── api/              # Flask后端API蓝图
│   ├── css/              # 前端样式文件
│   ├── js/               # 前端JS脚本
│   ├── *.html            # 前端页面
│   ├── models.py         # Web端ORM模型
│   ├── server.py         # Web服务入口
│   └── requirements.txt  # Web端依赖
├── weibospider/          # 爬虫与数据导入
│   ├── spiders/          # Scrapy爬虫脚本
│   ├── output/           # 爬虫输出数据
│   ├── import_output_to_db.py # 数据导入数据库
│   ├── auto_spider.py    # 自动化爬虫调度
│   ├── models.py         # 爬虫端ORM模型
│   ├── config.py         # 爬虫数据库配置
│   └── ...               # 其他辅助脚本
├── create_tables.py      # 数据库建表入口
├── run_auto_spider.py    # 一键采集+入库自动化脚本
├── requirements.txt      # 全项目依赖
├── testdata.sql          # 导出的测试数据
└── README.md             # 项目说明文档
```

## 一、开发环境

- **操作系统**：Windows 10/11（推荐 Windows 10 及以上）
- **编程语言**：Python 3.12.11
- **依赖管理**：`pip`，依赖见 `app/requirements.txt`
- **数据库**：MySQL 8.0（需支持 utf8mb4 编码）
- **主要依赖包**：
  - Flask==2.0.1
  - Flask-SQLAlchemy==2.5.1
  - SQLAlchemy==1.4.23
  - PyMySQL==1.0.2
  - cryptography==3.4.7
  - 及 Scrapy、SnowNLP 等（爬虫和情感分析）

## 二、数据库初始化流程

1. **配置数据库连接**
   - 修改 `weibospider/config.py` 中的 `SQLALCHEMY_DATABASE_URI`，填入你的 MySQL 用户名、密码、主机、端口和数据库名。
   - 确保数据库已创建（如 `weibo`），并已授权用户访问。

2. **安装依赖**
   ```bash
   pip install -r app/requirements.txt
   ```

3. **初始化数据库表**
   - 在项目根目录下运行：
     ```bash
     python create_tables.py
     ```
   - 或直接运行：
     ```bash
     python weibospider/init_db.py
     ```
   - 成功后会看到所有表创建成功的提示。
   - 数据库建表语句见 `weibospider/models.py`

## 三、测试数据导入方法

1. **准备测试数据**
   - 将爬虫输出的 `.jsonl` 或 `.csv` 文件放入 `weibospider/output/` 目录。
   - 示例文件如：
     - `fan_*.jsonl`
     - `tweet_spider_by_keyword*.jsonl`
     - `user_spider_*.jsonl`
     - `tweet_spider_by_user_id*.jsonl`
     - `*_评论(Min版).csv`

2. **批量导入数据**
   - 在根目录运行：
     ```bash
     python weibospider/import_output_to_db.py
     ```
   - 脚本会自动识别 output 目录下的所有数据文件，批量导入到对应数据库表，并自动做情感分析等处理。

## 四、项目运行步骤与使用方法

### 1. 自动化爬虫采集
- 编辑 `weibospider/cookie.txt`，填写自己的cookie
- 编辑 `weibospider/weibo_user.txt`，每行填写"明星名 用户ID"，如：
  ```
  鞠婧祎 3669102477
  马嘉祺 1234567890
  ```
- 在根目录运行自动化爬虫：
  ```bash
  python run_auto_spider.py
  ```
- 脚本会自动调度爬虫、采集数据并导入数据库。

### 2. 启动 Web 服务
-  修改`app/config.py`，填入你的 MySQL 用户名、密码、主机、端口和数据库名。
- 进入 app 目录后运行：
  ```bash
  python server.py
  ```
- 默认会启动 Flask Web 服务，浏览器访问 http://localhost:5000

### 3. 访问与使用

- 访问首页、报表、明星详情等页面，进行数据分析与可视化。
- 可根据实际需求修改 `app/` 下的前端页面和后端接口。

---

## 五、导出的测试数据

- 见`testdata.sql`。

## 六、小组分工
- 滕勇功：前后端基本架构+部分功能代码
- 于尧：前后端基本架构
- 石乐涵：爬虫+部分功能代码
- 谭荔丹：爬虫数据入库+部分功能代码+所有前后端连接以及功能集成调试
