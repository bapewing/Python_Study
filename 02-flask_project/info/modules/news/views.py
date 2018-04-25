import flask

from info import db
from info.models import User, News, Comment, CommentLike
from info.utils import constants
from info.utils.common import user_login_data
from info.utils.response_code import RET
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

    is_collected = False
    # 用户登录后才允许收藏和取消收藏
    if user:
        # collection_news 后面可以不用加all，因为sqlalchemy会在使用的时候去自动加载（getter懒加载）
        if news_model in user.collection_news:
            is_collected = True

    comments_model_list = []
    try:
        comments_model_list = Comment.query.filter(Comment.news_id == news_id).order_by(
            Comment.create_time.desc()).all()
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据库查询错误')

    comment_ids = []
    if user:
        try:
            # 1、查询当前新闻下所有的评论
            comment_ids = [comment.id for comment in comments_model_list]
            # 2、查询当前评论中哪些评论被当前用户点赞  in_ sql原生函数
            comment_likes = CommentLike.query.filter(CommentLike.comment_id.in_(comment_ids),
                                                     CommentLike.user_id == user.id).all()
            # 3、查询被点赞的评论的id
            comment_like_ids = [like_model.comment_id for like_model in comment_likes]
        except Exception as e:
            flask.current_app.logger.error(e)
            return flask.jsonify(errno=RET.DBERR, errmsg='数据库查询错误')

    comments_json_list = []
    for comment in comments_model_list:
        comment_json = comment.to_dict()
        comment_json['is_like'] = False
        if comment.id in comment_like_ids:
            comment_json['is_like'] = True
        comments_json_list.append(comment_json)

    data = {
        'user': user.to_dict() if user else None,
        'news': news_json_list,
        'detail_news': news_model.to_dict(),
        'is_collected': is_collected,
        'comments': comments_json_list
    }

    return flask.render_template('news/detail.html', data=data)


@news_blu.route('/news_collect', methods=['POST'])
@user_login_data
def collect():
    user = flask.g.user
    if not user:
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    parameters = flask.request.json
    news_id = parameters.get('news_id')
    action = parameters.get('action')
    if not all([news_id, action]):
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    if action not in ['collect', 'cancel_collect']:
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        news_id = int(news_id)  # 保证news_id为整数
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    # 查询新闻是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据库查询错误')

    if not news:
        return flask.jsonify(errno=RET.NODATA, errmsg='未查询到该新闻数据')
    # 开始执行数据库操作
    if action == 'collect':
        if news not in user.collection_news:
            user.collection_news.append(news)
        else:
            return flask.jsonify(errno=RET.DATAEXIST, errmsg='已经收藏')
    else:
        if news in user.collection_news:
            user.collection_news.remove(news)

    return flask.jsonify(errno=RET.OK, errmsg='操作成功')


@news_blu.route('/news_comment', methods=['POST'])
@user_login_data
def post_comment():
    user = flask.g.user
    if not user:
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    parameters = flask.request.json
    news_id = parameters.get('news_id', None)
    comment = parameters.get('comment', None)
    parent_id = parameters.get('parent_id', None)

    if not all([news_id, comment]):
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        news_id = int(news_id)
        if parent_id:
            parent_id = int(parent_id)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        news_model = News.query.get(news_id)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据库查询错误')

    if not news_model:
        return flask.jsonify(errno=RET.NODATA, errmsg='未查询到新闻数据')

    comment_model = Comment()
    comment_model.user_id = user.id
    comment_model.news_id = news_id
    comment_model.content = comment
    if parent_id:
        comment_model.parent_id = parent_id

    # 注意：没有使用SQLALCHEMY自动commit的功能是因为执行完retun才会进行数据commit
    # return时需要使用到评论的id
    try:
        db.session.add(comment_model)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据库插入错误')
    data = {
        'comment': comment_model.to_dict()
    }

    return flask.jsonify(errno=RET.OK, errmsg='评论成功', data=data)


@news_blu.route('/comment_like', methods=['POST'])
@user_login_data
def comment_like():
    user = flask.g.user
    if not user:
        return flask.jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    parameters = flask.request.json
    comment_id = parameters.get('comment_id', None)
    action = parameters.get('action', None)

    if not all([comment_id, action]):
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    if action not in ['add', 'remove']:
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        comment_id = int(comment_id)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        comment_model = Comment.query.get(comment_id)
    except Exception as e:
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据库查询错误')
    if not comment_model:
        return flask.jsonify(errno=RET.NODATA, errmsg='评论不存在')
    comment_like_model = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                  CommentLike.comment_id == comment_model.id).first()
    if action == 'add':
        if not comment_like_model:
            comment_like_model = CommentLike()
            comment_like_model.comment_id = comment_model.id
            comment_like_model.user_id = user.id
            db.session.add(comment_like_model)
            comment_model.like_count += 1
    else:
        if comment_like_model:
            # model没有delete方法
            # comment_like_model.delete()
            db.session.delete(comment_like_model)
            comment_model.like_count -= 1

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flask.current_app.logger.error(e)
        return flask.jsonify(errno=RET.DBERR, errmsg='数据库错误')

    return flask.jsonify(errno=RET.OK, errmsg='OK')
