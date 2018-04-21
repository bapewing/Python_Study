import redis
import logging


# 添加项目相关配置
class Config(object):
    SECRET_KEY = "Python"
    # mysql配置
    SQLALCHEMY_DATABASE_URI = "mysql://root:1017@127.0.0.1:3306/information"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 请求结束时，SQLALCHEMY自动执行一次db.session.commit()操作
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    # redis配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 开启session标签
    SESSION_USE_SIGNER = True
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 86400 * 3
    # 设置日志等级
    LOG_LEVEL = logging.DEBUG


# TODO:类可以设置成私有类
class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = logging.WARNING


class TestingConfig(Config):
    DEBUG = True
    TESTING = True


# 参考源代码，字典形式存储配置，类似枚举
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}
