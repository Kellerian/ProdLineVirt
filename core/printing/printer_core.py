from collections import deque
import socket
from threading import Thread
from logging import getLogger
from time import sleep

from libs.loggers import PRINTER_LOGGER
from libs.sockets import get_data_from_socket, get_server_socket
from libs.template_parsers import (
    extract_barcode_value_from_template, process_barcode
)


class PrinterEmul:
    def __init__(self, name: str, port: int, buffer_size: int):
        self.name = name
        self.server = get_server_socket(port)
        self._can_run = True
        self._t_processing = Thread(target=self._run_processing_thread)
        self._t_server = Thread(target=self._run_login_thread)
        self._connections: list[socket.socket] = []
        self._log = getLogger(PRINTER_LOGGER)
        self._max_size = buffer_size
        self._print_buffer: deque[str] = deque([])
        self._printed = 0

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

    def buffer_size(self) -> int:
        return len(self._print_buffer)

    def set_buffer_size(self, size: int):
        self._max_size = size

    def buffer_data(self) -> list[str]:
        return list(self._print_buffer)

    def remove(self, code: str):
        self._print_buffer.remove(code)

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
        while self._can_run:
            for client in self._connections.copy():
                self._process_client(client)
        for client in self._connections.copy():
            client.close()
            self._connections.remove(client)

    def _process_client(self, client: socket.socket):
        try:
            msg_received = get_data_from_socket(client)
        except UnicodeDecodeError:
            msg_received = ""
        except Exception as e:
            self._log.critical(f"<{self.name}> {client} {e}")
            try:
                client.close()
            except:
                pass
            self._connections.remove(client)
            return
        if not msg_received:
            return
        self._log.debug(f"[{self.name}] NEW MESSAGE: {msg_received}")
        if self._process_status_requests(msg_received, client):
            return
        dm_extracted = extract_barcode_value_from_template(msg_received)
        if not dm_extracted:
            return
        self._log.info(f"[{self.name}] BARCODE: {dm_extracted}")
        self._add_barcode_to_buffer(process_barcode(dm_extracted))

    def _add_barcode_to_buffer(self, barcode: str):
        self._print_buffer.append(barcode)
        self._printed += 1
        self._log.info(
            f"[{self.name}] <{self._printed}> PRINTED: {barcode}"
        )

    def _process_status_requests(
        self, msg_received: str, client: socket.socket
    ) -> bool:
        current_buffer_size = len(self._print_buffer)
        available_space = self._max_size - current_buffer_size
        response_text = ""
        self._log.debug(f"[{self.name}] CHECKING IF STATUS REQUEST: "
                        f"{msg_received}")
        if msg_received == f"{chr(27)}!?":
            response_text = '\x00'
        elif msg_received == "~S,CHECK":
            response_text = '00'
        elif msg_received == "OUT @LABEL":
            response_text = f"{self._printed}"
        elif msg_received == "~HS":
            response_text = f"0,0,0,0,{current_buffer_size}"
        elif msg_received == "~S,LABEL":
            response_text = f"{available_space}"
        if not response_text:
            return False
        self._log.debug(f"[{self.name}] STATUS RESPONSE: {response_text}")
        client.send(response_text.encode())
        return True
