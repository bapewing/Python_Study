import flask

from info.utils import constants
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET
from . import user_blu


@user_blu.route('/user_info')
@user_login_data
def user_info():
    user = flask.g.user
    if not user:
        return flask.redirect('/')
    data = {
        'user': user.to_dict()
    }
    return flask.render_template('user/user.html', data=data)


@user_blu.route('/base_info', methods=['GET', 'POST'])
@user_login_data
def user_base_info():
    user = flask.g.user
    if not user:
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    if flask.request.method == "GET":
        return flask.render_template('user/user_base_info.html', data={'user': user.to_dict()})

    parameters = flask.request.json
    nick_name = parameters.get('nick_name', None)
    signature = parameters.get('signature', None)
    gender = parameters.get('gender', None)

    if not all([nick_name, signature, gender]):
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    if gender not in ['MAN', 'WOMAN']:
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    user.nick_name = nick_name
    user.signature = signature
    user.gender = gender

    return flask.jsonify(errno=RET.OK, errmsg='OK')


@user_blu.route('/pic_info', methods=['GET', 'POST'])
@user_login_data
def user_pic_info():
    user = flask.g.user
    if not user:
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    if flask.request.method == "GET":
        return flask.render_template('user/user_pic_info.html', data={'user': user.to_dict()})

    try:
        # bug：must be str, not bytes 需要使用read读取成字节文件
        avatar = flask.request.files.get('avatar').read()
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        key = storage(avatar)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.THIRDERR, errmsg='上传图片失败')
    # 保存图片的key
    user.avatar_url = key
    data = {
        'avatar_url': constants.QINIU_DOMIN_PREFIX + key
    }

    return flask.jsonify(errno=RET.OK, errmsg='OK', data=data)