import time


def get_time():
    return time.ctime()


def index():

    return "index"


def center():

    return "center"


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