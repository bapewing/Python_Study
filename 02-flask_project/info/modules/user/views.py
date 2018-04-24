import flask

from info.utils.common import user_login_data
from . import user_blu


@user_blu.route('/user_info')
@user_login_data
def user_info():
    user = flask.g.user
    if not user:
        # return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
        return flask.redirect('/')
    data = {
        'user': user.to_dict()
    }
    return flask.render_template('user/user.html', data=data)


@user_blu.route('/user_base_info', methods=['GET', 'POST'])
def user_base_info():
    if flask.request.method == "GET":
        return flask.render_template('user/user_base_info.html')

