import socket
from .utils import receive_msgpack, send_msgpack


class Client:
    def __init__(self, host, port, computer_name):
        """
        Initializes the Client with the Manager address and the current computer name. (operational)

        Args:
            host (str): Hostname or IP address of the server.
            port (int): Port number of the server.
            computer_name (str): Name of the computer to identify itself to the server.
        """
        self.selected_options = None
        self.manager_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.manager_addr = (host, port)
        self.computer_name = computer_name

    def execute(self, options={}):  # options - the entire data collected by the machine as a dictionary
        """
        Sends an execution command to the server with optional data and receives a response.

        Args:
            options (dict): A dictionary containing data collected by the machine, default is empty.

        Returns:
            dict: Data received from the Manager computer as a response to the execution request.
        """
        
         # Prepare message to share execution data with the server
        share_msg: dict = {
            "stage": "execution",
            "type": "SHARE",
            "data": {
                "options": {}
            }
        }
         # Prepare message to share execution data with the server
        share_msg["data"]["options"].update(options)

        # Send the message to the server using msgpack and receive the response
        try:
            send_msgpack(self.manager_socket, share_msg)
            exe_data = receive_msgpack(self.manager_socket)
        except OSError:
            return {}
        if not exe_data:
            return {}
        
        # Return only the 'data' part of the response
        return exe_data.get("data", {})

    def prep(self):
        """
        Sends a preparation request to the Manager computer and receives initial setup data.

        Returns:
            tuple: A tuple containing TLE (satellite orbit data), current time data, and night probability.
        """
        
         # Prepare a message to request setup data from the server
        prep_msg: dict = {
            "stage": "prep",
            "type": "REQUEST",
            "comp": self.computer_name
        }
        # Send the preparation message and receive the response
        send_msgpack(self.manager_socket, prep_msg)

        # Parse the response message and extract the necessary data
        request_msg = receive_msgpack(self.manager_socket)
        request_msg_data = request_msg.get('data')
        print(request_msg_data) # Debug print to show received data
        
         # Return TLE, time, and night probability from the response
        return (
            request_msg_data.get('tle'),
            request_msg_data.get('time'),
            int(request_msg_data.get('night_probability')),
            request_msg_data.get('simulation_duration'),
            request_msg_data.get('load_command_file'),
            request_msg_data.get('command_file_content'),
        )

    def run(self):
         # Connect the socket to the server address specified in manager_addr
        self.manager_socket.connect(self.manager_addr)
