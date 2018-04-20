from . import index_blu
import flask


@index_blu.route('/')
def index():
    return flask.render_template('news/index.html')


@index_blu.route('/favicon.ico')
def favicon():
    # 添加静态文件的方法可参考flask添加静态文件与动态文件方法
    # 本质上就是路由的实现原理（寻找到自定义的视图函数的过程），可以看add_url_rule这个函数
    return flask.current_app.send_static_file('news/favicon.ico')
