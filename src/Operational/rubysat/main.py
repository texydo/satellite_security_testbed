import sys
import time
import datetime
from command_handler import CommandHandler # Custom module for handling commands
import os
from client.rubySatClient import Client # Custom  module for communication with the Manager computer
import datetime
import queue
import socket
import random
import struct
import json
import threading
import traceback
import subprocess
import configparser
from utils import receive_msgpack
import msgpack


def is_daemon_running(process_name="daemon_server.py"):
    # Use tasklist on Windows to check if the process is running
    try:
        result = subprocess.run(
            ["tasklist"], stdout=subprocess.PIPE, text=True, shell=True
        )
        return process_name in result.stdout
    except Exception as e:
        print(f"Error checking process: {e}")
        return False


def start_daemon_server():
    if is_daemon_running():
        print("Daemon server is already running.")
        return
    try:
        # Command to activate the environment and start daemon_server.py
        subprocess.Popen(
            [
                "cmd.exe", "/k", 
                "conda activate env && cd C:\\Users\\SatUser\\Desktop\\RubySat\\rubysat && python daemon_server.py"
            ],
            shell=True
        )
        print("Daemon server started successfully.")
    except Exception as e:
        print(f"Failed to start daemon server: {e}")
        

def to_unix_time(time_fmt):
    # Converts a time tuple to Unix timestamp format
    time_fmt = tuple(time_fmt)
    year, month, day, hour, minute, float_seconds = time_fmt
    dt = datetime.datetime(year, month, day, hour, minute, int(float_seconds))
    dt = dt + datetime.timedelta(seconds=float_seconds - int(float_seconds))
    return dt.replace(tzinfo=datetime.timezone.utc).timestamp()


def get_relative_sim_time(exe_data, simulation_time_start):
    if not exe_data or "time" not in exe_data:
        return None
    return int(to_unix_time(exe_data["time"])) - simulation_time_start


class DataFromCosmos:
    def __init__(self, host, port):
        # Initialize the socket and queue for receiving data from Cosmos
        self.queue = queue.Queue()
        self.ruby_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ruby_addr = (host, port)
        self._stop_event = threading.Event()
        
    @property
    def last_message(self):
        # Retrieves the last message in the queue if available, else returns False
        return self.queue.get() if not self.queue.empty() else False

    def recv_all(self, n):
        """ Helper function to ensure all 'n' bytes are received """
        data = bytearray()
        while len(data) < n:
            packet = self.ruby_socket.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def run(self):
        # Connects to the Cosmos server and continuously receives data
        print("waiting")
        print(self.ruby_addr)
        self.ruby_socket.connect(self.ruby_addr)
        print("Connected")
        while True:
            packed_length = self.ruby_socket.recv(4) # Receive the length of the incoming JSON data
            
            if not packed_length:
                return None
            length = struct.unpack('!I', packed_length)[0] # Unpack the length
            json_data = self.ruby_socket.recv(length) # Receive the actual JSON data
            if not json_data:
                return None
            data = json.loads(json_data.decode('utf-8'))
            self.queue.put(data)
            
            # print the command which has been recieved
            #print(f"Data which entered Queue: {data.keys()}") # Check which commands or data is being inserted to the queue...
            
    def stop(self):
        self._stop_event.set()

            
class PiMetricsServer:
    def __init__(self, host, port):
        self.queue = queue.Queue()
        self.host = host
        self.port = port
        self._stop = threading.Event()

    @property
    def last_message(self):
        return self.queue.get() if not self.queue.empty() else None

    def run(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(1)
        server.settimeout(1.0)   # so we can check self._stop periodically
        print(f"[PiMetricsServer] Listening on {self.host}:{self.port}")

        conn = None
        try:
            while not self._stop.is_set():
                # --- Accept loop ---
                if conn is None:
                    try:
                        conn, addr = server.accept()
                        print(f"[PiMetricsServer] Connected by {addr}")
                        conn.settimeout(1.0)   # only for timeout checks
                    except socket.timeout:
                        continue

                # --- Receive loop ---
                try:
                    msg = receive_msgpack(conn)
                except socket.timeout:
                    # no data this interval, but still alive
                    continue
                except Exception as e:
                    print(f"[PiMetricsServer] Receive error: {e}")
                    conn.close()
                    conn = None
                    continue

                if not msg:
                    # empty read—just keep waiting
                    continue

                # real payload!
                self.queue.put(msg)

        finally:
            if conn:
                conn.close()
            server.close()
            print("[PiMetricsServer] Shut down")

    def stop(self):
        self._stop.set()
       


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('sim_config.ini')
    
    pi_host = config.get('PI_METRICS_COM', 'host')
    pi_port = config.getint('PI_METRICS_COM', 'port')
    pi_server = PiMetricsServer(pi_host, pi_port)
    pi_thread = threading.Thread(target=pi_server.run, daemon=False)
    pi_thread.start()
    
    current_time = int(time.time()) 
    commands_file_name=config.get('SIM_CONFIG', 'commands_file_name') # YAML file with commands
    simulation_duration=config.getint('SIM_CONFIG', 'simulation_duration') # Fallback duration in seconds
    simulation_text_file=config.get('SIM_CONFIG', 'simulation_text_file') # Output file for simulation script
    com_channel=config.get('SIM_CONFIG', 'com_channel') # Communication channel with the satellite
    
    # Parameters of the process that read data from cosmos
    cosmos_com_IP=config.get('COSMOS_COM', 'cosmos_com_IP')
    cosmos_com_PORT=config.getint('COSMOS_COM', 'cosmos_com_PORT')
    
    manager_client_PORT=config.getint('MANAGER_COM', 'manager_client_PORT')
    
    # Parameters of the process that send command to the satellie 
    cosmos_command_sender_IP=config.get('COSMOS_COM', 'cosmos_command_sender_IP')
    cosmos_com_sender_PORT=config.getint('COSMOS_COM', 'cosmos_com_sender_PORT')
    
    # Remove existing simulation file if it exists
    if os.path.exists(simulation_text_file):
        os.remove(simulation_text_file)

    # Initialize command handler with command file and communication channel
    handler = CommandHandler(commands_file_name, 
                             com_channel,
                             host=cosmos_command_sender_IP,
                             port=cosmos_com_sender_PORT)  

    # Exit if command file is invalid
    if not handler.valid_command_file:
        sys.exit(1)

    # Initialize client and connect to the Manager computer
    client = Client(sys.argv[1], manager_client_PORT, "operational")
    client.run()
    
    # Prepare the client and get initial data for the simulation
    (
        _,
        time_data,
        night_prob,
        prep_simulation_duration,
        load_command_file,
        command_file_content,
    ) = client.prep()
    if prep_simulation_duration is not None:
        simulation_duration = int(prep_simulation_duration)
    simulation_time_start = int(to_unix_time(time_data)) # Convert time data to Unix format
    
    if load_command_file and command_file_content:
        with open(simulation_text_file, "w", encoding="utf-8") as file:
            file.write(command_file_content)
        handler.loadSim(simulation_text_file)
    else:
        simulation_data = handler.simulate(simulation_duration)
        handler.write_simulation_file(simulation_text_file) # Write the simulation data and write it to a file

    generated_command_file_content = handler.readTxtFileContent(simulation_text_file)
    handler.start_server() # Start connection with the Ruby script
    
    # Start a thread to receive data from Cosmos server 
    CosmosRecv = DataFromCosmos(cosmos_com_IP, cosmos_com_PORT)
    CosmosRecv_thread = threading.Thread(target=CosmosRecv.run, daemon=False)
    CosmosRecv_thread.start()

    last_command = None # Variable to store the last command executed
    night_time = False  # Tracks if the current time is considered "night" for command execution rules
    current_time = 0
    manager_connected = True
    
    # handler.loadSim('simToLoad.txt')
    
    try:
        # Loop through each command in the simulation dictionary and execute based on time
        for command_epoch_time, command in handler.simulation_dic.items():
            script_line = str(command_epoch_time) + " " + command
            handler.last_execution_line = script_line # Update the last executed line
            new_exe_msg = {}
            
            # Include the last executed command if available
            if last_command:
                new_exe_msg.update({"command": last_command})
            if generated_command_file_content:
                new_exe_msg.update({"command_file_content": generated_command_file_content})
                generated_command_file_content = None
                
            # Get the last message from Cosmos if available    
            last_cosmos_message = CosmosRecv.last_message
            if (last_cosmos_message):
                new_exe_msg.update({"cosmos_data": last_cosmos_message})
                
            last_pi = pi_server.last_message
            if last_pi:
                    opts = last_pi.get("data", {}).get("options", {})
                    opts.pop("timestamp", None)
                    new_exe_msg["pi_metrics"] = opts
                
            # Execute the command and get execution data from the client    
            exe_data = client.execute(new_exe_msg)
            if not exe_data:
                manager_connected = False
                break
                          
            night_time = night_time if exe_data.get("night_probability") is None else exe_data.get("night_probability")
            last_command = None

            # Calculate the current simulation time
            current_time = get_relative_sim_time(exe_data, simulation_time_start)
            if current_time is None:
                manager_connected = False
                break
            command_time, command = script_line.split(maxsplit=1)
            command_time = int(command_time)
            
            # Wait until it's time to execute the next command
            while command_time >= current_time:
                last_cosmos_message = CosmosRecv.last_message
                last_pi = pi_server.last_message
                data = {}
                
                if last_cosmos_message:
                    data.update({"cosmos_data": last_cosmos_message})
                if last_pi:
                    opts = last_pi.get("data", {}).get("options", {})
                    opts.pop("timestamp", None)
                    data.update({"pi_metrics": opts})
                
                exe_data = client.execute(data)
                if not exe_data:
                    manager_connected = False
                    break
                    
                # Update night_time if needed and recalculate current time    
                night_time = night_time if exe_data.get("night_probability") is None else exe_data.get("night_probability")
                current_time = get_relative_sim_time(exe_data, simulation_time_start)
                if current_time is None:
                    manager_connected = False
                    break
            
                # print("Current time: ", current_time)
                # print("command time: ", command_time)
                # Execute or skip command based on conditions
                if current_time >= command_time:
                    last_command = command
                    print("new command: ",last_command)
                    if night_time:
                        # Randomly decide to execute or skip the command during night
                        if (random.randint(1, 100) < night_prob):
                            print(f"The command at time {current_time} is being executed...\n")
                            handler.run_command(command_time)
                            break
                        else:
                            print(f"The command at time {current_time} skipped\n")
                        break
                    else:
                        print(f"The command at time {current_time} is being executed...\n")
                        handler.run_command(command_time)
                        break

            if not manager_connected:
                break
                    
        #Send the last command and cosmos data and the last command to the manager
        new_exe_msg = {}
        
        if last_command:
            new_exe_msg.update({"command": last_command})
            print(f"Added the last command to the new msg: {last_command}")
                
        # Get the last message from Cosmos if available    
        last_cosmos_message = CosmosRecv.last_message
        if (last_cosmos_message):
            new_exe_msg.update({"cosmos_data": last_cosmos_message})
        
        last_pi = pi_server.last_message
        if last_pi:
            opts = last_pi.get("data", {}).get("options", {})
            opts.pop("timestamp", None)
            new_exe_msg["pi_metrics"] = opts
                        
        # Execute the command and get execution data from the client    
        exe_data = client.execute(new_exe_msg) if manager_connected else {}
        
        # Wait until the simulation duration is reached, then fall through to cleanup.
        while manager_connected and current_time <= simulation_duration:
            data = {}

            last_cosmos_message = CosmosRecv.last_message
            if last_cosmos_message:
                data.update({"cosmos_data": last_cosmos_message})

            last_pi = pi_server.last_message
            if last_pi:
                opts = last_pi.get("data", {}).get("options", {})
                opts.pop("timestamp", None)
                data.update({"pi_metrics": opts})

            exe_data = client.execute(data)
            if not exe_data or "time" not in exe_data:
                break

            current_time = get_relative_sim_time(exe_data, simulation_time_start)
            if current_time is None:
                break
            time.sleep(0.1)
           
    except TypeError as e:
        # Handle errors and print traceback for debugging
        print("An error occurred:", e)
        traceback.print_exc()  # This will print the full traceback
    finally:
        # Clean up by stopping all modules, server, and Cosmos receiving thread
        handler.stop_all_modules()
        handler.stop_server()
        CosmosRecv.stop()  
        CosmosRecv_thread.join()
        pi_server.stop()
        pi_thread.join()

        
