import socket


DEFAULT_RECV_SIZE = 4096
DEFAULT_ENCODING = "utf-8"
FALLBACK_ENCODING = "utf-16"
MAX_RECV_RETRY = 5


def get_server_socket(port: int) -> socket.socket:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(False)
    server.bind(("", port))
    server.listen(5)
    return server


def get_data_from_socket(s: socket) -> str:
    retry = 0
    data_all = b''
    while True:
        try:
            data = s.recv(DEFAULT_RECV_SIZE)
        except socket.timeout:
            if retry == MAX_RECV_RETRY:
                raise
            retry += 1
            continue
        if data == b'':
            raise socket.error("Отказано в подключении!")
        if not data:
            break
        data_all += data
        if len(data) < DEFAULT_RECV_SIZE:
            break
    final_data = data_all.decode(DEFAULT_ENCODING).strip()
    return final_data
