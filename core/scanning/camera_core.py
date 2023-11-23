import socket
from logging import getLogger
from random import choice, randint
from threading import Thread
from time import sleep

from libs.grades import BAD_CODES, GOOD_CODES
from libs.loggers import CAMERA_LOGGER
from libs.sockets import get_server_socket


class CameraEmul:
    def __init__(
        self, name: str,
        port: int = 23,
        gen_errors: bool = False,
        error_percent: int = 2,
        stack=1,
        drop_dm_percent: int = 0,
        add_code_quality: bool = False,
        bad_codes_percent: int = 0
    ):
        self.name = name
        self.server = get_server_socket(port)
        self._can_run = True
        self._t_processing = Thread(target=self._run_processing_thread)
        self._t_server = Thread(target=self._run_login_thread)
        self._connections: list[socket.socket] = []
        self._log = getLogger(CAMERA_LOGGER)
        self.gen_errors = gen_errors
        self.add_code_quality = add_code_quality
        self.bad_codes_percent = bad_codes_percent
        self.error_percent = error_percent
        self.stack = stack
        self.drop_dm_percent = drop_dm_percent
        self.stack_pool = []

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

    def _run_processing_thread(self):
        i = 0
        while 1:
            if self.connections:
                if not self.codes:
                    continue
                message = self.codes.popleft()
                orig_code = None
                if self.gen_errors and randint(0, 100) <= self.error_percent:
                    if randint(0, 1):
                        message = 'error'
                    else:
                        orig_code = message
                        message = "\n\r".join([message, message])
                else:
                    if self.add_code_quality:
                        if randint(0, 100) <= self.bad_codes_percent:
                            message += f'@{choice(BAD_CODES)}'
                        else:
                            message += f'@{choice(GOOD_CODES)}'
                    orig_code = message
                self.stack_pool.append(message)
                if len(self.stack_pool) == self.stack:
                    message = "\n\r".join(self.stack_pool)
                    self.stack_pool.clear()
                else:
                    continue
                if (
                    self.drop_dm_percent and
                    randint(0, 100) <= self.drop_dm_percent
                ):
                    self._log.info(
                        f"[{self.name}]<{len(self.codes)}> "
                        f"DROPPED: {message.strip()}"
                    )
                else:
                    for client in self._connections.copy():
                        try:
                            client.send(bytes(f"{message}\n\r", 'utf-8'))
                            self._log.info(
                                f"[{self.name}]<{len(self.codes)}> "
                                f"SENT: {message.strip()}"
                            )
                        except ConnectionAbortedError:
                            continue
                        except Exception as e:
                            self._log.warning(
                                f"[{self.name}]<{len(self.codes)}>"
                                f" ERROR: {client} {e}"
                            )
                            self._connections.remove(client)
