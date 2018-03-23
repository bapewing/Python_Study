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
@create_route_list("/gettime.html")
def get_time(path_info):
    return time.ctime()


@create_route_list("/index.html")
def index(path_info):
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
        with open("./template/index.html", "r") as file:
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


@create_route_list("/center.html")
def center(path_info):
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


@create_route_list("/add/\d{6}\.html")
def add(path_info):
    code = re.match("/add/(\d{6})\.html", path_info).group(1)
    try:
        conn = pymysql.connect(host="localhost", port=3306, db="stock_db", user="root", password="1017", charset="utf8")
        cur = conn.cursor()
        # 添加之前先判断，数据库中是否有要添加的记录
        sql = "SELECT * FROM focus WHERE info_id = (SELECT id FROM info WHERE code = %s)"
        if cur.execute(sql, [code]):
            return "已经收藏过该支股票"
        sql = "INSERT INTO focus (info_id) SELECT id FROM info WHERE code = %s"
        cur.execute(sql, [code])
        conn.commit()
    except Exception as e:
        conn.rollback()
        return "添加失败" + str(e)
    else:
        return "添加成功"
    finally:
        cur.close()
        conn.close()


@create_route_list("/del/\d{6}\.html")
def delete(path_info):
    code = re.match("/del/(\d{6})\.html", path_info).group(1)
    try:
        conn = pymysql.connect(host="localhost", port=3306, db="stock_db", user="root", password="1017", charset="utf8")
        cur = conn.cursor()
        sql = "DELETE FROM focus WHERE info_id =  (SELECT id FROM info WHERE code = %s)"
        cur.execute(sql, [code])
        conn.commit()
    except Exception as e:
        conn.rollback()
        return "删除失败" + str(e)
    else:
        return "删除成功"
    finally:
        cur.close()
        conn.close()


@create_route_list("/update/\d{6}\.html")
def update(path_info):
    code = re.match(r"/update/(\d{6})\.html", path_info).group(1)
    try:
        conn = pymysql.connect(host="localhost", port=3306, db="stock_db", user="root", password="1017", charset="utf8")
        cur = conn.cursor()
        sql = "SELECT note_info FROM focus WHERE info_id = (SELECT id FROM info WHERE code = %s)"
        if cur.execute(sql, [code]) == 0:
            return "ERROR"
        # TODO:为什么不能打印fetchone()信息
        note_info = cur.fetchone()[0]
        conn.commit()
        with open("./template/update.html", "r") as file:
            html_data = file.read()
    except Exception as e:
        conn.rollback()
        return "更新备注信息失败" + str(e)
    else:
        # 添加修改备注信息页模板，并添加动态资源
        html_data = re.sub(r"\{%code%\}", code, html_data)
        html_data = re.sub(r"\{%note_info%\}", note_info, html_data)
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
    # 现在路由列表存放的是正则的路径，所以不能使用==去判断
    for url, func in route_list:
        print(url)
        # if url == path_info:
        if re.match(url, path_info):
            start_response("200 OK", [("Server", "Python 3.0")])
            return func(path_info)
    else:
        start_response("404 Not Found", [("Content-Type", "text/html")])
        return "Hello Kitty"
