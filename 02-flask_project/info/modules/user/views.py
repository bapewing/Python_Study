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
    # 保存图片的key TODO:图片每次获取都需要请求七牛，能不在本地做缓存？
    user.avatar_url = key
    data = {
        'avatar_url': constants.QINIU_DOMIN_PREFIX + key
    }

    return flask.jsonify(errno=RET.OK, errmsg='OK', data=data)


@user_blu.route('/pass_info', methods=['GET', 'POST'])
@user_login_data
def user_pass_info():
    user = flask.g.user
    if not user:
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    if flask.request.method == "GET":
        return flask.render_template('user/user_pass_info.html', data={'user': user.to_dict()})

    parameters = flask.request.json
    old_password = parameters.get('old_password', None)
    new_password = parameters.get('new_password', None)

    if not all([old_password, new_password]):
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    if not user.check_passowrd(old_password):
        return flask.jsonify(errno=RET.PWDERR, errmsg='密码错误')
    user.password = new_password

    return flask.jsonify(errno=RET.OK, errmsg='OK')


@user_blu.route('/collection')
@user_login_data
def user_collection_info():
    user = flask.g.user
    if not user:
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    page = flask.request.args.get('p', 1)
    try:
        page = int(page)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    pagination_obj = None
    try:
        pagination_obj = user.collection_news.paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据库查询错误')

    current_page = pagination_obj.page
    total_pages = pagination_obj.pages
    collection_model_list = pagination_obj.items

    collection_json_list = []
    for collection in collection_model_list:
        collection_json_list.append(collection.to_basic_dict())

    data = {
        'total_page': total_pages,
        'current_page': current_page,
        'collections': collection_json_list
    }

    return flask.render_template('user/user_collection.html', data=data)
