import socket

from utils import receive_msgpack, send_msgpack


class Client:
    def __init__(self, host, port, computer_name):
        self.selected_options = None
        self.manager_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.manager_addr = (host, port)
        self.computer_name = computer_name

    def execute(self, options=None):  # options - the entire data collected by the machine as a dictionary
        if options is None:
            options = {}
        share_msg: dict = {
            "stage": "execution",
            "type": "SHARE",
            "data": {
                "options": {}
            }
        }
        share_msg["data"]["options"].update(options)

        send_msgpack(self.manager_socket, share_msg)
        exe_data = receive_msgpack(self.manager_socket)
        return exe_data

    def prep(self):
        prep_msg: dict = {
            "stage": "prep",
            "type": "REQUEST",
            "comp": self.computer_name
        }
        send_msgpack(self.manager_socket, prep_msg)

        request_msg = receive_msgpack(self.manager_socket)
        request_msg_data = request_msg.get('data')

        return request_msg_data.get('tle'), request_msg_data.get('time'), (request_msg_data.get('min'), request_msg_data.get('max'))

    def run(self):
        self.manager_socket.connect(self.manager_addr)

