from flask import Blueprint,session,request,redirect

admin_blue = Blueprint('admin',__name__,url_prefix='/admin')

from . import views

@admin_blue.before_request
def check_user_is_admin():
    # user_id = session.get('user_id',None)
    is_admin = session.get('is_admin',False)
    # 如果不是管理员,那么就不能进入后台管理系统
    if not is_admin and not request.url.endswith("/admin/login"):
       return redirect('/')