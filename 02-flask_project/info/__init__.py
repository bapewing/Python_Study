import flask
import flask_sqlalchemy
import flask_wtf
import redis
import flask_session
from flask_wtf.csrf import generate_csrf

import config
import logging
import logging.handlers

# 在Flask很多扩展里面都可以先初始化扩展的对象，然后再去调用 init_app 方法去初始化
db = flask_sqlalchemy.SQLAlchemy()
# Python3.6之后新增变量类型注释
redis_db = None  # type:redis.StrictRedis


# redis_db: redis.StrictRedis = None


def setup_log(config_pattern):
    # 设置日志的记录等级
    logging.basicConfig(level=config.config[config_pattern].LOG_LEVEL)
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = logging.handlers.RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


def create_app(config_pattern):
    # 配置日志
    setup_log(config_pattern)
    app = flask.Flask(__name__)
    app.config.from_object(config.config[config_pattern])
    # 通过app初始化
    db.init_app(app)
    # 帮我们做了：从cookie中取出随机值，从表单中取出随机，然后进行校验，并且响应校验结果
    # 我们需要做：1. 在返回响应的时候，往cookie中添加一个csrf_token，2. 并且在表单中添加一个隐藏的csrf_token
    # 而我们现在登录或者注册不是使用的表单，而是使用 ajax 请求，所以我们需要在 ajax 请求的时候带上 csrf_token 这个随机值就可以了
    # 请求服务器使用post，put，delete等需要修改服务器数据的操作都需要csrf保护
    # bug：不关闭保护的话，请求400
    flask_wtf.csrf.CSRFProtect(app)
    global redis_db
    redis_db = redis.StrictRedis(host=config.config['development'].REDIS_HOST,
                                 port=config.config['development'].REDIS_PORT, decode_responses=True)
    flask_session.Session(app)

    # bug：ImportError: cannot import name 'db'
    # 循环导入时，db还没有创建，所以导入失败
    from info.utils.common import do_index_class
    app.add_template_filter(do_index_class, 'index_class')

    # bug：依然会造成循环导入的问题
    from info.utils.common import user_login_data

    @app.errorhandler(404)
    @user_login_data
    def page_not_found(e):
        user = flask.g.user
        data = {'user': user.to_dict() if user else None}
        return flask.render_template('news/404.html', data=data)

    # CSRF对服务器进行数据操作的请求方法都需要设置保护，统一在hook时设置
    # bug：400 需要将设置在 flask_session.Session(app)之后，否则发送请求时使用到redis数据库会报错
    @app.after_request
    def after_request(response):
        csrf_token = generate_csrf()
        response.set_cookie('csrf_token', csrf_token)
        return response

    # 注册相关蓝图
    # 顶部导入蓝图的话，会出现循环导入的bug，解决：什么时候注册蓝图什么时候导入蓝图
    from info.modules.index import index_blu
    app.register_blueprint(index_blu)
    from info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)
    from info.modules.news import news_blu
    app.register_blueprint(news_blu)
    from info.modules.user import user_blu
    app.register_blueprint(user_blu)
    from info.modules.admin import admin_blu
    app.register_blueprint(admin_blu)

    # 其实也可以返回元组 app, info_db
    return app
