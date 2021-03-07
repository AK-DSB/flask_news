import datetime
import json
import re
from . import passport_blue
from flask import request, current_app, make_response, jsonify, session, redirect, url_for
import random

from ...libs.yuntongxun.sms import CCP
from ...utils.response_code import RET


@passport_blue.route('/logout', methods=['POST', 'GET'])
def logout():
    from info import redis_store
    session.pop('user_id', None)
    session.pop('is_admin', None)
    if request.method == 'POST':

        return jsonify(errno=RET.OK, errmsg='退出成功')
    return redirect(url_for('admin.admin_login'))


@passport_blue.route('/login', methods=['POST'])
def login():
    from info import models, db
    mobile = request.json.get('mobile')
    password = request.json.get('password')
    if not all([mobile, password]):
        return jsonify(error=RET.PARAMERR, errmsg='参数不全')
    try:
        user = models.User.query.filter(models.User.mobile == mobile).first()
    except Exception as e:
        current_app.logger(e)
        return jsonify(errno=RET.DBERR, errmsg='用户查询失败')
    if not user:
        return jsonify(errno=RET.NODATA, errmsg='用户尚未注册')
    if not user.check_password(password):
        return jsonify(errno=RET.DBERR, errmsg='密码错误')
    # 将用户保存在session中
    session['user_id'] = user.id
    # 记录用户最后一次登陆时间
    user.last_login = datetime.datetime.now()
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg='登录成功')


# 注册用户
# 请求路径: /passport/register
# 请求方式: POST
# 请求参数: mobile, sms_code, password
# 返回值errno, errmsg
@passport_blue.route('/register', methods=['POST'])
def register():
    from ... import redis_store
    dict_data = request.json
    mobile = dict_data.get('mobile')
    sms_code = dict_data.get('sms_code')
    password = dict_data.get('password')
    if not all([mobile, sms_code, password]):
        return jsonify(err=RET.PARAMERR, errmsg='参数不全')
    try:
        redis_sms_code = redis_store.get(f'sms_code:{mobile}')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='短信验证码取出失败')
    if not redis_sms_code:
        return jsonify(errno=RET.NODATA, errmsg='短信验证码已过期')
    if sms_code != redis_sms_code:
        return jsonify(errno=RET.DATAERR, errmsg='短信验证码填写有误')
    try:
        redis_store.delete(f'sms_code"{mobile}')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='验证码删除失败')
    from info import db, models
    user = models.User(
        nick_name=mobile,
        password=password,
        mobile=mobile,
        signature='该用户很懒什么都没写',
    )
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='用户注册失败')
    return jsonify(errno=RET.OK, errmsg='注册成功')


# 请求路径 /passport/sms_code
# 请求方式 POST
# 请求参数 mobile  image_code, image_code_id
# 返回值: errno, errmsg
@passport_blue.route('/sms_code', methods=['GET', 'POST'])
def sms_code():
    # from info import redis_store, constants
    # json_data = request.data
    # dict_data = json.loads(json_data)
    # mobile = dict_data.get('mobile')
    # image_code = dict_data.get('image_code')
    # image_code_id = dict_data.get('image_code_id')
    # redis_image_code = redis_store.get(f'image_code:{image_code_id}')
    # print(image_code, redis_image_code)
    # if image_code.lower() != redis_image_code.lower():
    #
    #     return jsonify(errno=10000, errmsg='验证码填错了!')
    # if not re.match(r'1[3-9]\d{9}', mobile):
    #     return jsonify(errno=20000, errmsg='手机号格式不匹配')
    # ccp = CCP()
    # msg = 'qwertyuiopasdfghgjklzxcvbnmQWERTYUIOPLKJHGFDFSAZXCVBNM0123456789'
    # code = ''
    # for i in range(6):
    #     code += random.choice(msg)
    # result = ccp.send_template_sms(str(mobile), [code, 5], 1)
    # if result == -1:
    #     return jsonify(errno=30000, errmsg='短信发送失败')
    # return jsonify(errno=0, errmsg=f'短信发送成功,请查收')

    from info import redis_store, constants
    dict_data = request.get_json()
    mobile = dict_data.get('mobile')
    image_code = dict_data.get('image_code')
    image_code_id = dict_data.get('image_code_id')
    # 参数为空校验 all()方法
    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')
    # 校验手机格式
    if not re.match(r'1[3-9]\d{9}', mobile):
        return jsonify(error=RET.DATAERR, errmsg='手机格式错误')
    try:
        redis_image_code = redis_store.get(f'image_code:{image_code_id}')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='操作redis失败')
    if not redis_image_code:
        return jsonify(errno=RET.NODATA, errmsg='图片验证码已过期')
    if image_code.lower() != redis_image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg='图片验证码填写错误')

    # 删除redis里面的图片验证码
    try:
        redis_store.delete(f'image_code{image_code_id}')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='删除图片验证码错误')
    code = '%06d' % random.randint(0, 999999)
    # ccp = CCP()
    # result = ccp.send_template_sms(to=mobile, datas=[code, constants.SMS_CODE_REDIS_EXPIRES / 60], temp_id=1)
    # print(result)
    # if result == -1:
    #     return jsonify(errno=RET.DATAERR, errmsg='短信发送失败')
    current_app.logger.error(f'短信验证码是{code}')
    # 将短信保存到redis中
    try:
        redis_store.set('sms_code:%s' % mobile, code, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='短信保存失败')
    return jsonify(errno=RET.OK, errmsg=f'短信发送成功,请注意查收,验证码是{code}')


# 功能: 获取图片验证码
# 请求路径 /passport/image_code
# GET请求
# 请求参数cur_id, pre_id
# 返回值: 图片验证码
@passport_blue.route('/image_code')
def image_code():
    from info import redis_store, constants
    from ...utils.captcha.captcha import captcha
    name, text, image_data = captcha.generate_captcha()

    # 将图片验证码保存
    try:
        cur_id = request.args.get('cur_id')
        pre_id = request.args.get('pre_id')
        redis_store.set(f'image_code:{cur_id}', text, constants.IMAGE_CODE_REDIS_EXPIRES)
        print(cur_id)
        print(pre_id)
        if pre_id:
            redis_store.delete(f'image_code:{pre_id}')
    except Exception as e:
        current_app.logger.error(e)
        return '图片验证码操作失败'
    response = make_response(image_data)
    response.headers['Content-Type'] = 'image/png'
    return response

