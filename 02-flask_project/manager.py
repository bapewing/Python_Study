import flask
import flask_sqlalchemy
import flask_wtf
import redis


# 添加项目相关配置
class Config(object):
    DEBUG = True
    # mysql配置
    SQLALCHEMY_DATABASE_URI = "mysql://root:1017@127.0.0.1:3306/information"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # redis配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379


app = flask.Flask(__name__)
app.config.from_object(Config)
info_db = flask_sqlalchemy.SQLAlchemy(app)
# 只做服务器验证工作，cookie中的 csrf_token 和表单中的 csrf_token 需要我们自己实现
flask_wtf.csrf.CSRFProtect(app)
redis_db = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)


@app.route("/")
def index():
    return "index"


if __name__ == '__main__':
    app.run()