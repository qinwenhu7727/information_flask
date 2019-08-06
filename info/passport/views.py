from info.lib.yuntongxun.sms import CCP
from info.utils.response_code import RET
from . import passport_blue
from flask import make_response,request,jsonify,session,current_app
from info.utils.captcha.captcha import captcha
from info import redis_store,constants,db
import re
import random
from info.models import User
from datetime import datetime

@passport_blue.route('/logout')
def logout():
    session.pop('mobile',None)
    session.pop('user_id',None)
    session.pop('nick_name',None)
    session.pop('is_admin',None)
    return jsonify(errno = RET.OK,errmsg = '退出')





# 登陆
@passport_blue.route('/login',methods = ["POST","GET"])
def login():
    mobile = request.json.get('mobile')
    password = request.json.get('password')

    try:
    # 根据用户传输过来的手机号进行查询
        user =  User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.e(e)

    if not user:
        return jsonify(errno = RET.USERERR , errmsg = '请注册')

    if not user.check_password(password):
        return jsonify(errno = RET.PWDERR,errmsg = '请输入正确的密码')

    # 设置最后更新时间
    user.last_login = datetime.now()
    db.session.commit()

    session['mobile'] = user.mobile
    session['user_id'] = user.id
    session['nick_name'] = user.nick_name

    return jsonify(errno = RET.OK,errmsg = '登陆成功')


# 注册
@passport_blue.route('/register',methods = ["POST","GET"])
def register():
    mobile = request.json.get('mobile')
    smscode = request.json.get('smscode')
    password = request.json.get('password')

    if not all([mobile,smscode,password]):
        return jsonify(errno = RET.PARAMERR,errmsg = '请输入正确的参数')

    # 注册
    # 获取到redis数据库里面的短信验证码
    real_sms_code =  redis_store.get('sms_code_' + mobile)

    if not real_sms_code:
        return jsonify(errno = RET.NODATA,errmsg = '短信验证码已经过期')

    if smscode != real_sms_code:
        return jsonify(errno = RET.PARAMERR,errmsg = '请输入正确的短信验证码')

    user = User()
    user.nick_name = mobile
    user.password = password
    user.mobile = mobile
    # 提交注册用户到数据库里面
    db.session.add(user)
    db.session.commit()
    return jsonify(errno = RET.OK,errmsg = '注册成功')



"""
发送短信验证码实现流程：
    接收前端发送过来的请求参数
    检查参数是否已经全部传过来
    判断手机号格式是否正确
    检查图片验证码是否正确，若不正确，则返回
    生成随机的短信验证码
    使用第三方SDK发送短信验证码
"""
@passport_blue.route('/sms_code',methods = ["POST","GET"])
def sms_code():
    # 获取到前端发送过来的手机号
    mobile = request.json.get('mobile')
    # 获取到前端发送过来的图片验证码
    image_code = request.json.get('image_code')
    # Content-Type : text/html
    # 获取到前端发送过来的uuid,目的是为了获取到redis里面的值
    image_code_id = request.json.get('image_code_id')
    # 判断前端传输过来的数据是否有问题
    if not all([mobile,image_code,image_code_id]):
        return jsonify(errno = RET.PARAMERR,errmsg = '请输入正确的参数')

    # 校验手机号是否正确
    if not re.match('1[3456789]\\d{9}',mobile):
        return jsonify(errno = RET.PARAMERR,errmsg = '请输入正确的手机号')


    # 获取存取到redis里面的图片验证码
    # 从redis获取到的值是二进制,前端传递过来的数据是字符串类型,所以没有办法进行比较
    # 需要设置redis里面的第三个参数,表示进行解码
    # redis.StrictRedis(host=name.REDIS_HOST,port=name.REDIS_PORT,decode_responses=True)
    real_image_code = redis_store.get('image_code_' + image_code_id)
    # 判断图片验证码是否过期
    if not real_image_code:
        return jsonify(errno = RET.NODATA,errmsg = '图片验证码已经过期')

    # 检查图片验证码是否正确
    if image_code.lower() != real_image_code.lower():
        return jsonify(errno = RET.PARAMERR,errmsg = '请输入正确的图片验证码')

    # 生成随机数
    # 随机数6为 100000
    # 创建一个随机数
    # 第一个参数表示开始的位置
    # 第二个参数表示结束的位置
    result =  random.randint(0,999999)
    smsCode = "%06d"%result
    print('短信验证码:' + smsCode )
    # 设置短信验证码
    redis_store.set('sms_code_'+mobile,smsCode,constants.SMS_CODE_REDIS_EXPIRES)

    # 发送短信
    # 第一个参数:发送给哪个手机号
    # 第二个参数:表示数据内容,格式[短信验证码的内容,几分钟之后过期]
    # 第三参数:表示默认值
    # statusCode = CCP().send_template_sms(mobile,[smsCode,5],1)
    # if statusCode != 0:
    #     return jsonify(errno = RET.THIRDERR,errmsg = '发送短信失败')
    return jsonify(errno = RET.OK,errmsg = '发送短信成功')



# imageCodeUrl = "/passport/image_code?code_id=431387b1-42dd-4671-840d-bfbefc6
@passport_blue.route('/image_code')
def image_code():
    url =  request.url
    # 获取到uuid,uuid是一个唯一值
    code_id =  request.args.get('code_id')
    print("UUID = " + code_id)
    # 生成图片验证码
    # 第一个参数:表示图片验证码的名字
    # 第二个参数:表示图片验证码的内容
    # 第三个参数:表示图片验证码的图片
    name, text, image = captcha.generate_captcha()
    print("图片验证码的内容:" + text)
    # 设置redis
    redis_store.set('image_code_' + code_id,text,constants.IMAGE_CODE_REDIS_EXPIRES)
    # 返回一张图片,目前返回的是空图片
    resp = make_response(image)
    resp.headers['Content-Type'] = 'image/jpg'
    return resp