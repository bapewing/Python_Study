import time
import re


def get_time():
    return time.ctime()


def index():
    data_from_sql = "暂时没有数据"

    with open("./template/index.html", "r") as file:
        html_data = file.read()

    html_data = re.sub(r"\{%content%\}", data_from_sql, html_data)
    return html_data


def center():
    data_from_sql = "暂时没有数据"

    with open("./template/center.html", "r") as file:
        html_data = file.read()

    html_data = re.sub(r"\{%content%\}", data_from_sql, html_data)
    return html_data


# WSGI 协议的实现是为了服务器通过框架访问数据库内的动态资源
def app(request_info, start_response):
    path_info = request_info["PATH_INFO"]

    if path_info == "/gettime.py":
        start_response("200 OK", [("Server", "Python 3.0")])
        return get_time()
    elif path_info == "/index.py":
        start_response("200 OK", [("Server", "Python 3.0")])
        return index()
    elif path_info == "/center.py":
        start_response("200 OK", [("Server", "Python 3.0")])
        return center()
    else:
        start_response("404 Not Found", [("Content-Type", "text/html")])
        return "Hello Kitty"