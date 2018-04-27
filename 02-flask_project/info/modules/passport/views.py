import random
import re

import datetime
import flask

from info import redis_db, db
from info.models import User
from info.utils import constants
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from info.libs.yuntongxun.sms import CCP
from . import passport_blu


@passport_blu.route('/image_code')
def get_image_code():
    """
    生成图片验证码并返回
    1. 取到参数
    2. 判断参数是否有值
    3. 生成图片验证码
    4. 保存图片验证码文字内容到redis
    5. 返回验证码图片
    """
    # 请求参数可以通过.com/image_code?imageCodeId=xxxxx 发送
    # 通过request.args()获取参数的内容，每次只能取一个key对应的值
    image_code_id = flask.request.args.get('imageCodeId', None)

    if not image_code_id:
        flask.abort(403)
    # 生成图片验证码,图片内容需要保存
    name, text, image = captcha.generate_captcha()
    # 数据库操作都需要在try中实现
    try:
        redis_db.set('imageCodeId' + image_code_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        flask.current_app.looger.error(e)
        # 存不进去属于服务器错误
        flask.abort(500)
    else:
        response = flask.make_response(image)
        # 兼容所有浏览器
        response.headers['Content-Type'] = "image/jpg"
        return response


@passport_blu.route('/sms_code', methods=['POST'])
def send_sms_code():
    """
    发送短信的逻辑
    1. 获取参数：手机号，图片验证码内容，图片验证码的编号 (随机值)
    2. 校验参数(参数是否符合规则，判断是否有值)
    3. 先从redis中取出真实的验证码内容
    4. 与用户的验证码内容进行对比，如果对比不一致，那么返回验证码输入错误
    5. 如果一致，生成验证码的内容(随机数据)
    6. 发送短信验证码,并保存验证码，以便校验
    7. 告知发送结果
    """
    # 本质：最后调用loads函数
    parameters = flask.request.json
    # parameters = flask.json.loads(flask.request.data)
    mobile_phone = parameters.get('mobile')
    image_code = parameters.get('image_code')
    image_code_id = parameters.get('image_code_id')

    if not all([mobile_phone, image_code, image_code_id]):
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数有误')
    if not re.match('1[35678]\\d{9}', mobile_phone):
        return flask.jsonify(errno=RET.PARAMERR, errmsg='手机号格式不正确')

    try:
        real_image_code = redis_db.get('imageCodeId' + image_code_id)
    except Exception as e:
        flask.current_app.logger(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据查询失败')
    else:
        # 过期
        if not real_image_code:
            return flask.jsonify(errno=RET.NODATA, errmsg='图片验证码过期')
        if image_code.upper() != real_image_code:
            return flask.jsonify(error=RET.DATAERR, errmsg='输入验证码错误')
        # 验证通过，可以发送手机验证码了
        sms_code_str = "%06d" % random.randint(0, 999999)
        # 不去搞和这个编码问题，直接变量
        flask.current_app.logger.debug(sms_code_str)
        # bug：验证码和过期时间以数组形式传给第三方，属于文档阅读不仔细
        result = CCP().send_template_sms(mobile_phone, [sms_code_str, constants.SMS_CODE_REDIS_EXPIRES / 5], '1')

        if result != 0:
            return flask.jsonify(errno=RET.THIRDERR, errmsg='发送短信失败')
        else:
            try:
                # 手机号作为key
                redis_db.set(mobile_phone, sms_code_str, constants.SMS_CODE_REDIS_EXPIRES)
            except Exception as e:
                flask.current_app.logger.error(e)
                return flask.jsonify(errno=RET.DBERR, errmsg='数据保存失败')
        return flask.jsonify(errno=RET.OK, errmsg='发送成功')


@passport_blu.route('/register', methods=['POST'])
def register():
    """
    注册的逻辑
    1. 获取参数
    2. 校验参数
    3. 取到服务器保存的真实的短信验证码内容
    4. 校验用户输入的短信验证码内容和真实验证码内容是否一致
    5. 如果一致，初始化 User 模型，并且赋值属性
    6. 将 user 模型添加数据库
    7. 返回响应
    """
    parameters = flask.request.json
    mobile_phone = parameters.get('mobile')
    sms_code = parameters.get('smscode')
    password = parameters.get('password')  # TODO: ajax请求加密？

    if not all([mobile_phone, sms_code, password]):
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    if not re.match('1[35678]\\d{9}', mobile_phone):
        return flask.jsonify(errno=RET.PARAMERR, errmsg='手机号格式不正确')
    try:
        real_sms_code = redis_db.get(mobile_phone)
    except Exception as e:
        flask.current_app.error.logger(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据库查询错误')
    else:
        if real_sms_code != sms_code:
            return flask.jsonify(errno=RET.DATAERR, errmsg='验证码过期')

        # 用户已经注册，停止往数据库插入数据
        if User.query.filter(User.mobile == mobile_phone).first():
            return flask.jsonify(errno=RET.DATAEXIST, errmsg='用户已经注册')

        user = User()
        user.mobile = mobile_phone
        user.nick_name = mobile_phone
        user.password = password
        user.last_login = datetime.datetime.now()

        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flask.current_app.logger.error(e)
            return flask.jsonify(errno=RET.DBERR, errmsg='数据库保存失败')
        else:
            flask.session['user_id'] = user.id
            flask.session['mobile'] = user.mobile
            flask.session['nick_name'] = user.nick_name

            return flask.jsonify(errno=RET.OK, errmsg='注册成功')


@passport_blu.route('/login', methods=['POST'])
def login():
    parameters = flask.request.json
    mobile = parameters.get('mobile', None)
    password = parameters.get('password', None)

    if not all([mobile, password]):
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    if not re.match('1[35678]\\d{9}', mobile):
        return flask.jsonify(errno=RET.PARAMERR, errmsg='手机号格式不正确')

    # 校验密码时，先查询当前手机号否注册过
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据库查询错误')
    if not user:
        return flask.jsonify(errno=RET.NODATA, errmsg='用户不存在')
    if not user.check_passowrd(password):
        return flask.jsonify(errno=RET.PWDERR, errmsg='用户名或密码输入错误')

    flask.session['user_id'] = user.id
    flask.session['mobile'] = user.mobile
    flask.session['nick_name'] = user.nick_name

    # 设置用户最后一次登录时间
    user.last_login = datetime.datetime.now()
    # 如果在视图函数中，对模型身上的属性有修改，那么需要commit到数据库保存
    # 但是其实可以不用自己去写 db.session.commit(),前提是对SQLAlchemy有过相关配置
    # try:
    #     db.session.commit()
    # except Exception as e:
    #     db.session.rollback()
    #     flask.current_app.logger.error(e)

    return flask.jsonify(errno=RET.OK, errmsg='登录成功')


@passport_blu.route('/logout')
def logout():
    flask.session.pop('user_id', None)
    flask.session.pop('mobile', None)
    flask.session.pop('nick_name', None)

    return flask.jsonify(errno=RET.OK, errmsg='退出成功')
