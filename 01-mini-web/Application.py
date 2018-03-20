

# WSGI 协议的实现是为了服务器通过框架访问数据库内的动态资源
def app(request_info, start_response):
    # path_info = request_info["PATH_INFO"]

    start_response("404 Not Found", [("Content-Type", "text/html")])
    return "Hello Kitty"