from gevent import monkey
import socket
import re
import threading
import multiprocessing
import gevent

monkey.patch_all()  # 将阻塞程序的函数变成非阻塞，从而实现协程


class HTTPServer(object):

    def __init__(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 服务器重启地址重用
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("", 8080))
        server_socket.listen(128)
        self.server_socket = server_socket

    def start(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            print("接收来自%s的请求" % (client_address,))
            # 多线程
            # thd = threading.Thread(target=handle_client_request, args=(client_socket, ))
            # thd.start()
            # 多进程
            # process = multiprocessing.Process(target=handle_client_request, args=(client_socket, ))
            # process.start()
            # 进程间不共享全局变量，且各个进程之间互不影响
            # 子进程执行任务时，主进程socket要及时关闭，否则主进程不断消耗资源
            # client_socket.close()
            gevent.spawn(self.handle_client_request, client_socket)
            # join jionall 目的让主进程等待协程执行完毕再继续执行
            # 此处因为外层有个死循环 所以主进程不会结束 而添加join的话 又相当于单任务了

    def handle_client_request(self, df_socket):
        receive_data = df_socket.recv(4096)
        # print(receive_data.decode().splitlines())
        if not receive_data:
            print("未收到请求数据,断开连接")
            df_socket.close()
        request_info_list = receive_data.decode().splitlines()
        # 通过正则匹配分组获取请求的url路径
        # TODO:偶尔会出现数组越界的问题?
        url_resource = re.match("\w+\s+(\S+)", request_info_list[0]).group(1)

        if url_resource == "/":
            url_resource = "/index.html"
        # .py结尾就是请求动态资源
        if url_resource.endswith(".py"):
            import Application
            # Application模块一定要调用start_response函数，否则HTTPServer找不到response_header属性
            response_body = Application.app({"PATH_INFO": url_resource}, self.start_response)
            response = (self.response_header + "\r\n" + response_body).encode()
            df_socket.send(response)
            df_socket.close()
        else:
            try:
                with open("./static" + url_resource, "rb") as file:
                    response_body = file.read()
            except Exception as e:
                print("异常信息:%s" % e)
                response_header = "HTTP/1.1 404 Not Found\r\n"
                response_header += "Server:Python 1.0\r\n"
                response_body = "Request URL Error".encode()
            else:
                response_header = "HTTP/1.1 200 OK\r\n"
                response_header += "Server:Python 1.0\r\n"
            finally:
                response = (response_header + "\r\n").encode() + response_body
                df_socket.send(response)
                df_socket.close()

    def start_response(self, status, headers):
        self.response_header = "Http/1.1 %s\r\n" % status
        for header_name, header_value in headers:
            self.response_header += "%s:%s\r\n" % (header_name, header_value)


def main():
    hs = HTTPServer()
    hs.start()


if __name__ == '__main__':
    main()
