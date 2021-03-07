from flask import render_template, g, redirect, url_for, request, jsonify, current_app

from . import profile_blue

from ...utils.commons import user_login_data


# 我的关注
@profile_blue.route('/user_follow', methods=['POST', 'GET'])
@user_login_data
def user_follow():
    from info.models import News
    from info.utils.response_code import RET
    page = request.args.get('p', 1)
    try:
        page = int(page)
    except Exception as e:
        page = 1

    try:
        paginate = g.user.followed.paginate(page=page, per_page=2, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取作者失败')
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items
    author_list = [author.to_dict() for author in items]

    data = {
        "totalPage": totalPage,
        "currentPage": currentPage,
        "author_list": author_list,
    }

    return render_template('news/user_follow.html', data=data)


# 新闻列表
@profile_blue.route('/news_list')
@user_login_data
def news_list():
    from info.models import News
    from info.utils.response_code import RET
    page = request.args.get('p', 1)
    try:
        page = int(page)
    except Exception as e:
        page = 1

    try:
        paginate = News.query.filter(News.user_id == g.user.id).order_by(News.create_time.desc()).paginate(page=page, per_page=5, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取新闻失败')
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items
    news_list = [news.to_review_dict() for news in items]

    data = {
        "totalPage": totalPage,
        "currentPage": currentPage,
        "news_list": news_list,
    }

    return render_template('news/user_news_list.html', data=data)


# 新闻发布
@profile_blue.route('/news_release', methods=['GET', 'POST'])
@user_login_data
def news_release():
    from info.utils.response_code import RET
    from info.models import Category, News
    if request.method == 'GET':
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='获取新闻类别失败')
        category_list = [category.to_dict() for category in categories]
        return render_template('news/user_news_release.html', categories=category_list)
    news_dic = {
        "title": request.form.get('title'),
        "category_id": request.form.get('category_id'),
        "digest": request.form.get('digest'),
        "index_image_url": request.files.get('index_image'),
        "content": request.form.get('content'),
    }
    print(news_dic)
    if not all([news_dic.get('title'), news_dic.get('category_id'), news_dic.get('digest')]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')
    try:
        from info.utils import image_storage
        image_name = image_storage.image_storage(news_dic.get('index_image_url').read())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='七牛云异常')
    if not image_name:
        return jsonify(errno=RET.NODATA, errmsg='图片上传失败')
    from info import constants
    news_dic.update({'index_image_url': constants.QINIU_DOMIN_PREFIX + image_name})
    print(news_dic)
    news = News(source=g.user.nick_name, user_id=g.user.id, status=1, **news_dic)
    try:
        from info import db
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='新闻发布失败')
    return jsonify(errno=RET.OK, errmsg='新闻发布成功')


# 收藏新闻
@profile_blue.route('/collection')
@user_login_data
def collection():
    from info.models import News
    from info.utils.response_code import RET
    page = request.args.get('p', 1)
    try:
        page = int(page)
    except Exception as e:
        page = 1

    try:
        paginate = g.user.collection_news.order_by(News.create_time.desc()).paginate(page=page, per_page=5, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取新闻失败')
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items
    news_list = [news.to_dict() for news in items]

    data = {
        "totalPage": totalPage,
        "currentPage": currentPage,
        "news_list": news_list,
    }

    return render_template('news/user_collection.html', data=data)


# 密码修改
@profile_blue.route('/pass_info', methods=['GET', 'POST'])
@user_login_data
def pass_info():
    from info.utils.response_code import RET
    if request.method == 'GET':
        return render_template('news/user_pass_info.html')
    old_password = request.json.get('old_password')
    new_password = request.json.get('new_password')
    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')
    if not g.user.check_password(old_password):
        return jsonify(errno=RET.DATAERR, errmsg='密码错误')

    g.user.password = new_password
    from info import db
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg='修改成功')


# 头像修改
@profile_blue.route('/pic_info', methods=['GET', 'POST'])
@user_login_data
def pic_info():
    from ...utils import image_storage
    from info.utils.response_code import RET
    if request.method == 'GET':
        data = {
            'user_info': g.user.to_dict()
        }
        return render_template('news/user_pic_info.html', data=data)
    avatar = request.files.get('avatar')
    if not avatar:

        return jsonify(errno=RET.PARAMERR, errmsg='图片不能为空')
    try:
        image_name = image_storage.image_storage(avatar.read())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='七牛云异常')
    if not image_name:
        return jsonify(errno=RET.NODATA, errmsg='图片上传失败')
    g.user.avatar_url = image_name
    from ... import db
    db.session.commit()
    from info import constants
    data = {
        'avatar_url': constants.QINIU_DOMIN_PREFIX + image_name
    }
    return jsonify(errno=RET.OK, errmsg='上传成功', data=data)


# 获取/设置用户基本信息
# 请求路径:/user/base_info
# 请求方式:GET, POST
# 请求参数: POST请求参数,nick_name,signature,gender
@profile_blue.route('/base_info', methods=['GET', 'POST'], endpoint='base_info')
@user_login_data
def base_info():
    from ...utils.response_code import RET
    if request.method == 'GET':
        return render_template("news/user_base_info.html", user_info=g.user.to_dict())
    nick_name = request.json.get('nick_name')
    signature = request.json.get('signature')
    gender = request.json.get('gender')
    if not all([nick_name, signature, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')
    if gender not in ['MAN', 'WOMAN']:
        return jsonify(errno=RET.DATAERR, errmsg='性别异常')
    g.user.signature = signature
    g.user.nick_name = nick_name
    g.user.gender = gender
    from info import db
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg='修改成功')


@profile_blue.route('/info', endpoint='user_index')
@user_login_data
def user_index():
    if not g.user:
        return redirect(url_for('index.index'))
    data = {
        "user_info": g.user.to_dict(),
    }
    return render_template("news/user.html", data=data)