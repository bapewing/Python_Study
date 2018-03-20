import socket


def handle_client_request(df_socket):
    receive_data = df_socket.recv(4096)
    print(receive_data.decode())


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
