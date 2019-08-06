from flask import g, redirect
from flask import request, jsonify

from info import constants
from info import db
from info.models import User, Category, News
from info.utils.response_code import RET
from . import profile_blue

from flask import render_template
from info.utils.common import user_login_data
from info.utils.image_storage import storage


@profile_blue.route("/followed_user")
@user_login_data
def user_follow():
    user = g.user

    page =  request.args.get("p",1)

    try:
        page = int(page)
    except Exception as e:
        page = 1

    paginate =  user.followed.paginate(page,4,False)

    items =  paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    users_list = []

    for item in items:
        users_list.append(item.to_dict())

    data = {
        "users":users_list,
        "current_page":current_page,
        "total_page":total_page
    }

    return render_template("news/user_follow.html", data = data)



@profile_blue.route('/news_list')
@user_login_data
def news_list():
    user = g.user
    page = request.args.get("p", "1")

    try:
        page = int(page)
    except Exception as e:
        page = 1

    # 获取发布的所有新闻
    paginate = News.query.filter(News.user_id == user.id).paginate(page, 2, False)
    itmes = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    collection_news_list = []

    for item in itmes:
        collection_news_list.append(item.to_review_dict())

    data = {
        "current_page": current_page,
        "total_page": total_page,
        "news_list": collection_news_list
    }
    return render_template("news/user_news_list.html",data = data)


@profile_blue.route('/news_release', methods=["GET", "POST"])
@user_login_data
def news_release():
    user = g.user
    if request.method == "GET":
        categorys = Category.query.all()

        categorys_list = []

        for category in categorys:
            categorys_list.append(category.to_dict())

        categorys_list.pop(0)
        data = {
            "categories": categorys_list
        }

        return render_template('news/user_news_release.html', data=data)


        # POST 提交，执行发布新闻操作

    # 1. 获取要提交的数据
    title = request.form.get("title")
    source = "个人发布"
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image")
    category_id = request.form.get("category_id")
    # 1.1 判断数据是否有值
    if not all([title, source, digest, content, index_image, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    url =  index_image.read()
    # 上传到七牛云 返回七牛云的key
    key =  storage(url)

    news = News()
    news.title = title
    news.source = source
    news.digest = digest
    news.content = content
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
    news.category_id = category_id
    news.user_id = user.id
    news.status = 1

    db.session.add(news)
    db.session.commit()
    return jsonify(errno = RET.OK,errmsg = '发布成功')


@profile_blue.route('/collection')
@user_login_data
def collection():
    user = g.user
    page = request.args.get("p", "1")

    try:
        page = int(page)
    except Exception as e:
        page = 1

    # 获取到所有的收藏新闻
    paginate = user.collection_news.paginate(page, 2, False)
    itmes = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    collection_news_list = []

    for item in itmes:
        collection_news_list.append(item.to_dict())

    data = {
        "current_page": current_page,
        "total_page": total_page,
        "collections": collection_news_list
    }

    return render_template("news/user_collection.html", data=data)


@profile_blue.route("/pass_info", methods=["GET", "POST"])
@user_login_data
def pass_info():
    user = g.user
    if request.method == "GET":
        data = {
            "user_info": user.to_dict() if user else None
        }
        return render_template("news/user_pass_info.html", data=data)
    old_password = request.json.get('old_password')
    new_password = request.json.get('new_password')

    if not user.check_password(old_password):
        return jsonify(errno=RET.PWDERR, errmsg='密码错误')

    user.password = new_password
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg='密码修改成功')


@profile_blue.route("/pic_info", methods=["GET", "POST"])
@user_login_data
def pic_info():
    user = g.user
    if request.method == "GET":
        data = {
            "user_info": user.to_dict() if user else None
        }
        return render_template("news/user_pic_info.html", data=data)

    avatar_url = request.files.get('avatar').read()
    # 上传到七牛云
    key = storage(avatar_url)
    # 更新用户的头像
    user.avatar_url = key
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg='ok', data={"avatar_url": constants.QINIU_DOMIN_PREFIX + key})


@profile_blue.route("/base_info", methods=["GET", "POST"])
@user_login_data
def user_base_info():
    user = g.user
    if request.method == "GET":
        data = {
            "user_info": user.to_dict() if user else None
        }
        return render_template("news/user_base_info.html", data=data)

    nick_name = request.json.get('nick_name')
    signature = request.json.get('signature')
    gender = request.json.get('gender')

    user.nick_name = nick_name
    user.signature = signature
    user.gender = gender
    # 因为这条数据,在数据库已经存在,所以直接提交不需要add
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg='修改成功')


@profile_blue.route("/info")
@user_login_data
def user_info():
    user = g.user
    if not user:
        # 如果用户没有登陆,直接调到首页
        return redirect("/")

    data = {
        "user_info": user.to_dict() if user else None
    }

    return render_template("news/user.html", data=data)
