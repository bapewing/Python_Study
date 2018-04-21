from info.models import User
from . import index_blu
import flask


@index_blu.route('/')
def index():
    # 判断用户是否登录逻辑
    user_id = flask.session.get('user_id')
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            flask.current_app.logger(e)
    data = {
        'user': user.to_dict() if user else None
    }
    return flask.render_template('news/index.html', data=data)


@index_blu.route('/favicon.ico')
def favicon():
    # 添加静态文件的方法可参考flask添加静态文件与动态文件方法
    # 本质上就是路由的实现原理（寻找到自定义的视图函数的过程），可以看add_url_rule这个函数
    return flask.current_app.send_static_file('news/favicon.ico')

