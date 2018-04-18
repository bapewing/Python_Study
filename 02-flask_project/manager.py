import flask
import flask_sqlalchemy
import flask_wtf
import redis
import flask_session
import flask_script
import flask_migrate


# 添加项目相关配置
class Config(object):
    DEBUG = True
    SECRET_KEY = "iECgbYWReMNxkRprrzMo5KAQYnb2UeZ3bwvReTSt+VSESW0OB8zbglT+6rEcDW9X"
    # mysql配置
    SQLALCHEMY_DATABASE_URI = "mysql://root:1017@127.0.0.1:3306/information"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # redis配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 开启session标签
    SESSION_USE_SIGNER = True
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 86400 * 3


app = flask.Flask(__name__)
app.config.from_object(Config)
info_db = flask_sqlalchemy.SQLAlchemy(app)
# 只做服务器验证工作，cookie中的 csrf_token 和表单中的 csrf_token 需要我们自己实现
flask_wtf.csrf.CSRFProtect(app)
redis_db = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)
flask_session.Session(app)
manager = flask_script.Manager(app)
# 将app与db关联
flask_migrate.Migrate(app, info_db)
manager.add_command('db', flask_migrate.MigrateCommand)


@app.route("/")
def index():
    flask.session['name'] = "wxy"
    flask.session['age'] = 18
    return "index"


if __name__ == '__main__':
    manager.run()