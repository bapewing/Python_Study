import flask
import flask_sqlalchemy
import flask_wtf
import redis
import flask_session
import flask_script
import config


app = flask.Flask(__name__)
app.config.from_object(config.config['development'])
info_db = flask_sqlalchemy.SQLAlchemy(app)
# 只做服务器验证工作，cookie中的 csrf_token 和表单中的 csrf_token 需要我们自己实现
flask_wtf.csrf.CSRFProtect(app)
redis_db = redis.StrictRedis(host=config.config['development'].REDIS_HOST, port=config.config['development'].REDIS_PORT)
flask_session.Session(app)
manager = flask_script.Manager(app)