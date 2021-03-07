from . import news_blue
from flask import current_app, render_template, session, jsonify, request, abort, g

# 请求路径: /news/<int:news_id>
# 请求方式 GET
# 请求参数 news_id
# 返回值: detail.html data字典数据
from ...utils.commons import user_login_data
from ...utils.response_code import RET


# 关注
@news_blue.route('/followed_user', methods=['POST'])
@user_login_data
def followed_user():
    from info.models import User
    if not g.user:
        return jsonify(errno=RET.NODATA, errmsg='用户未登录')

    author_id = request.json.get('user_id')
    action = request.json.get('action')

    if not all([author_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')
    try:
        author = User.query.get(author_id)
    except Exception as e:
        current_app.ogger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取作者失败')

    if not author:
        return jsonify(errno=RET.NODATA, errmsg='该作者不存在')
    if g.user.id == author.id:
        return jsonify(errno=RET.NODATA, errmsg='自己不能关注自己')
    if action == 'follow':
        # 判断当前用户是否关注了该作者
        if g.user not in author.followers:
            author.followers.append(g.user)
    else:
        if g.user in author.followers:
            author.followers.remove(g.user)
    return jsonify(errno=RET.OK, errmsg='关注成功')


# 评论点赞
# 请求参数 comment_id, action, g.user
@news_blue.route('/comment_like', methods=['POST'])
@user_login_data
def comment_like():
    from info.models import Comment, CommentLike
    from info import db
    if not g.user:
        return jsonify(errno=RET.NODATA, errmsg='用户未登录')
    comment_id = request.json.get('comment_id')
    action = request.json.get('action')
    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')
    if action not in ['add', 'remove']:
        return jsonify(errno=RET.DATAERR, errmsg='操作类型有误')
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取评论失败')
    if not comment:
        return jsonify(errno=RET.NODATA, errmsg='评论不存在')
    try:
        if action == 'add':
            # 判断用户是否对当前评论点过赞
            comment_like = CommentLike.query.filter(CommentLike.user_id == g.user.id, CommentLike.comment_id == comment_id).first()
            print(comment_like)
            if not comment_like:
                comment_likes = CommentLike(user_id=g.user.id, comment_id=comment_id)

                db.session.add(comment_likes)

                # 该评论的点赞数量 +1
                comment.like_count += 1
                db.session.commit()
        else:
            # 判断用户是否对当前评论点过赞
            comment_like = CommentLike.query.filter(CommentLike.user_id == g.user.id, CommentLike.comment_id == comment_id).first()
            print(comment_like)
            if comment_like:
                from info import db
                db.session.delete(comment_like)

                # 该评论的点赞数量 +1
                if comment.like_count > 0:
                    comment.like_count -= 1
                db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='操作失败')
    return jsonify(errno=RET.OK, errmsg='操作成功')


# 新闻评论 请求方式 POST， 参数
@news_blue.route('/news_comment', methods=['POST'])
@user_login_data
def news_comment():
    from info.models import News, Comment
    from info import db
    if not g.user:
        return jsonify(errno=RET.NODATA, errmsg='请先登录')
    news_id = request.json.get('news_id')
    content = request.json.get('comment')
    parent_id = request.json.get('parent_id')
    if not all([news_id, content]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取新闻失败')
    comment_dic = {
        'user_id': g.user.id,
        'news_id': news_id,
        'content': content,
        'parent_id': parent_id
    }
    comment = Comment(**comment_dic)
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='评论失败')
    return jsonify(errno=RET.OK, errmsg='评论成功', data=comment.to_dict())


# 收藏与取消收藏 参数 新闻id action(是收藏还是取消收藏)
@news_blue.route('/news_collect', methods=['POST'])
@user_login_data
def news_collect():
    # 判断用户是否登录
    if not g.user:
        return jsonify(errno=RET.NODATA, errmsg='请先登录')
    # 获取参数 ajax提交的
    news_id = request.json.get('news_id')
    action = request.json.get('action')

    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')

    # 操作类型校验
    if action not in ['collect', "cancel_collect"]:
        return jsonify(errno=RET.DATAERR, errmsg='操作类型有误')

    # 根据新闻的编号取出新闻来
    try:
        from info.models import News
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取新闻失败')
    # 判断新闻对象是否存在
    if not news:
        return jsonify(errno=RET.NODATA, errmsg='新闻不存在')

    # 根据操作类型，进行收藏&取消收藏
    if action == 'collect':
        # 判断用户是否对该新闻做过收藏
        if news not in g.user.collection_news:
            g.user.collection_news.append(news)
    else:
        if news in g.user.collection_news:
            g.user.collection_news.remove(news)
    return jsonify(errno=RET.OK, errmsg='收藏成功')


@news_blue.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    from info.models import User, News, Category, Comment, CommentLike
    from ...utils.response_code import RET
    # 从session中取出用户数据
    # user_id = session.get('user_id')
    # user = None
    # if user_id:
    #     try:
    #         user = User.query.get(user_id)
    #     except Exception as e:
    #         current_app.logger.error(e)
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取新闻失败')
    if not news:
        abort(404)
    # 获取前6条热门新闻
    try:
        click_news = News.query.order_by(News.clicks.desc()).limit(6).all()
    except Exception as e:
        current_app.logger.error(e)
    # 将热门新闻对象列表转成字典列表
    click_news_list = [news.to_dict() for news in click_news]

    # 判断用户是否收藏过改文章
    is_collected = False
    # 用户需要登录并且该新闻在用户收藏过的新闻列表中
    if g.user:
        if news in g.user.collection_news:
            is_collected = True

    # 查询数据库中，该新闻的所有评论内容
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取评论失败')
    try:
        commentslikes = []
        if g.user:
            # 用户点赞过的所有评论
            commentslikes = CommentLike.query.filter(CommentLike.user_id == g.user.id).all()
        # 用户点赞过的所有评论id
        mylike_comment_ids = [commentLike.comment_id for commentLike in commentslikes]
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取点赞失败')
    comment_list = []
    for comment in comments:
        comm_dict = comment.to_dict()
        # 判断用户是否对评论点过赞  该评论是否在用户点赞列表里
        # if comment.id in mylike_comment_ids:
        comm_dict['is_like'] = comment.id in mylike_comment_ids
        print(comm_dict)
        comment_list.append(comm_dict)

    # 判断登录用户是否关注了新闻的作者
    is_followed = False
    if g.user and news.user:
        if g.user in news.user.followers:
            is_followed = True

    data = {
        'news_info': news.to_dict(),
        'user_info': g.user.to_dict() if g.user else "",
        'news_list': click_news_list,
        'is_collected': is_collected,
        'comments': comment_list,
        'is_followed': is_followed
    }
    return render_template('news/detail.html', data=data)