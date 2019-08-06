# 自定义过滤器,判断index位置,如果是1,返回clss1
from flask import g
from flask import session
import functools
from info.models import User


def do_class_index(index):

    if index == 0:
        return "first"
    elif index == 1:
        return "second"
    elif index == 2:
        return "third"
    else:
        return ""


def user_login_data(f):
    @functools.wraps(f)
    def wrapper(*args,**kwargs):
        user_id = session.get('user_id')
        user = None
        # 判断用户是否已经登陆,user_id 是否有值
        if user_id:
            # 根据用户的id查询用户
            user = User.query.get(user_id)
        g.user = user
        return f(*args,**kwargs)
    return wrapper



# def user_login_data():
#     user_id = session.get('user_id')
#     user = None
#     # 判断用户是否已经登陆,user_id 是否有值
#     if user_id:
#         # 根据用户的id查询用户
#         user = User.query.get(user_id)
#     return user