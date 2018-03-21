import time
import re

route_list = []


def create_route_list(path_info):
    def func1(func):
        route_list.append((path_info, func))

        def func2():
            pass

        return func2

    return func1


# 利用装饰器工厂的概念，创建函数时，自动创建路由列表
@create_route_list("/gettime.py")
def get_time():
    return time.ctime()


@create_route_list("/index.py")
def index():
    data_from_sql = "暂时没有数据"

    with open("./template/index.html", "r") as file:
        html_data = file.read()

    html_data = re.sub(r"\{%content%\}", data_from_sql, html_data)
    return html_data


@create_route_list("/center.py")
def center():
    data_from_sql = "暂时没有数据"

    with open("./template/center.html", "r") as file:
        html_data = file.read()

    html_data = re.sub(r"\{%content%\}", data_from_sql, html_data)
    return html_data


# django添加路由列表
# TODO:路由的概念？
# route_list = [("/gettime.py", get_time), ("/index.py", index), ("/center.py", center)]


# WSGI 协议的实现是为了服务器通过框架访问数据库内的动态资源
def app(request_info, start_response):
    path_info = request_info["PATH_INFO"]
    print(path_info)
    for url, func in route_list:
        print(url)
        if url == path_info:
            start_response("200 OK", [("Server", "Python 3.0")])
            return func()
    else:
        start_response("404 Not Found", [("Content-Type", "text/html")])
        return "Hello Kitty"
