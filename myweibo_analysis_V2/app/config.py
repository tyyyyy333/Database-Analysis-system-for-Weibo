class Config:
    SECRET_KEY = '12345'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@localhost:3306/dbname?charset=utf8mb4' # 将password换为你自己的密码，dbname换为你自己的数据库名称
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 可根据需要添加更多配置项 