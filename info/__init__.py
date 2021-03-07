from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, redirect
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, generate_csrf
from redis import StrictRedis
from config import config_dic
import logging

from info.modules.admin import admin_blue
from info.modules.passport import passport_blue
from info.modules.news import news_blue
from info.modules.profile import profile_blue
from info.utils.commons import hot_news_filter

redis_store = None

db = SQLAlchemy()


def create_app(config_name):

    app = Flask(__name__)

    config = config_dic.get(config_name)

    # 调用日志方法，记录程序运行信息
    log_file(config.LEVEL_NAME)

    app.config.from_object(config)

    # 创建SQLAlchemy对象，关联app
    db.init_app(app)

    # 创建redis对象
    global redis_store
    redis_store = StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)

    # 创建Session对象,读取APP中session配置信息
    Session(app=app)

    # 使用CSRFProtect保护app
    CSRFProtect(app=app)

    # 将首页蓝图index_blue注册到app中
    from info.modules.index import index_blue
    app.register_blueprint(index_blue)
    app.register_blueprint(passport_blue)
    app.register_blueprint(news_blue)
    app.register_blueprint(profile_blue)
    app.register_blueprint(admin_blue)

    # 使用请求钩子拦截所有的请求,统一的在cookie中设置csrf_token
    @app.after_request
    def after_request(resp):
        csrf_token = generate_csrf()
        resp.set_cookie('csrf_token', csrf_token)
        return resp

    # 将函数添加到系统默认的过滤器列表中
    app.add_template_filter(hot_news_filter, 'my_filter')

    # 统一处理404异常信息
    @app.errorhandler(404)
    def page_not_found(e):
        print(e)
        return redirect("/404")
    return app


def log_file(LEVEL_NAME):
    # 设置日志的记录等级
    logging.basicConfig(level=LEVEL_NAME)
    # 日志记录器，知名日志保存的路径，每个日志文件的最大大小，保存的日志文件个数上线
    file_log_handler = RotatingFileHandler('logs/log.txt', maxBytes=1024 * 1024 * 100, backupCount=10)
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    file_log_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_log_handler)




















