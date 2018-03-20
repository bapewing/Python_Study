import socket
import re


def handle_client_request(df_socket):
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


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 服务器重启地址重用
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("", 8080))
    server_socket.listen(128)

    while True:
        client_socket, client_address = server_socket.accept()
        print("接收来自%s的请求" % (client_address,))
        handle_client_request(client_socket)


if __name__ == '__main__':
    main()
