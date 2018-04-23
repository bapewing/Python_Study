import flask

from info.models import User, News
from info.utils import constants
from info.utils.common import user_login_data
from . import news_blu


@news_blu.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    user = flask.g.user
    news_model_list = []
    try:
        news_model_list = News.query.order_by(News.create_time.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        flask.current_app.logger.error(e)

    new_json_list = []
    for news in news_model_list:
        new_json_list.append(news.to_basic_dict())
    data = {
        'user': user.to_dict() if user else None,
        'news': new_json_list
    }
    return flask.render_template('news/detail.html', data=data)
