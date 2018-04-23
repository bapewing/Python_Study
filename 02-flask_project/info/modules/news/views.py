import flask

from info.models import User, News
from info.utils import constants
from info.utils.common import user_login_data
from . import news_blu


@news_blu.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    user = flask.g.user
    # 排行榜数据显示
    news_model_list = []
    try:
        news_model_list = News.query.order_by(News.create_time.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        flask.current_app.logger.error(e)

    news_json_list = []
    for news in news_model_list:
        news_json_list.append(news.to_basic_dict())

    # 新闻详情展示
    news_model = None
    try:
        news_model = News.query.get(news_id)
    except Exception as e:
        flask.current_app.logger.error(e)
    if not news_model:
        flask.abort(404)
    news_model.clicks += 1

    is_collected = True

    data = {
        'user': user.to_dict() if user else None,
        'news': news_json_list,
        'detail_news': news_model.to_dict(),
        'is_collected': is_collected
    }
    return flask.render_template('news/detail.html', data=data)
