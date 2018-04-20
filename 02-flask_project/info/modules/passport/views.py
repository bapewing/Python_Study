import random
import re

import flask

from info import redis_db
from info.utils import constants
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from sms import CCP
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
    # TODO:复习request的args属性
    image_code_id = flask.request.args.get('imageCodeId', None)

    if not image_code_id:
        flask.abort(403)
    # 生成图片验证码,图片内容需要保存
    name, text, image = captcha.generate_captcha()
    # 数据库操作都需要在try中实现
    try:
        redis_db.set('imageCodeId' + image_code_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        # TODO:复习logger属性
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
        flask.current_app.logger.debug("短信验证码内容是：%s" % sms_code_str)
        # bug：验证码和过期时间以数组形式传给第三方，属于文档阅读不仔细
        result = CCP().send_template_sms(mobile_phone, [sms_code_str, constants.SMS_CODE_REDIS_EXPIRES/5], '1')

        if result != 0:
            return flask.jsonify(errno=RET.THIRDERR, errmsg='发送短信失败')
        else:
            try:
                # 手机号作为key
                redis_db.set('SMS_' + mobile_phone, sms_code_str, constants.SMS_CODE_REDIS_EXPIRES)
            except Exception as e:
                flask.current_app.logger(e)
                return flask.jsonify(errno=RET.DBERR, errmsg='数据保存失败')
            return flask.jsonify(errno=RET.OK, errmsg='发送成功')
