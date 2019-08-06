from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import redis
from flask_wtf import CSRFProtect
from flask_session import Session
from flask_script import Manager
from flask_migrate import Migrate,MigrateCommand
"""
入口程序


"""
class Config(object):
    # 开启调试模式
    DEGUBG = True
    # 设置数据库的链接地址
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/information_20'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 设置redis的主机和端口号
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    # 设置秘钥
    SECRET_KEY = 'fjlakdjflaksjfl'
    # 把session存储到redis里面
    SESSION_TYPE = 'redis'
    # 使用session的签名
    SESSION_USE_SIGNER = True
    SESSION_REDIS =  redis.StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
    # 设置session的有效期 ,单位秒,有效期可以随意设置
    SESSION_PERMANENT = 86400 * 2



app = Flask(__name__)
# 加载配置文件
app.config.from_object(Config)
# 创建数据库对象,一定要注意上面加载配置文件和数据库的代码顺序不能混淆
db = SQLAlchemy(app)
# 创建redis对象(用来存储验证码,图片验证码和短信验证码)
redis_store =  redis.StrictRedis(host=Config.REDIS_HOST,port=Config.REDIS_PORT)
# 开启CSRF保护,避免视图函数受到攻击
CSRFProtect(app)
# 开启session
Session(app)
# 把app交给manager进行管理
manager = Manager(app)
# 创建数据库的迁移框架
Migrate(app,db)
# 添加迁移数据库框架的脚本
manager.add_command('xxx',MigrateCommand)

@app.route("/")
def index():
    return 'index222'

if __name__ == '__main__':
    manager.run()