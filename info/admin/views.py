from flask import g,jsonify,current_app
from flask import session, redirect, url_for
from info.utils.image_storage import storage
from info import db
from info.models import User, News, Category
from info.utils.response_code import RET
from . import admin_blue
from flask import render_template, request
from info.utils.common import user_login_data
import time
from datetime import datetime,timedelta

@admin_blue.route("/add_category",methods = ["GET","POST"])
def add_category():
    cid =  request.json.get("id")
    name = request.json.get("name")


    if cid:
        category =  Category.query.get(cid)
        category.name = name
    else:

        category = Category()
        category.name = name
        db.session.add(category)
    db.session.commit()

    return jsonify(errno = RET.OK,errmsg = "ok")




@admin_blue.route("/news_type")
def news_type():
    categorys =  Category.query.all()
    category_list = []
    for category in categorys:
        category_list.append(category.to_dict())

    category_list.pop(0)
    data = {
        "categories":category_list
    }
    return render_template("admin/news_type.html",data = data)




@admin_blue.route("/news_edit_detail",methods = ["GET","POST"])
def news_edit_detail():
    if request.method == "GET":
        news_id = request.args.get("news_id")

        news = News.query.get(news_id)

        categorys =  Category.query.all()

        categorys_list = []

        for category in categorys:
            categorys_list.append(category.to_dict())

        categorys_list.pop(0)

        data = {
            "news":news.to_dict(),
            "categories":categorys_list
        }

        return render_template("admin/news_edit_detail.html",data = data)

    news_id = request.form.get("news_id")
    title = request.form.get("title")
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image")
    category_id = request.form.get("category_id")
    # 1.1 判断数据是否有值
    if not all([title, digest, content, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if index_image:
        try:
            index_image = index_image.read()
        except Exception as e:
            return jsonify(errno=RET.PARAMERR, errmsg="参数有误")


    key = storage(index_image)

    # 3. 设置相关数据
    news.title = title
    news.digest = digest
    news.content = content
    news.category_id = category_id

    # 4. 保存到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")
    # 5. 返回结果
    return jsonify(errno=RET.OK, errmsg="编辑成功")







@admin_blue.route("/news_edit")
def news_edit():
    page =  request.args.get("p",1)
    try:
        page = int(page)
    except Exception as e:
        page = 1

    paginate =  News.query.order_by(News.create_time.desc()).paginate(page,10,False)

    items = paginate.items
    total_page = paginate.pages
    current_page = paginate.page

    news_list  =[]
    for item in items:
        news_list.append(item.to_basic_dict())

    data = {
        "news_list":news_list,
        "total_page":total_page,
        "current_page":current_page
    }

    return render_template("admin/news_edit.html",data = data)



@admin_blue.route("/news_review_detail",methods = ["GET","POST"])
def news_review_detail():
    if request.method == "GET":
        news_id =  request.args.get("news_id")
        news = News.query.get(news_id)
        data = {
            "news":news.to_dict()
        }
        return render_template("admin/news_review_detail.html",data = data)
    # 获取到前端传递过来的动作,表示通过或者拒绝
    action = request.json.get("action")
    news_id = request.json.get('news_id')

    # 当前用户发表的新闻
    news = News.query.get(news_id)
    # 判断管理员是通过还是拒绝
    if action == "accept":
        # 通过
        news.status = 0
    else:
        # 表示拒绝的原因,因为没有通过必须告诉用户为什么没有通过
        reason = request.json.get('reason')
        if not reason:
            return jsonify(errno = RET.PARAMERR,errmsg = '请输入拒绝的原因')
        # 拒绝
        news.status = -1

    db.session.commit()
    return jsonify(errno = RET.OK,errmsg = 'ok')


@admin_blue.route('/news_review')
def news_review():
    page = request.args.get("p", 1)
    # 管理员的输入搜索数据
    keywords = request.args.get("keywords")

    try:
        page = int(page)
    except Exception as e:
        page = 1

    filters = [News.status != 0]
    # 判断管理员是否有搜索数据
    if keywords:
        filters.append(News.title.contains(keywords))

    paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page,10,False)
    items = paginate.items

    current_page = paginate.page
    total_page = paginate.pages

    news_list = []

    for item in items:
        news_list.append(item.to_review_dict())

    data = {
        "current_page":current_page,
        "total_page":total_page,
        "news_list":news_list
    }


    return render_template('admin/news_review.html',data = data)



@admin_blue.route('/user_list')
def user_list():
    page = request.args.get("p",1)

    try:
        page = int(page)
    except Exception as e:
        page = 1


    paginate =  User.query.filter(User.is_admin == False).order_by(User.last_login.desc()).paginate(page,10,False)

    items = paginate.items

    current_page = paginate.page
    total_page = paginate.pages

    user_list = []

    for u in items:
        user_list.append(u.to_admin_dict())

    data = {
        "current_page":current_page,
        "total_page":total_page,
        "users":user_list
    }

    return render_template("admin/user_list.html",data = data)











@admin_blue.route('/user_count')
def user_count():
    # 总人数
    total_count  = 0
    # 每个月新增人数
    mon_count  = 0
    # 每天新增人数
    day_count  = 0
    # 查询总人数
    total_count =  User.query.filter(User.is_admin == False).count()
    # 获取到当前的时间
    now =  time.localtime()



    # 获取到月和年
    mon_begin = "%d-%02d-01"%(now.tm_year,now.tm_mon)
    # 获取时分秒
    mon_begin_day =  datetime.strptime(mon_begin,"%Y-%m-%d")

    # 查询本月新增人数,11月1号 0点0分0秒
    mon_count =  User.query.filter(User.is_admin == False , User.create_time >= mon_begin_day).count()

    # 获取到月和年
    day_begin = "%d-%02d-%02d" % (now.tm_year, now.tm_mon,now.tm_mday)
    # 获取时分秒
    day_begin_day = datetime.strptime(day_begin, "%Y-%m-%d")

    # 查询本月新增人数,11月1号 0点0分0秒
    day_count = User.query.filter(User.is_admin == False, User.create_time >= day_begin_day).count()

    # 获取到月和年
    today_begin = "%d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday)
    # 获取时分秒 2018-11-7 00:00:00
    today_begin_day = datetime.strptime(today_begin, "%Y-%m-%d")

    activate_count = []
    activate_time = []

    for i in range(0,30):
        # 获取到今天的开始时间
        begin_day = today_begin_day - timedelta(days = i)
        # 获取到今天的结束时间
        end_day = today_begin_day - timedelta(days = (i - 1))

        day_count = User.query.filter(User.is_admin == False, User.create_time >= begin_day,User.create_time < end_day).count()
        activate_count.append(day_count)
        activate_time.append(begin_day.strftime('%Y-%m-%d'))

    # 算一个月的活跃用户
    #
    activate_count.reverse()
    activate_time.reverse()
    data = {
        "total_count":total_count,
        "mon_count":mon_count,
        "day_count":day_count,
        "active_count":activate_count,
        "active_date":activate_time
    }

    return render_template('admin/user_count.html',data = data)



@admin_blue.route('/index')
@user_login_data
def admin_index():
    """站点主页
        """
    # 读取登录用户的信息
    user = g.user
    # 优化进入主页逻辑：如果管理员进入主页，必须要登录状态，反之，就引导到登录界面
    if not user:
        return redirect(url_for('admin.admin_login'))

    # 构造渲染数据
    data = {
        'user': user.to_dict()
    }
    # 渲染主页
    return render_template('admin/index.html', data=data)


@admin_blue.route('/login', methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        if user_id and is_admin:
            return redirect(url_for('admin.admin_index'))
        return render_template('admin/login.html')

    username = request.form.get("username")
    password = request.form.get("password")
    if not all([username, password]):
        return render_template('admin/login.html', errmsg="参数不足")

    user = User.query.filter(User.mobile == username, User.is_admin == True).first()

    if not user:
        return render_template('admin/login.html', errmsg='请登陆')

    if not user.check_password(password):
        return render_template('admin/login.html', errmsg='密码错误')

    session['user_id'] = user.id
    session['mobile'] = user.mobile
    session['nick_name'] = user.nick_name
    session['is_admin'] = user.is_admin

    return redirect(url_for('admin.admin_index'))
