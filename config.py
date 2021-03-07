# 设置配置信息
import logging
from datetime import timedelta

from redis import StrictRedis


class Config(object):
    # 调试信息
    DEBUG = True
    SECRET_KEY = '@@##$'

    # 数据库配置信息
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:FW249746@localhost:3306/info36?charset=utf8'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # 每当改变数据的内容之后请求结束后自动提交

    # redis 配置信息
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # session配置信息
    SESSION_TYPE = 'redis'  # 设置session存储类型
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)  # 指定session存储的redis服务器
    SESSION_USE_SIGNER = True  # 设置签名存储
    PERMANENT_SESSION_LIFETIME = timedelta(days=2)  # app.config源文件里找  设置session的有效期

    LEVEL_NAME = logging.DEBUG


# 开发环境配置信息配置信息
class DevelopConfig(Config):
    ENV = 'development'
    LEVEL_NAME = logging.DEBUG


# 生产(线上)环境配置信息
class ProductConfig(Config):
    DEBUG = False
    LEVEL_NAME = logging.ERROR


# 测试环境配置信息
class TestConfig(Config):
    ENV = 'test'


# 提供一个统一的访问入口
config_dic = {
    'develop': DevelopConfig,
    'product': ProductConfig,
    'test': TestConfig
}