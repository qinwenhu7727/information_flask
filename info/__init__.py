import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask import g
from flask import render_template

from config import Config,DevelopementConfig,ProdutionConfig,config_map

from flask_sqlalchemy import SQLAlchemy

import redis

from flask_wtf import CSRFProtect

from flask_session import Session
# 生成一个CSRF_token
from flask_wtf.csrf import generate_csrf


# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG) # 调试debug级
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日志记录器
logging.getLogger().addHandler(file_log_handler)

# 创建数据库对象,一定要注意上面加载配置文件和数据库的代码顺序不能混淆
db = SQLAlchemy()
# 创建一个默认值叫做redis用来存储验证码
redis_store = None # type: redis.StrictRedis

def create_app(config_name):

    app = Flask(__name__)

    # 获取配置文件里面的key
    name =  config_map.get(config_name)
    # 加载配置文件DevelopementConfig,ProdutionConfig
    app.config.from_object(name)
    # 初始化
    db.init_app(app)
    # 创建redis对象(用来存储验证码,图片验证码和短信验证码)
    global redis_store
    redis_store =  redis.StrictRedis(host=name.REDIS_HOST,port=name.REDIS_PORT,decode_responses=True)

    # 开启CSRF保护,避免视图函数受到攻击
    CSRFProtect(app)
    # 开启session
    Session(app)

    @app.after_request
    def after_request(response):
        # 创建一个CSRF_Token
        csrf_token =  generate_csrf()
        # 往浏览器客户端写一个CSRF_token
        response.set_cookie('csrf_token',csrf_token)
        return response


    from info.utils.common import user_login_data
    @app.errorhandler(404)
    @user_login_data
    def error_404_handler(error):
        user = g.user

        data = {
            "user_info": user.to_dict() if user else None,

        }
        return render_template('news/404.html', data=data)

    # 注册自定义过滤器
    from info.utils.common import do_class_index
    # 添加一个模板过滤器
    # 第一个参数表示函数的名字
    # 第二个参数表示过滤器的名字
    app.add_template_filter(do_class_index,'indexClass')

    # 首页
    from info.index import index_blue
    app.register_blueprint(index_blue)

    # 登陆注册
    from info.passport import passport_blue
    app.register_blueprint(passport_blue)

    # 新闻详情
    from info.news import news_blue
    app.register_blueprint(news_blue)

    # 个人中心
    from info.user import profile_blue
    app.register_blueprint(profile_blue)

    # 个人中心
    from info.admin import admin_blue
    app.register_blueprint(admin_blue)

    return app

