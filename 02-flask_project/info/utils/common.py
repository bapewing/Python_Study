import flask
import functools

from info.models import User


def do_index_class(index):
    if index == 0:
        return "first"
    elif index == 1:
        return "second"
    elif index == 2:
        return "third"


# 装饰器访问全局变量
def user_login_data(func):
    # TODO: 作用：可以保持当前装饰器去装饰的函数的 __name__ 的值不变
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        user_id = flask.session.get('user_id', None)
        user = None
        if user_id:
            try:
                user = User.query.get(user_id)
            except Exception as e:
                flask.current_app.logger.error(e)
        flask.g.user = user
        return func(*args, **kwargs)
    return wrapper


# 常规定义全局变量
# def query_user_data():
#     user_id = flask.session.get('user_id', None)
#     user = None
#     if user_id:
#         try:
#             user = User.query.get(user_id)
#         except Exception as e:
#             flask.current_app.logger.error(e)
#     flask.g.user = user