from flask_migrate import Migrate,MigrateCommand
from flask_script import Manager
from info import create_app,db
from info import models
from info.models import User

"""
入口程序
ctrl + alt + o :优化导包,去掉没用的包

"""

app = create_app("develope")


# 把app交给manager进行管理
manager = Manager(app)
# 创建数据库的迁移框架
Migrate(app,db)
# 添加迁移数据库框架的脚本
manager.add_command('xxx',MigrateCommand)

@manager.option('-n', '--name', dest='name')
@manager.option('-p', '--pwd', dest='pwd')
def create_super_user(name,pwd):
    user = User()
    user.nick_name = name
    user.password = pwd
    user.mobile = name
    # 说明当前用户是管理员
    user.is_admin = True
    db.session.add(user)
    db.session.commit()





if __name__ == '__main__':
    manager.run()