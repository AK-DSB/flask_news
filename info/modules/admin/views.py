from flask import render_template, request, jsonify, current_app, session, redirect, url_for, g
from werkzeug.security import check_password_hash
import time
from datetime import datetime, timedelta


from ...utils.commons import user_login_data
from ...utils.image_storage import image_storage
from ...utils.response_code import RET


from . import admin_blue


# 新闻分类增加与修改
@admin_blue.route('/add_category', methods=['POST'])
def add_category():
    from info import db
    from info.models import Category
    category_id = request.json.get('id')
    category_name = request.json.get('name')

    if not category_name:
        return jsonify(errno=RET.PARAMERR, errmsg='分类名字不能为空')
    if category_id:
        # 编辑
        try:
            category = Category.query.get(category_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='获取分类失败')
        if not category:
            return jsonify(errno=RET.NODATA, errmsg='分类不存在')
        category.name = category_name
        db.session.commit()
        return jsonify(errno=RET.OK, errmsg='修改成功')
    else:
        # 新增
        category = Category(name=category_name)
        try:
            db.session.add(category)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='分类增加失败')
        return jsonify(errno=RET.OK, errmsg='分类增加失败')


# 新闻分类管理
@admin_blue.route('/news_category')
def news_category():
    from info.models import Category
    category = Category.query.all()
    try:
        category_list = [category.to_dict() for category in category]
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/news_type.html', errmsg='获取分类失败')
    return render_template('admin/news_type.html', category_list=category_list)


# 新闻详情编辑
@admin_blue.route('/news_edit_detail', methods=['POST', 'GET'])
def news_edit_detail():
    from ... import constants, db
    from info.models import News, Category
    if request.method == 'GET':
        news_id = request.args.get('news_id')
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/news_edit_detail.html', errmsg='新汶获取失败')
        if not news:
            return render_template('admin/news_edit_detail.html', errmsg='新闻不存在')
        try:
            category = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/news_edit_detail.html', errmsg='获取分类失败')
        category_list = [category.to_dict() for category in category]
        return render_template('admin/news_edit_detail.html', news=news.to_dict(), category_list=category_list)
    news_id = request.form.get('news_id')
    title = request.form.get('title')
    digest = request.form.get('digest')
    content = request.form.get('content')
    index_image = request.files.get('index_image', '')
    category_id = request.form.get('category_id')
    if not all([news_id, title, digest, content, category_id, index_image]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取新闻失败')
    if not news:
        return jsonify(errno=RET.NODATA, errmsg='新闻不存在')
    # 上传图片
    try:
        image_name = image_storage(index_image.read())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='七牛云异常')
    if not image_name:
        return jsonify(errno=RET.NODATA, errmsg='图片上传失败')
    news.title = title
    news.category_id = category_id
    news.digest = digest
    news.content = content
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + image_name
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg='修改成功')


# 新闻板式编辑
@admin_blue.route('/news_edit')
def news_edit():
    page = int(request.args.get('p', 1))
    keywords = request.args.get('keywords', '')
    from info.models import News
    try:
        # 判断是否有搜索关键字
        filters = []
        if keywords:
            filters.append(News.title.contains(keywords))
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page=page,
                                                                                          per_page=10,
                                                                                          error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/news_edit.html', errmsg='获取人数失败')
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items
    news_list = [news.to_review_dict() for news in items]
    data = {
        'totalPage': totalPage,
        'currentPage': currentPage,
        'news_list': news_list
    }
    return render_template('admin/news_edit.html', data=data)


# 新闻审核
@admin_blue.route('/news_review_detail', methods=['GET', 'POST'])
def news_review_detail():
    from info.models import News
    from info import db
    if request.method == 'GET':
        news_id = request.args.get('news_id')
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/news_review_detail.html', errmsg='新闻获取失败')
        if not news:
            return render_template('admin/news_review_detail.html', errmsg='新闻不存在')
        return render_template('admin/news_review_detail.html', news=news.to_dict())
    news_id = request.json.get('news_id')
    action = request.json.get('action')
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')
    if action not in ['accept', 'reject']:
        return jsonify(errno=RET.DATAERR, errmsg='操作类型有误')
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取新闻失败')
    if not news:
        return render_template(errno=RET.NODATA, errmsg='新闻不存在')
    if action == 'accept':
        news.status = 0
        db.session.commit()
        return jsonify(errno=RET.OK, errmsg='新闻不存在')
    else:
        reason = request.json.get('reason')
        news.status = -1
        news.reason = reason
        db.session.commit()
        return jsonify(errno=RET.OK, errmsg='新闻不存在')


# 新闻列表
@admin_blue.route('/news_review')
def news_review():

    page = int(request.args.get('p', 1))
    keywords = request.args.get('keywords', '')
    from info.models import News
    try:
        # 判断是否有搜索关键字
        filters = [News.status != 0]
        if keywords:
            filters.append(News.title.contains(keywords))
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page=page,
                                                                                                        per_page=3,
                                                                                                        error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/news_review.html', errmsg='获取人数失败')
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items
    news_list = [news.to_review_dict() for news in items]
    data = {
        'totalPage': totalPage,
        'currentPage': currentPage,
        'news_list': news_list
    }
    return render_template('admin/news_review.html', data=data)


# 用户列表
@admin_blue.route('/user_list')
def user_list():
    page = int(request.args.get('p', 1))
    from info.models import User
    try:
        paginate = User.query.filter(User.is_admin == False).order_by(User.create_time.desc()).paginate(page=page, per_page=2, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/user_list.html', errmsg='获取人数失败')
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items
    user_list = [user.to_admin_dict() for user in items]
    data = {
        'totalPage': totalPage,
        'currentPage': currentPage,
        'user_list': user_list
    }
    return render_template('admin/user_list.html', data=data)


# 用户统计
@admin_blue.route('/user_count')
def user_count():
    from info.models import User
    # 获取用户总数
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/user_count.html', errmsg='获取总人数失败')
    # 获取月活人数
    localtime = time.localtime()
    try:
        # 先获取本月的1号的0点的，字符串数据
        month_start_time_str = "%s-%s-01" % (localtime.tm_year, localtime.tm_mon)
        # 根据字符串格式化日期对象
        month_start_time_date = datetime.strptime(month_start_time_str, '%Y-%m-%d')
        # 最后一次登录的事件大于等于本月的1号的0点钟的人数
        month_count = User.query.filter(User.last_login >= month_start_time_date, User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/user_count.html', errmsg='获取月活人数失败')
    # 获取日活人数
    try:
        # 先获取本日的0点的，字符串数据
        day_start_time_str = "%s-%s-%s" % (localtime.tm_year, localtime.tm_mon, localtime.tm_mday)
        # 根据字符串格式化日期对象
        day_start_time_date = datetime.strptime(day_start_time_str, '%Y-%m-%d')
        # 最后一次登录的事件大于等于本日0点钟的人数
        day_count = User.query.filter(User.last_login >= day_start_time_date, User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/user_count.html', errmsg='获取日活人数失败')
    # 获取活跃事件段内，对应的活跃人数
    activate_date = []  # 获取活跃的日期
    activate_count = []  # 获取活跃人数
    for i in range(0, 10):
        begin_date = day_start_time_date - timedelta(days=i)

        end_date = day_start_time_date - timedelta(days=i - 1)
        activate_date.append(begin_date.strftime('%m-%d'))
        every_day_active_count = User.query.filter(User.is_admin == False, User.last_login >= begin_date, User.last_login >= end_date).count()
        activate_count.append(every_day_active_count)

    # 将容器翻转
    activate_count.reverse()
    activate_date.reverse()
    # 携带数据渲染页面
    data = {
        'total_count': total_count,
        'month_count': month_count,
        'day_count': day_count,
        'activate_date': activate_date,
        'activate_count': activate_count,
    }
    return render_template('admin/user_count.html', data=data)


# 管理员首页
@admin_blue.route('/index')
@user_login_data
def admin_index():
    data = {
        'user_info': g.user.to_dict() if g.user else None
    }
    return render_template('admin/index.html', data=data)


@admin_blue.route('/login', methods=['POST', 'GET'])
def admin_login():
    from ...models import User
    if request.method == 'GET':
        # 判断管理员是否登陆过了
        if session.get('is_admin'):

            return redirect(url_for('admin.admin_index'))
        return render_template('admin/login.html')
    username = request.form.get('username')
    password = request.form.get('password')
    if not all([username, password]):
        return render_template('admin/login.html', errmsg='参数不全')
    try:
        admin = User.query.filter(User.nick_name == username, User.is_admin == True).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html', errmsg='查询失败')
    if not admin:
        return render_template('admin/login.html', errmsg='管理员不存在')
    if not admin.check_password(password=password):
        return render_template('admin/login.html', errmsg='密码错误')
    session['user_id'] = admin.id
    session['is_admin'] = True
    return redirect(url_for('admin.admin_index'))
