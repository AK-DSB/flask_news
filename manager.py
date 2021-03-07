"""
相关配置信息:
1.数据库配置
2.redis配置
3.session配置
4.CSRFProtect配置
"""
# 调用方法,获取app
from flask import current_app

from info import create_app, db, models
from flask_script import Manager, Server
from flask_migrate import Migrate, MigrateCommand


app = create_app('develop')
manager = Manager(app)

Migrate(app=app, db=db)

manager.add_command('db', MigrateCommand)
manager.add_command('runserver', Server(host='0.0.0.0', port=5000))


# 定义方法 创建管理员对象
@manager.option('-u', '--username', dest='username')
@manager.option('-p', '--password', dest='password')
@manager.option('-m', '--mobile', dest='mobile')
def create_superuser(username, password, mobile):
    admin = models.User()
    admin.nick_name = username
    admin.mobile = mobile
    admin.password = password
    admin.is_admin = True
    try:
        db.session.add(admin)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return '创建失败'
    return '创建成功'


if __name__ == '__main__':
    manager.run()