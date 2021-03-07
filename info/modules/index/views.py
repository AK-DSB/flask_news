from . import index_blue
from ... import redis_store
import logging
from flask import current_app, render_template, session, jsonify, request, g
from info.models import User, News, Category


# 首页新闻列表
# 请求路径 /newsList
# 请求方式 GET
# 请求参数: cid,page,per_page
# 返回值； data数据
from ...utils.commons import user_login_data


@index_blue.route('/newslist')
def news_list():
    from ...utils.response_code import RET
    cid = int(request.args.get('cid', 1))
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    # 分页查询
    try:
        # 判断新闻的分类是否为1
        # filters = ''
        # if cid != 1:
        #     filters = (News.category_id == cid)
        # paginate = News.query.filter(filters).order_by(News.create_time.desc()).paginate(page=page, per_page=per_page, error_out=False)
        filters = [News.status == 0]
        if cid != 1:
            filters.append(News.category_id == cid)
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page=page,
                                                                                                         per_page=per_page,
                                                                                                         error_out=False)

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取新闻失败')
    # 获取到分页对象中的属性，总页数，当前页，当前页的对象列表
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items
    # 将对象转换成字典列表
    news_list = [item.to_dict() for item in items]
    # 携带数据，返回响应
    return jsonify(errno=RET.OK, errmsg='获取新闻成功', totalPage=totalPage, currentPage=currentPage, newsList=news_list)


@index_blue.route('/', methods=['GET', 'POST'], endpoint='index')
@user_login_data
def show_index():
    from ...utils.response_code import RET
    # 获取用户登录信息
    # user_id = session.get('user_id')
    # print(session)
    # user = None
    # if user_id:
    #     try:
    #         user = User.query.get(user_id)
    #     except Exception as e:
    #         current_app.logger.error(e)
    #         return jsonify(errno=RET.DATAERR, errmsg='获取用户失败')

    # 查询热门新闻 根据点击量查询前十条
    try:
        news = News.query.order_by(News.clicks.desc()).limit(10).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='获取新闻失败')
    # 将新闻对象列表转成字典列表
    news_list = [item.to_dict() for item in news]
    # 查询所有的分类数据
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='获取分类失败')
    # 将分类数据的对象转换成,字典列表
    category_list = [category.to_dict() for category in categories]
    data = {
        'user_info': g.user.to_dict() if g.user else '',
        'news_list': news_list,
        'category_list': category_list,
    }
    return render_template('news/index.html', data=data)


# 处理网站logo
@index_blue.route('/favicon.ico')
def get_web_log():
    # current_send_static_file('filename') 会自动去静态文件加中去寻找文件
    return current_app.send_static_file('news/favicon.ico')


# 统一处理404页面
@index_blue.route('/404')
@user_login_data
def page_not_found():
    data = {
        'user_info': g.user.to_dict() if g.user else ""
    }
    return render_template('news/404.html', data=data)