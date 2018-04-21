from info.models import User, News
from info.utils import constants
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

    news_model_list = []
    try:
        news_model_list = News.query.order_by(News.clicks.desc()).limit(constants.USER_COLLECTION_MAX_NEWS)
    except Exception as e:
        flask.current_app.logger(e)

    # 对象列表转成字典列表
    news_json_list = []
    for news in news_model_list:
        news_json_list.append(news.to_dict())

    data = {
        'user': user.to_dict() if user else None,
        'news': news_json_list
    }
    return flask.render_template('news/index.html', data=data)


@index_blu.route('/favicon.ico')
def favicon():
    # 添加静态文件的方法可参考flask添加静态文件与动态文件方法
    # 本质上就是路由的实现原理（寻找到自定义的视图函数的过程），可以看add_url_rule这个函数
    return flask.current_app.send_static_file('news/favicon.ico')

