from flask import Blueprint, request, session, redirect

admin_blue = Blueprint('admin', __name__, url_prefix='/admin')

from . import views


# 使用请求钩子，拦截用户的请求
# 拦截的是普通用户
# 拦截的是访问了非登录页面
@admin_blue.before_request
def before_request():
    # 判断访问的是否非登录页面
    # print(request.url)
    # if request.url.endswith('/admin/login'):
    #     return
    # else:
    #     # 判断是否是管理员
    #     if session.get('is_admin'):
    #         pass
    #     else:
    #         return redirect('/')

    # 封装以上代码
    if not request.url.endswith('/admin/login'):
        if not session.get('is_admin'):
            return redirect('/')
