import time
import re
import pymysql

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
    data_from_sql = ""
    try:
        conn = pymysql.connect(host="localhost", port=3306, db="stock_db", user="root", password="1017", charset="utf8")
        cur = conn.cursor()
        sql = "SELECT * FROM info"
        cur.execute(sql)
        for line in cur.fetchall():
            line_data = """
            <tr>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td><input type="button" value="添加" id="toAdd" name="toAdd" systemidvaule="%s"></td>
        </tr>
            """ % (line[0], line[1], line[2], line[3], line[4], line[5], line[6], line[7], line[1])
            data_from_sql += line_data
        conn.commit()
        with open("./template/center.html", "r") as file:
            html_data = file.read()
    except Exception as e:
        conn.rollback()
        return "获取数据失败" + str(e)
    else:
        html_data = re.sub(r"\{%content%\}", data_from_sql, html_data)
        return html_data
    finally:
        cur.close()
        conn.close()


@create_route_list("/center.py")
def center():
    data_from_sql = ""
    try:
        conn = pymysql.connect(host="localhost", port=3306, db="stock_db", user="root", password="1017", charset="utf8")
        cur = conn.cursor()
        sql = "SELECT i.code,i.short,i.chg,i.turnover,i.price,i.highs,f.note_info FROM info AS i INNER JOIN focus AS f ON i.id = f.info_id"
        cur.execute(sql)
        for line in cur.fetchall():
            line_data = """
              <tr>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>
                        <a type="button" class="btn btn-default btn-xs" href="/update/%s.html"> <span class="glyphicon glyphicon-star" aria-hidden="true"></span> 修改 </a>
                    </td>
                    <td>
                        <input type="button" value="删除" id="toDel" name="toDel" systemidvaule="%s">
                    </td>
                </tr>
              """ % (line[0], line[1], line[2], line[3], line[4], line[5], line[6], line[0], line[0])
            data_from_sql += line_data
        conn.commit()
        with open("./template/center.html", "r") as file:
            html_data = file.read()
    except Exception as e:
        return "获取数据失败" + str(e)
    else:
        html_data = re.sub(r"\{%content%\}", data_from_sql, html_data)
        return html_data
    finally:
        cur.close()
        conn.close()


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
