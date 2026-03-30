import socket


DEFAULT_RECV_SIZE = 16384
DEFAULT_ENCODING = "utf-8"
FALLBACK_ENCODING = "utf-16"
MAX_RECV_RETRY = 5


def get_server_socket(port: int) -> socket.socket:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(False)
    server.bind(("", port))
    server.listen(5)
    return server


def get_data_from_socket(s: socket.socket) -> str:
    data_all = b''
    while True:
        try:
            data = s.recv(DEFAULT_RECV_SIZE)
            if data == b'':
                raise socket.error("Соединение разорвано!")
            data_all += data
            if len(data) < DEFAULT_RECV_SIZE:
                break
        except socket.timeout:
            break
    final_data = data_all.decode(DEFAULT_ENCODING).strip()
    return final_data
