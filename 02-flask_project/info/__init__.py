import flask
import flask_sqlalchemy
import flask_wtf
import redis
import flask_session
import config

# 在Flask很多扩展里面都可以先初始化扩展的对象，然后再去调用 init_app 方法去初始化
info_db = flask_sqlalchemy.SQLAlchemy()


def create_app(config_pattern):
    app = flask.Flask(__name__)
    app.config.from_object(config.config[config_pattern])
    # 通过app初始化
    info_db.init_app(app)
    # 只做服务器验证工作，cookie中的 csrf_token 和表单中的 csrf_token 需要我们自己实现
    flask_wtf.csrf.CSRFProtect(app)
    redis_db = redis.StrictRedis(host=config.config['development'].REDIS_HOST, port=config.config['development'].REDIS_PORT)
    flask_session.Session(app)

    # 其实也可以返回元组 app, info_db
    return app