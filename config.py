import redis
"""
专门用来存放配置文件

"""

class Config(object):
    # 开启调试模式,如果项目上线就不需要调试 DEGUBG = false

    # 设置数据库的链接地址,开发阶段会使用开发数据库
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
    SESSION_PERMANENT = 86400 * 3

# 开发阶段需要把debug调试模式开启
class DevelopementConfig(Config):
    DEGUBG = True

# 上线模式
class ProdutionConfig(Config):
    DEGUBG = False

# 通过字典动态传值
config_map = {
    "develope":DevelopementConfig,
    "prodution":ProdutionConfig
}






