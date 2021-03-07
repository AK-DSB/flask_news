a = 'hello' if False else "world"
print(a)

# 使用g 对象配合装饰器使用
# 装饰器的作用: 给已经存在的方法，添加额外功能，而不应该改变原有函数的结构
# 解决办法: 不改变原有函数的结构
# 如果不使用wraps修饰函数 那么就会报错
# AssertionError: View function mapping is overwriting an existing endpoint function: wrapper

from functools import wraps
from flask import g, Flask


haha = Flask(__name__)


def user_data(view_func):
    @wraps(view_func)  # 写装饰器的时候 最好写上这句话
    def wrapper(*args, **kwargs):
        """
        wrapper..doc
        :param args:
        :param kwargs:
        :return:
        """
        print('额外的功能')
        # g.name = 'AK'
        return view_func(*args, **kwargs)

    return wrapper


@haha.route('/index1')
@user_data
def test1():
    """
    test..doc
    :return:
    """
    print('test1')
    # print(g.name)


@haha.route('/index2')
@user_data
def test2():
    """
    test2..doc
    :return:
    """
    print('test1')


if __name__ == '__main__':
    print(test1.__name__)
    print(test1.__doc__)

    print(test2.__name__)
    print(test2.__doc__)

    test1()
    c = {'a': 1}
    c.update([('b', 1)])
    print(c)