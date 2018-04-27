import flask

from info.models import User
from . import admin_blu


@admin_blu.route('/index')
def index():
    return flask.render_template('admin/index.html')


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

