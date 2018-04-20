import flask

from info import redis_db
from info.utils import constants
from info.utils.captcha.captcha import captcha
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
