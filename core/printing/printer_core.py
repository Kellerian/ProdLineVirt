import random
from collections import deque
import socket
from threading import Thread
from logging import getLogger
from time import sleep

from core.printing.chw import get_chw_codes
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
        self._files_list: list[str] = []
        self._mac: str = "02:00:00:%02x:%02x:%02x" % (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )

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

    def clear_buffer(self) -> None:
        self._print_buffer.clear()

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
                sleep(0.01)
                pass
        for client in self._connections.copy():
            client.close()
            self._connections.remove(client)

    def _run_processing_thread(self):
        while self._can_run:
            for client in self._connections.copy():
                self._process_client(client)
            else:
                sleep(0.01)
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
            except socket.error:
                pass
            self._connections.remove(client)
            return
        if not msg_received:
            return
        if self._process_status_requests(msg_received, client):
            return
        self._log.debug(
            f"[{self.name}] MSG FROM {client.getsockname()}: {msg_received}"
        )
        dm_extracted = extract_barcode_value_from_template(msg_received)
        if not dm_extracted:
            return
        self._log.info(f"[{self.name}] BARCODES: {dm_extracted}")
        for code in dm_extracted:
            self._add_barcode_to_buffer(code)

    def _add_barcode_to_buffer(self, barcode: str):
        processed_code = process_barcode(barcode)
        self._print_buffer.append(processed_code)
        self._printed += 1
        self._log.info(
            f"[{self.name}] <{self._printed}> PRINTED: {barcode}"
        )

    def _process_status_requests(
        self, msg_received: str, client: socket.socket
    ) -> bool:
        current_buffer_size = len(self._print_buffer)
        # available_space = self._max_size - current_buffer_size
        response_text = ""
        # self._log.debug(
        #     f"[{self.name}] CHECKING IF STATUS REQUEST: {msg_received}"
        # )
        # TEST_RESPONSE = [
        #     '\x20' if self._print_buffer else '\x00',
        #     f"0,0,0,0,{current_buffer_size}"
        # ]
        if f"{chr(27)}!?" in msg_received:
            response_text = '\x20' if self._print_buffer else '\x00'
            # response_text = TEST_RESPONSE[random.randint(0, 1)]
        elif f"{chr(27)}!." in msg_received:
            response_text = "CLEAR BUFFER"
        elif "~!F" in msg_received:
            if self._files_list:
                response_text = "\r".join(self._files_list)
            else:
                response_text = chr(26)
        elif "DOWNLOAD F" in msg_received:
            parts = msg_received.split(",")
            self._files_list.append(parts[1])
        elif "~S,CHECK" in msg_received:
            response_text = '00'
        elif "~S,STATUS" in msg_received:
            response_text = f'00,{current_buffer_size:05d}'
        elif "OUT @LABEL" in msg_received:
            response_text = f"{self._printed}"
        elif "~HS" in msg_received:
            response_text = f"0,0,0,0,{current_buffer_size}"
            # response_text = TEST_RESPONSE[random.randint(0, 1)]
        elif "~S,LABEL" in msg_received:
            response_text = f"{current_buffer_size}"
        # Эмуляция чеквейра
        elif "START" in msg_received:
            response_text = "START ON"
        elif "STOP" in msg_received:
            client.sendall("STOP CMD".encode())
            client.sendall("STOP LINE".encode())
            return True
        elif "ORDER" in msg_received:
            order_id = int(msg_received.split("=")[1])
            codes = get_chw_codes(
                order_id, '127.0.0.1', 6432, 'ekoniva_chw'
            )
            if codes:
                for code in codes:
                    self._add_barcode_to_buffer(code)
                response_text = f"ORDER SELECT={order_id}"
            else:
                response_text = f"Отсутствуют коды в БД для заказа {order_id}"
        elif "STATE" in msg_received:
            response_text = "STATE 0x248A = RUNNING"
        elif "STATE=1" in msg_received:
            response_text = "STATE 0x248A = RUNNING"
        elif "BOXCLOSE" in msg_received:
            response_text = "OK"
        elif "SPLIT" in msg_received:
            response_text = "OK"
        elif "~S,BUFCLR" in msg_received:
            response_text = "CLEAR BUFFER"
        elif msg_received in (
            'OUT GETSETTING$("CONFIG", "NET", "MAC ADDRESS")',
            '^NMACADDR'
        ):
            response_text = self._mac
        elif "~S,FEED" in msg_received:
            return True
        else:
            return False
        # self._log.debug(f"[{self.name}] STATUS RESPONSE: {response_text}")
        if response_text == "CLEAR BUFFER":
            self.clear_buffer()
        else:
            # self._log.debug(f"[{self.name}] RESP TO {client.getsockname()}: "
            #                 f"{response_text}")
            client.sendall(response_text.encode())
        return True
