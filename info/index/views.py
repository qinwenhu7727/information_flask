import logging
from info import db
from info.models import User, News, Category
from info.utils.response_code import RET
from . import index_blue
from flask import render_template,current_app,session,request,jsonify
from  info import constants

@index_blue.route("/news_list")
def news_list():
    cid = request.args.get("cid","1")
    page = request.args.get("page","1")
    per_page = request.args.get("per_page","10")

    # 需要把上面的分类id,页数,每页展示的条目数,转换成整数
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        cid = 1
        page = 1
        per_page = 10

    # paginate:表示分页
    # 第一个参数:表示页数,第几页
    # 第二个参数: 表示每个页面展示几条数据
    # 第三个参数表示,是否需要有错误输出
    # if cid == 1:
    #     paginate = News.query.order_by(News.create_time.desc()).paginate(page,per_page,False)
    # else:
    #     paginate = News.query.filter(News.category_id == cid).order_by(News.create_time.desc()).paginate(page, per_page, False)
    filter = [News.status == 0]
    if cid != 1:
       filter.append(News.category_id == cid)



    paginate = News.query.filter(*filter).order_by(News.create_time.desc()).paginate(page, per_page,False)
    # 查询出来的数据
    items = paginate.items
    # 获取到总的页数
    toal_page = paginate.pages
    # 获取到当前页
    current_page = paginate.page

    items_list = []

    for item in items:
        items_list.append(item.to_dict())

    data = {
        "current_page":current_page,
        # 116
        "total_page":toal_page,
        "news_dict_li":items_list
    }

    return jsonify(errno = RET.OK ,errmsg = "ok", data = data)







@index_blue.route("/")
def index():
    user_id =  session.get('user_id')
    user = None
    # 判断用户是否已经登陆,user_id 是否有值
    if user_id:
       # 根据用户的id查询用户
       user = User.query.get(user_id)

    # 查询首页右边的热门排行新闻数据
    news = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)

    news_list = []

    for new_model in news:
        news_list.append(new_model.to_dict())


    # 上面的分类数据
    categorys =  Category.query.all()

    category_list = []

    for category in categorys:
        category_list.append(category.to_dict())

    data = {
        # "click_news_list":news_list
        "user_info": user.to_dict() if user else None,
        "click_news_list": news_list,
        "categories":category_list
    }

    return render_template('news/index.html',data= data )




@index_blue.route('/favicon.ico')
def send_img():

    return current_app.send_static_file('news/favicon.ico')