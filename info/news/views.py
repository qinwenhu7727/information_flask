from flask import g
from flask import session,request,jsonify

from info import constants, db
from info.models import News, User, Comment, CommentLike
from info.utils.response_code import RET
from . import news_blue
from flask import render_template
from info.utils.common import user_login_data

@news_blue.route("/followed_user",methods = ["POST","GET"])
@user_login_data
def followed_user():
    user = g.user
    # 表示我要关注的这个新闻作者的id
    user_id = request.json.get("user_id")
    # 'follow', 'unfollow'
    action = request.json.get("action")
    # 获取到当前的新闻作者
    news_user = User.query.get(user_id)

    if action == "follow":
        # 关注
        if news_user not in user.followed:
            # 表示当前新闻的作者,不在我关注的人列表当中,如果不在,就把作者添加到我的关注人列表当中
            user.followed.append(news_user)
        else:
            return jsonify(errno = RET.PARAMERR,errmsg = "我已经关注你了")
    else:
        # 取消关注
        if news_user in user.followed:
            user.followed.remove(news_user)
        else:
            return jsonify(errno=RET.PARAMERR, errmsg="没有在我的关注人列表里面,没有办法取消")

    db.session.commit()
    return jsonify(errno = RET.OK,errmsg = "ok")


@news_blue.route('/comment_like',methods = ["POST"])
@user_login_data
def comment_like():
    user = g.user
    if not user:
        return jsonify(errno = RET.SESSIONERR,errmsg = '请登陆')
    # 获取到评论id
    comment_id = request.json.get('comment_id')
    # 表示动作,如果 add(点赞)，remove(取消点赞)
    action = request.json.get('action')
    # 根据评论id获取到评论
    comment = Comment.query.get(comment_id)

    """
    用户点赞:
    1 需要根据评论查询
    2 需要用户必须登陆
    """

    if action == 'add':
       # 表示用户想点赞
       comment_like = CommentLike.query.filter(CommentLike.comment_id == comment_id,CommentLike.user_id == user.id).first()
       # 如果用户之前没有点赞,在点击的时候,就表示点赞,如果之前用户已经点赞,那么在点击就是取消
       if not comment_like:
           comment_like = CommentLike()
           comment_like.comment_id = comment_id
           comment_like.user_id = user.id
           # 如果被点赞了,那么点赞的条目数字,就必须+1

           db.session.add(comment_like)
           comment.like_count += 1

    else:
       # 取消点赞
       comment_like = CommentLike.query.filter(CommentLike.comment_id == comment_id,
                                               CommentLike.user_id == user.id).first()
       if comment_like:
           db.session.delete(comment_like)
           comment.like_count -= 1

    db.session.commit()
    return jsonify(errno = RET.OK,errmsg = 'ok')



@news_blue.route('/news_comment',methods = ["POST"])
@user_login_data
def news_comment():

    user = g.user

    if not user:
        return jsonify(errno = RET.SESSIONERR,errmsg = '请登陆')

    news_id = request.json.get('news_id')
    content = request.json.get('comment')
    parent_id = request.json.get('parent_id')

    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = content
    # 不是所有的评论都有回复评论,所以需要判断
    if parent_id:
        comment.parent_id = parent_id

    # 如果是第一次往数据库里面添加数据,需要添加add,如果更新数据,就不需要add,直接commit
    db.session.add(comment)
    db.session.commit()

    return jsonify(errno = RET.OK,errmsg = 'ok' ,data=comment.to_dict() )




@news_blue.route('/news_collect' ,methods = ["POST"])
@user_login_data
def news_collect():

    user = g.user

    # 判断当前的用户是否已经登陆,如果没有登陆,那么提示用户,请用户登录
    if not user:
        return jsonify(errno = RET.SESSIONERR ,errmsg = '请登陆')

    news_id = request.json.get('news_id')
    # 动作,一个表示收藏,一个表示取消收藏 'collect', 'cancel_collect
    action = request.json.get('action')


    # 根据id获取到新闻
    news = News.query.get(news_id)

    if action == 'collect':
        # 说明收藏
        user.collection_news.append(news)
    else:
        #  取消收藏
        user.collection_news.remove(news)

    db.session.commit()

    return jsonify(errno = RET.OK,errmsg = 'ok')





@news_blue.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):

    user = g.user

    # 查询首页右边的热门排行新闻数据
    news = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)



    news_list = []

    for new_model in news:
        news_list.append(new_model.to_dict())

    # 根据新闻id获取到详情页面的数据
    news_content =  News.query.get(news_id)

    # 当前新闻是否被收藏,一般默认情况下,第一次进来默认值肯定是false
    is_collection = False
    # 如果user有值,说明用户已经登陆
    if user:
        # 判断当前新闻,是否在当前用户的新闻收藏列表里面
        if news_content in user.collection_news:
            is_collection = True


    # 获取到新闻的评论列表
    comments =  Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    # 所有的点赞数据
    comment_likes = []
    # 所有的点赞id
    comment_likes_ids = []
    if user:
        comment_likes = CommentLike.query.filter(CommentLike.user_id == user.id).all()
        comment_likes_ids =  [comment_like.comment_id for comment_like in comment_likes]

    comments_list = []

    for comment in comments:
        comment_dict =  comment.to_dict()
        if comment.id in comment_likes_ids:
            comment_dict['is_like'] = True
        comments_list.append(comment_dict)

    # 判断用户是否关注
    is_followed = False

    # 当前新闻必须有作者,才能关注, 用户必须登陆,才能关注作者

    if user:
        # 判断当前新闻的作者是否在我关注的人的列表里面(张三,李四)
        if news_content.user in user.followed:
            is_followed = True


    data = {
        "user_info": user.to_dict() if user else None,
        "click_news_list": news_list,
        "news":news_content.to_dict(),
        "is_collected":is_collection,
        "comments":comments_list,
        "is_followed":is_followed
    }
    return render_template('news/detail.html',data = data)