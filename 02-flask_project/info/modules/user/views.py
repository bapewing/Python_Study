import flask

from info import db
from info.models import Category, News, User
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


@user_blu.route('/news_release', methods=['GET', 'POST'])
@user_login_data
def user_news_release():
    user = flask.g.user
    if not user:
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    if flask.request.method == "GET":
        try:
            category_model_list = Category.query.all()
        except Exception as e:
            flask.current_app.logger.error(e)
            return flask.jsonify(errno=RET.DBERR, errmsg='数据库查询错误')
        category_json_list = []
        for category in category_model_list:
            category_json_list.append(category.to_dict())
        # 移除最新的分类
        category_json_list.pop(0)

        data = {
            'user': user.to_dict(),
            'categories': category_json_list
        }
        return flask.render_template('user/user_news_release.html', data=data)

    title = flask.request.form.get("title")
    source = "个人发布"
    digest = flask.request.form.get("digest")
    content = flask.request.form.get("content")
    index_image = flask.request.files.get("index_image")
    category_id = flask.request.form.get("category_id")

    if not all([title, source, digest, content, index_image, category_id]):
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数有误')

    try:
        category_id = int(category_id)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数有误')

    try:
        index_image = index_image.read()
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        key = storage(index_image)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.THIRDERR, errmsg='上传图片失败')

    news = News()
    news.title = title
    news.digest = digest
    news.source = source
    news.content = content
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
    news.category_id = category_id
    news.user_id = user.id
    news.status = 1

    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据库错误')

    return flask.jsonify(errno=RET.OK, errmsg='OK')


@user_blu.route('/news_list')
@user_login_data
def user_news_list():
    user = flask.g.user
    if not user:
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    page = flask.request.args.get("p", 1)

    try:
        page = int(page)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        pagination_obj = News.query.filter(News.user_id == user.id).paginate(page, constants.USER_COLLECTION_MAX_NEWS,
                                                                             False)
        news_model_list = pagination_obj.items if pagination_obj.items else []
        current_page = pagination_obj.page if pagination_obj.page else 1
        total_page = pagination_obj.pages if pagination_obj.pages else 1
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据库查询错误')

    news_json_list = []
    for news in news_model_list:
        news_json_list.append(news.to_review_dict())

    data = {
        "news_list": news_json_list,
        "total_page": total_page,
        "current_page": current_page
    }

    return flask.render_template('user/user_news_list.html', data=data)


@user_blu.route('/user_follow')
@user_login_data
def user_follow():
    user = flask.g.user
    if not user:
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    p = flask.request.args.get("p", 1)
    try:
        p = int(p)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        pagination_obj = user.followed.paginate(p, constants.USER_FOLLOWED_MAX_COUNT, False)
        follow_model_list = pagination_obj.items
        current_page = pagination_obj.page
        total_page = pagination_obj.pages
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据库查询错误')

    user_json_list = []
    for follow_user in follow_model_list:
        user_json_list.append(follow_user.to_dict())

    data = {
        "users": user_json_list,
        "total_page": total_page,
        "current_page": current_page
    }

    return flask.render_template('user/user_follow.html', data=data)


# TODO: 1.退出时的bug 2.通过/other_info/<int:other_user_id>方式获取用户信息 3.接口可以设计成获取页面所有数据，而不是用到两个请求
@user_blu.route('/other_info')
@user_login_data
def other_info():
    user = flask.g.user
    if not user:
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    other_user_id = flask.request.args.get('other_user_id')
    try:
        other_user_id = int(other_user_id)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        other = User.query.get(other_user_id)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据库查询错误')

    if not other:
        flask.abort(404)

    is_followed = False
    if other and user:
        if other in user.followed:
            is_followed = True

    data = {
        'user': user.to_dict(),
        'is_followed': is_followed,
        'other_info': other.to_dict()
    }
    return flask.render_template('user/other.html', data=data)


@user_blu.route('/other_news_list')
@user_login_data
def other_news_list():
    user = flask.g.user
    if not user:
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    other_user_id = flask.request.args.get('other_user_id')
    page = flask.request.args.get('p', 1)

    if not all([other_user_id, page]):
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        other_user_id = int(other_user_id)
        page = int(page)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        other = User.query.get(other_user_id)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据库查询错误')

    if not other:
        return flask.jsonify(errno=RET.NODATA, errmsg='当前用户不存在')

    try:
        pagination_obj = other.news_list.paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
        news_model_list = pagination_obj.items
        current_page = pagination_obj.page
        total_page = pagination_obj.pages
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errnp=RET.DBERR, errmsg='数据库查询错误')

    news_json_list = []
    for news_item in news_model_list:
        news_json_list.append(news_item.to_basic_dict())

    data = {
        "news_list": news_json_list,
        "total_page": total_page,
        "current_page": current_page
    }
    return flask.jsonify(errno=RET.OK, errmsg="OK", data=data)
