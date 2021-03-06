from src.models.Blockchain import Blockchain
import json
import socket
import logging
import threading
import traceback


class Server:
    sock = None
    client_dict = {}

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        self.blockchain = Blockchain("Genesis")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = socket.gethostbyname(socket.gethostname())
        self.server_port = 7000
        self.sock.bind((self.server_address, self.server_port))
        thread = threading.Thread(target=self.receive_message)
        thread.start()

    def receive_message(self):  # Получаем сообщения предупреждения или блоки

        while True:
            try:
                data, addr = self.sock.recvfrom(1024)  # buffer size is 1024 bytes
                logging.info(str(data.decode()))
                logging.info(str(addr))
                self.client_address, self.client_port = addr[0], addr[1]
                self.client_dict[addr[0]] = addr[1]
                self.define_type_message(data.decode(), self.client_address, self.client_port)
            except Exception as e:
                logging.error(str(e))
                print(traceback.format_exc())

    def send_block(self, block, client_ip, client_port):
        for ip in self.client_dict.keys():
            if ip != client_ip:
                self.sock.sendto(block.encode(), (ip, client_port))

    def send_blockchain(self, client_ip, client_port):
        json_encoder = json.JSONEncoder()
        self.sock.sendto(json_encoder.encode(self.blockchain.chain).encode(), (client_ip, client_port))

    def send_notifi(self, client_ip, client_port):
        for ip in self.client_dict.keys():
            if ip != client_ip:
                self.sock.sendto("Notification!".encode(), (ip, client_port))

    def define_type_message(self, mes, client_ip, client_port):
        if mes.find("Notification") != -1:
            self.send_notifi(client_ip, client_port)
            # TODO call Notification on main_window
        elif mes.find("hello") != -1:
            self.send_blockchain(client_ip, client_port)
        else:
            data = json.JSONDecoder().decode(mes)
            self.blockchain.chain.append(data)
            self.send_block(data, client_ip, client_port)


serv = Server()
