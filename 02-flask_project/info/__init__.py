import flask
import flask_sqlalchemy
import flask_wtf
import redis
import flask_session
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
    print(app.url_map)
    app.config.from_object(config.config[config_pattern])
    # 通过app初始化
    db.init_app(app)
    # 只做服务器验证工作，cookie中的 csrf_token 和表单中的 csrf_token 需要我们自己实现
    # bug：不关闭保护的话，请求400
    # flask_wtf.csrf.CSRFProtect(app)
    global redis_db
    redis_db = redis.StrictRedis(host=config.config['development'].REDIS_HOST,
                                 port=config.config['development'].REDIS_PORT, decode_responses=True)
    flask_session.Session(app)
    # 注册相关蓝图
    # 顶部导入蓝图的话，会出现循环导入的bug，解决：什么时候注册蓝图什么时候导入蓝图
    from info.modules.index import index_blu
    app.register_blueprint(index_blu)
    from info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)

    # 其实也可以返回元组 app, info_db
    return app
