import flask
import time

from datetime import datetime, timedelta

from info.models import User, News, Category
from info.utils import constants
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET
from . import admin_blu


@admin_blu.route('/index')
@user_login_data
def index():
    user = flask.g.user
    data = {
        'user': user.to_dict() if user else None
    }
    return flask.render_template('admin/index.html', data=data)


@admin_blu.route('/login', methods=['GET', 'POST'])
def admin_login():
    if flask.request.method == 'GET':
        user_id = flask.session.get('user_id', None)
        is_admin = flask.session.get('is_admin', False)
        if user_id and is_admin:
            return flask.redirect(flask.url_for('admin.index'))
        return flask.render_template('admin/login.html')

    # 取到登录的参数
    username = flask.request.form.get("username")
    password = flask.request.form.get("password")

    # 判断参数
    if not all([username, password]):
        return flask.render_template('admin/login.html', errmsg="参数错误")

    # 查询当前用户
    try:
        user = User.query.filter(User.mobile == username, User.is_admin == True).first()
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.render_template('admin/login.html', errmsg="用户信息查询失败")

    if not user:
        return flask.render_template('admin/login.html', errmsg="未查询到用户信息")

    # 校验密码
    if not user.check_passowrd(password):
        return flask.render_template('admin/login.html', errmsg="用户名或者密码错误")

    # 保存用户的登录信息
    flask.session["user_id"] = user.id
    flask.session["mobile"] = user.mobile
    flask.session["nick_name"] = user.nick_name
    flask.session["is_admin"] = user.is_admin

    # 跳转到后面管理首页
    return flask.redirect(flask.url_for('admin.index'))


@admin_blu.route('/user_count')
@user_login_data
def user_count():
    user = flask.g.user
    if not user:
        # TODO: 什么时候返回模板文件？
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    # TODO:根据需求，需要显示模板时，应该有个默认返回值 不需要返回模板时，可以return json
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonfiy(errno=RET.DBERR, errmsg='数据库查询错误')

    # TODO: 查询下时间格式
    t = time.localtime()
    begin_mon_time = datetime.strptime(('%d-%02d-01' % (t.tm_year, t.tm_mon)), '%Y-%m-%d')
    try:
        mon_count = User.query.filter(User.is_admin == False, User.create_time > begin_mon_time).count()
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonfiy(errno=RET.DBERR, errmsg='数据库查询错误')

    begin_day_time = datetime.strptime(('%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday)), '%Y-%m-%d')
    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time > begin_day_time).count()
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonfiy(errno=RET.DBERR, errmsg='数据库查询错误')

    # 拆线图数据

    active_time = []
    active_count = []

    # 取到今天的时间字符串
    today_date_str = ('%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday))
    # 转成时间对象
    today_date = datetime.strptime(today_date_str, "%Y-%m-%d")

    for i in range(0, 31):
        # 取到某一天的0点0分
        begin_date = today_date - timedelta(days=i)
        # 取到下一天的0点0分
        end_date = today_date - timedelta(days=(i - 1))
        count = User.query.filter(User.is_admin == False, User.last_login >= begin_date,
                                  User.last_login < end_date).count()
        active_count.append(count)
        active_time.append(begin_date.strftime('%Y-%m-%d'))

    # User.query.filter(User.is_admin == False, User.last_login >= 今天0点0分, User.last_login < 今天24点).count()

    # 反转，让最近的一天显示在最后
    active_time.reverse()
    active_count.reverse()

    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_time": active_time,
        "active_count": active_count

    }

    return flask.render_template('admin/user_count.html', data=data)


@admin_blu.route('/user_list')
@user_login_data
def user_list():
    user = flask.g.user
    if not user:
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    page = flask.request.args.get("page", 1)
    try:
        page = int(page)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        pagination_obj = User.query.filter(User.is_admin == False).paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT,
                                                                            False)
        user_model_list = pagination_obj.items
        current_page = pagination_obj.page
        total_page = pagination_obj.pages
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据库查询错误')

    # 进行模型列表转字典列表
    user_json_list = []
    for user in user_model_list:
        user_json_list.append(user.to_admin_dict())

    data = {
        "users": user_json_list,
        "total_page": total_page,
        "current_page": current_page,
    }

    return flask.render_template('admin/user_list.html', data=data)


@admin_blu.route('/news_review')
@user_login_data
def news_review():
    user = flask.g.user
    if not user:
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    page = flask.request.args.get("page", 1)
    keywords = flask.request.args.get('keywords', None)
    try:
        page = int(page)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    filters = [News.status != 0]
    if keywords:
        filters.append(News.title.contains(keywords))

    try:
        pagination_obj = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page,
                                                                                                constants.ADMIN_NEWS_PAGE_MAX_COUNT,
                                                                                                False)
        news_model_list = pagination_obj.items
        current_page = pagination_obj.page
        total_page = pagination_obj.pages
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据库查询错误')

    # 进行模型列表转字典列表
    news_json_list = []
    for news in news_model_list:
        news_json_list.append(news.to_review_dict())

    data = {
        "news_list": news_json_list,
        "total_page": total_page,
        "current_page": current_page
    }

    return flask.render_template('admin/news_review.html', data=data)


@admin_blu.route('/news_review_detail/<int:news_id>')
@user_login_data
def news_review_detail(news_id):
    user = flask.g.user
    if not user:
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    try:
        news = News.query.get(news_id)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据库查询错误')

    if not news:
        return flask.render_template('admin/news_review_detail.html', data={"errmsg": "未查询到此新闻"})

    data = {
        "news": news.to_dict()
    }
    return flask.render_template('admin/news_review_detail.html', data=data)


@admin_blu.route('/news_review_action', methods=['POST'])
@user_login_data
def news_review_action():
    user = flask.g.user
    if not user:
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    # 1. 接受参数
    news_id = flask.request.json.get("news_id")
    action = flask.request.json.get("action")

    # 2. 参数校验
    if not all([news_id, action]):
        return flask.jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ("accept", "reject"):
        return flask.jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 查询到指定的新闻数据
    try:
        news = News.query.get(news_id)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    if not news:
        return flask.jsonify(errno=RET.NODATA, errmsg="未查询到数据")

    if action == "accept":
        # 代表接受
        news.status = 0
    else:
        # 代表拒绝
        reason = flask.request.json.get("reason")
        if not reason:
            return flask.jsonify(errno=RET.PARAMERR, errmsg="请输入拒绝原因")
        news.status = -1
        news.reason = reason

    return flask.jsonify(errno=RET.OK, errmsg="OK")


@admin_blu.route('/news_edit')
@user_login_data
def news_edit():
    user = flask.g.user
    if not user:
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    page = flask.request.args.get("page", 1)
    keywords = flask.request.args.get('keywords', None)
    try:
        page = int(page)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    filters = [News.status == 0]
    if keywords:
        filters.append(News.title.contains(keywords))

    try:
        pagination_obj = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page,
                                                                                                constants.ADMIN_NEWS_PAGE_MAX_COUNT,
                                                                                                False)
        news_model_list = pagination_obj.items
        current_page = pagination_obj.page
        total_page = pagination_obj.pages
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据库查询错误')

    # 进行模型列表转字典列表
    news_json_list = []
    for news in news_model_list:
        news_json_list.append(news.to_dict())

    data = {
        "news_list": news_json_list,
        "total_page": total_page,
        "current_page": current_page
    }

    return flask.render_template('admin/news_edit.html', data=data)


@admin_blu.route('/news_edit_detail', methods=['GET', 'POST'])
@user_login_data
def news_edit_detail():
    user = flask.g.user
    if not user:
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    if flask.request.method == 'GET':

        news_id = flask.request.args.get('news_id')
        if not news_id:
            flask.abort(404)
        try:
            news_id = int(news_id)
        except Exception as e:
            flask.current_app.logger.error(e)
            return flask.render_template('admin/news_edit_detail.html', errmsg='参数错误')

        try:
            news = News.query.get(news_id)
        except Exception as e:
            flask.current_app.logger.error(e)
            return flask.render_template('admin/news_edit_detail.html', errmsg='查询数据错误')

        if not news:
            return flask.render_template('admin/news_edit_detail.html', errmsg='未查询到数据')

        try:
            category_model_list = Category.query.all()
        except Exception as e:
            flask.current_app.logger.error(e)
            return flask.render_template('admin/news_edit_detail.html', errmsg="查询数据错误")

        category_json_list = []
        for category in category_model_list:
            category_json = category.to_dict()
            if category.id == news.category_id:
                category_json['is_selected'] = True
            category_json_list.append(category_json)
        category_json_list.pop(0)

        data = {
            "news": news.to_dict(),
            "categories": category_json_list
        }

        return flask.render_template('admin/news_edit_detail.html', data=data)

    news_id = flask.request.form.get("news_id")
    title = flask.request.form.get("title")
    digest = flask.request.form.get("digest")
    content = flask.request.form.get("content")
    index_image = flask.request.files.get("index_image")
    category_id = flask.request.form.get("category_id")

    if not all([title, digest, content, category_id]):
        return flask.jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    try:
        news = News.query.get(news_id)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    if not news:
        return flask.jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")

    if index_image:
        try:
            index_image = index_image.read()
        except Exception as e:
            flask.current_app.logger.error(e)
            return flask.jsonify(errno=RET.PARAMERR, errmsg="参数有误")

        try:
            key = storage(index_image)
        except Exception as e:
            flask.current_app.logger.error(e)
            return flask.jsonify(errno=RET.THIRDERR, errmsg="上传图片错误")
        news.index_image_url = constants.QINIU_DOMIN_PREFIX + key

    news.title = title
    news.digest = digest
    news.content = content
    news.category_id = category_id

    return flask.jsonify(errno=RET.OK, errmsg="OK")

