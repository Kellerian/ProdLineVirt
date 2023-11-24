import socket
from collections import deque
from logging import getLogger
from random import choice, randint
from threading import Thread
from time import sleep

from libs.grades import BAD_CODES, GOOD_CODES
from libs.loggers import CAMERA_LOGGER
from libs.sockets import get_server_socket


def is_error(percent: int) -> bool:
    return randint(0, 100) <= percent


class CameraEmul:
    def __init__(self, name: str, port: int = 23):
        self.name = name
        self.server = get_server_socket(port)
        self._can_run = True
        self._t_processing = Thread(target=self._run_processing_thread)
        self._t_server = Thread(target=self._run_login_thread)
        self._connections: list[socket.socket] = []
        self._log = getLogger(CAMERA_LOGGER)
        self._to_send: deque[str] = deque([])
        self._sent: deque[str] = deque([])

        self._noread, self._noread_errs = False, 0
        self._grade, self._grade_errs = False, 0
        self._dups, self._dups_errs = False, 0

    def set_noread(self, enabled: bool, error_percent: int = 0):
        self._noread, self._noread_errs = enabled, error_percent

    def set_grade(self, enabled: bool, error_percent: int = 0):
        self._grade, self._grade_errs = enabled, error_percent

    def set_duplicates(self, enabled: bool, error_percent: int = 0):
        self._dups, self._dups_errs = enabled, error_percent

    def start(self):
        self._can_run = True
        self._t_processing = Thread(target=self._run_processing_thread)
        self._t_server = Thread(target=self._run_login_thread)
        self._t_processing.start()
        self._t_server.start()

    def stop(self):
        self._can_run = False
        self._t_server.join()
        self._t_processing.join()

    def _run_login_thread(self):
        while self._can_run:
            try:
                connected_client, address = self.server.accept()
                connected_client.setblocking(True)
                self._connections.append(connected_client)
                self._log.info(f"[{self.name}] NEW CLIENT from {address}"
                               f" {connected_client}")
            except BlockingIOError:
                pass
            sleep(0.01)
        for client in self._connections.copy():
            client.close()
            self._connections.remove(client)

    def _can_process_data_to_send(self) -> bool:
        return len(self._connections) > 0 and len(self._to_send) > 0

    def _run_processing_thread(self):
        while self._can_run:
            if not self._can_process_data_to_send():
                sleep(0.01)
                continue
            processed_messages: list[tuple[str, bool]] = []
            while self._to_send:
                message = self._to_send.popleft()
                message, is_ok = self._process_message(message)
                processed_messages.append((message, is_ok))
            self._send_message([msg for msg, _ in processed_messages])
            self._sent.extend(
                [msg for msg, is_ok in processed_messages if is_ok]
            )

    def _process_message(self, message: str) -> tuple[str, bool]:
        is_good = True
        if self._noread and is_error(self._noread_errs):
            message = 'error'
            return message, False
        if self._grade and is_error(self._grade_errs):
            message += f'@{choice(BAD_CODES)}'
            is_good = False
        else:
            message += f'@{choice(GOOD_CODES)}'
        if self._dups and is_error(self._dups_errs):
            message = "\n\r".join([message, message])
        return message, is_good

    def _send_message(self, messages: list[str]):
        message = "\n\r".join(messages)
        for client in self._connections.copy():
            try:
                client.send(bytes(f"{message}\n\r", 'utf-8'))
                self._log.info(f"[{self.name}] SENT: {message}")
            except ConnectionAbortedError as e:
                self._log.warning(f"[{self.name}] {client} "
                                  f"потеряно соединение: {e}")
                self._connections.remove(client)
            except Exception as e:
                self._log.error(f"[{self.name}] {client} {e}")
                self._connections.remove(client)

    def send(self, messages: list[str]):
        self._to_send.extend(messages)

    def remove(self, data: str):
        self._sent.remove(data)

    def get_sent_data(self) -> list[str]:
        data_list = []
        while self._sent:
            data_list.append(self._sent.pop())
        return data_list
