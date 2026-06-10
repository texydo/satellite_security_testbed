import datetime
from pickle import FALSE
from command_class import Command
import yaml
import random
import time
import sys
import random


from ADCS_module import ADCS
from TPL_module import TPL
from COM_module import COM
from PI_PAYLOAD_module import PI_PAYLOAD

import subprocess
import socket
import difflib
import configparser

ruby_process = None


class CommandHandler:
    def __init__(self, file_path, com_channel, host, port):
        """
        Initializes a new instance of CommandHandler.

        Args:
            file_path (str): Path to the file containing command definitions.
            com_channel (str): a string decribing the coms channel for the satellite.

        Internal workings:
            - Initializes attributes with provided arguments.
            - Calls load_commands() to load command definitions from the specified file.
        """
        self.file_path = file_path
        self.commands = {}
        self.com_channel = com_channel
        self.last_execution_line = None
        self.simulation_dic = {}
        self.valid_command_file = self.load_commands()
        self.loadingMode = False
        self.loadedCommandsName =""

        self.host = host
        self.port = port

        
        self.modules = {"ADCS": ADCS(com_channel, self.send_commend),
                        "TPL": TPL(com_channel, self.send_commend),
                        "COM": COM(com_channel, self.send_commend),
                        "PI_PAYLOAD": PI_PAYLOAD(com_channel, self.send_commend)
                        }
        
        # Set the window in which the first commands will be scheduled in.
        self.commands_start_sec_range = (30, 90)


    def load_commands(self):
        """
        Loads command definitions from a YAML file and initializes them with random durations and frequencies.

        This method is part of the initialization process of the CommandHandler instance. It relies on the file path
        provided during the instantiation of the CommandHandler class. Each command definition in the YAML file is
        processed to select a random duration and frequency within the specified ranges, which are then used to
        instantiate a new Command object. These objects are stored in the `commands` attribute of the CommandHandler
        instance.

        Args:
            None

        Internal workings:
            - Opens and reads the YAML file specified by `self.file_path`.
            - Iterates through each command definition in the file.
            - Extracts the command name, duration range, and frequency range from each definition.
            - Selects a random duration and frequency within the specified ranges for each command.
            - Instantiates a new Command object with the selected duration and frequency and stores it in `self.commands`
              under the command name as the key.
        """
        try:
            print(self.file_path)
            with open(self.file_path, 'r') as file:
                data = yaml.safe_load(file)

            for item in data:
                if 'duration' not in item or 'frequency' not in item:
                    print("Invalid commands.yml file. Does not contain either duration or frequency")
                    return False
                command_name = item['command']
                self.commands[command_name] = Command(item)

        except Exception as e:
            print(f"Error validating commands: {e}")
            return False

        return True

    def simulate(self, total_seconds):
        """
        Generates a simulation timeline for a given duration based on the loaded commands.

        This method creates a simulation timeline represented as a list of command instances over a specified duration
        (`total_seconds`). It schedules each command according to its frequency, starting from the beginning of the
        timeline. Commands are scheduled in ascending order of their frequency to ensure fairness in distribution.

        Args:
            total_seconds (int): The total duration of the simulation in seconds.

        Returns:
            List[Command]: A list representing the simulation timeline, where each element is a Command instance
                           indicating the action to be taken at that time slot.
        """
        
        # Set the time in the simulation in which the commands start, usally zero. 
        # For example if the value is 60 the commands in the simulation will start from the 60's second and forward

        self.simulation = [None] * total_seconds
        for command in sorted(self.commands.values(), key=lambda c: c.frequency):
            command_start_time = random.randint(self.commands_start_sec_range[0], self.commands_start_sec_range[1]) 
            self.schedule_command(command, CommandHandler.get_random_index(self.simulation, command_start_time))

        return self.simulation

    def schedule_command(self, command, start_time):
        """
        Schedules a command to start at the earliest available time slot according to its frequency.

        This method schedules a given command to run at the earliest available time slot in the simulation timeline.
        It considers whether the command has a limited duration and adjusts the scheduling accordingly. If the command
        requires resetting after completion, it finds the closest subsequent time slot where the command can be reset.

        Args:
            command (Command): The command to be scheduled.
            start_time (int): The index in the simulation timeline where the command should start.

        Returns:
            None

        """
        is_limited_duration_command = self.isLimitedByDuration(command)

        current_time = start_time
        while current_time < len(self.simulation):
            if not self.simulation[current_time]:
                # Here: Set new values for the duration and frequcncy within the range.
                command.set_rnd_duration_and_frequency() 
                
                # For camera set new duration time
                if command.name.startswith("PI_PAYLOAD"):
                    camera_duration = random.randint(command.min_duration, command.max_duration)
                    command.name = command.name[:-1] + str(camera_duration)
                    
                    # Split command.name into words
                    words = command.name.split()
    
                    # Replace the last word with the camera_duration
                    words[-1] = str(camera_duration)
    
                    # Join the words back into a single string
                    command.name = " ".join(words)
                
                if is_limited_duration_command is not False:
                    reset_command_index = self.find_closest_none_type_item(current_time, command.duration)

                    if reset_command_index is not False:
                        self.simulation[current_time] = command
                        self.simulation[reset_command_index] = Command(None, is_limited_duration_command, 0, 0)
                        current_time += command.duration
                else:
                    self.simulation[current_time] = Command(None, command.name, command.duration, command.frequency)
                    # self.simulation[current_time] = command
                current_time += command.frequency
            else:
                current_time += 1

    @staticmethod
    def get_random_index(list, index):
        """
        Retrieves a random index from a given list, with special handling for None values.

        This method attempts to find an index within a specified range that does not contain a None value. It uses two rounds of attempts to increase the chances of finding such an index. The first round tries numbers between 1 and 10, and the second round tries numbers between 11 and 20. If after 20 attempts no suitable index is found, it returns the next available index.

        Args:
            list (list): The input list from which to retrieve a random index.
            index (int): The starting index from which to begin searching for a valid index.

        Returns:
            int: A random index from the list that does not contain a None value, or the next available index if no valid index is found after 20 attempts.

        Raises:
            ValueError: If the input list is empty.
        """
        attempts = 0
        max_attempts = 20

        while attempts < max_attempts:
            # First attempt: Numbers between the given index and index + 10 
            if attempts < 10:
                num = random.randint(index, index + 10)
            else:
                # Second attempt: Numbers between given index +11 and given index +21
                num = random.randint(index + 11, index + 21)

            if index < len(list) and list[index] is None:
                return num

            attempts += 1

        # If we reach here, it means we failed to find the number after 20 attempts
        return index + 1

    def write_simulation_file(self, output_file):
        """
        Writes simulation data to a file, including modifications to commands.

        This method iterates over the simulation data, applying necessary modifications to each command using the `CommandHandler.create_unified_command` method. It then writes the modified commands along with timestamps to the specified output file. Additionally, it updates the internal representation of the simulation data (`self.simulation_txt`) and a dictionary mapping timestamps to unified commands (`self.simulation_dic`).

        Args:
            output_file (str): The path to the output file where the simulation data will be written.
            simulation_start_epoch_time (int): The start time of the simulation in epoch time, used to calculate timestamps for each command.

        Note:
            Commands are expected to be objects with a `name` attribute. The `CommandHandler.create_unified_command` method is assumed to modify these commands according to some predefined rules or specifications.

        Raises:
            IOError: If there is an error opening or writing to the output file.
            AttributeError: If the simulation data contains elements that do not have a `name` attribute.
        """
        simulation_data = self.simulation

        self.simulation_txt = ""

        with open(output_file, 'w') as file:

            for i, command in enumerate(simulation_data):
                timestamp = 0
                if command:
                    unified_command = command.create_unified_command()

                    script_line = f"{timestamp + i + 1} {unified_command}\n"
                    file.write(script_line)
                    self.simulation_txt += script_line
                    self.simulation_dic[timestamp + i + 1] = unified_command

    def run_command(self, epoch_time):
        """
        Executes a command at a specified epoch time and manages any pending commands found within a given line of text.

        This method takes a combined string of time and command line and an epoch time as input. It splits the input string
        to extract the command time and the actual command. If the extracted command time matches the provided epoch time,
        it prints the command to indicate it's running. Additionally, it searches for any strings between the command time
        and the command itself, treating them as pending commands. If any pending commands are found, it executes them.

        Args:
            time_and_command_line (str): A string combining the command time and the command line, separated by whitespace.
            epoch_time (int): The epoch time at which the command should be executed.

        Returns:
            None
        """
        time_and_command_line = self.find_line_by_epoch(epoch_time)

        command_time, command = time_and_command_line.split(maxsplit=1)

        if time_and_command_line is not None:
            self.route_Command_To_Module(command)
        
        pending_commands = self.find_strings_between(time_and_command_line)

        if pending_commands is not None: self.execute_Pending_Commands(pending_commands)

        self.last_execution_line = time_and_command_line

    # Note: This function is here in order to test the run command function
    def excute_simulation(self, simulation_start_time):
        """
        Simulates the execution of commands over time based on a predefined simulation timeline.

        This method takes a simulation start time as input and simulates the execution of commands listed in a text-based
        simulation timeline. It reads the simulation timeline from a text file, where each line represents a command to be
        executed at a specific time. The simulation progresses by iterating through each line of the timeline, checking
        if the current system time matches the command's intended execution time. If a match is found, the corresponding
        command is executed. Otherwise, the simulation waits until the next command's execution time is reached.

        Args:
            simulation_start_time (int): The start time of the simulation in epoch timestamp format.

        Returns:
            None
        """

        try:
            self.start_server()
            # time.sleep(2)

            simulation_timer_start = int(time.time())

            for command_epoch_time, command in self.simulation_dic.items():

                script_line = str(command_epoch_time) + " " + command

                self.last_execution_line = script_line

                current_time = simulation_start_time + (int(time.time()) - simulation_timer_start)

                command_time, command = script_line.split(maxsplit=1)

                command_time = int(command_time)

                while command_time >= current_time:

                    current_time = simulation_start_time + (int(time.time()) - simulation_timer_start)
                    # Check if the current time matches the epoch time
                    if current_time == command_time:
                        self.run_command(current_time)
                        # print(command)
                        break
                    else:
                        time.sleep(0.5)
                        print(f"Time till next command is {command_time - current_time}")

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            self.stop_server()  # In the end of the simulation, stop the server

    def find_strings_between(self, current_line):
        """
        Extracts and formats key-value pairs from a dictionary based on a start and end condition.

        This method takes two lines of command as input, splits them to identify start and end keys, and then searches a dictionary (`self.simulation_dic`) for entries that fall between these keys. It sorts the dictionary keys to ensure a consistent order and then iterates through the range of indices between the start and end keys, extracting and formatting the key-value pairs. These formatted pairs are collected into a list and returned.

        Args:
            current_line (str): The line of text representing the end condition. It is split to extract the end key and value.

        Returns:
            list: A list of formatted strings, each representing a key-value pair from the dictionary that falls between the start and end conditions.

        Raises:
            KeyError: If either the start or end key is not found in the dictionary.
            ValueError: If the start or end key cannot be converted to an integer.
        """

        start_key, value = self.last_execution_line.split(' ', 1)
        end_key, value = current_line.split(' ', 1)
        dct = self.simulation_dic

        # Ensure both keys exist in the dictionary
        if int(start_key) not in dct or int(end_key) not in dct:
            return []

        # Sort the dictionary keys to ensure consistent ordering
        sorted_keys = sorted(dct.keys())

        # Find the indices of the start and end keys
        start_idx = sorted_keys.index(int(start_key))
        end_idx = sorted_keys.index(int(end_key))

        # Initialize an empty list to hold the results
        results = []

        # Iterate through the range of indices between start and end
        for idx in range(start_idx + 1, end_idx):  # Exclude end_key
            key = sorted_keys[idx]
            value = dct[key]
            # Format the key-value pair and append to the results list
            results.append(f"{key} {value}")

        return results

    def execute_Pending_Commands(self, commands):
        """
        Executes a list of pending commands by routing and sending each command to a module.

        This method iterates over the provided list of commands, routes each command to its intended module using the `route_Command_To_Module` method, and then sends the routed command to the module using the `send_commend` function imported from the `main` module. Each command is executed sequentially, printing a message to indicate the execution of each pending command.

        Args:
            commands (list): A list of commands to be executed. Each command is expected to be an object or data structure that can be processed by the `route_Command_To_Module` method and sent via the `send_commend` function.

        Note:
            The `send_commend` function and the `route_Command_To_Module` method are assumed to handle the details of sending commands to modules, including any necessary parsing or formatting required by the target module.

        Raises:
            NotImplementedError: If the `route_Command_To_Module` method or the `send_commend` function requires further implementation details that are not covered in this method.
        """
        for command in commands:
            print("Executing pending command")
            self.route_Command_To_Module(command)
          

    def isLimitedByDuration(self, full_command):
        """
        For the a command that is limited by duration (have a ON parameter) return the reset command from the respective module.
        
        This method takes a command name as input, splits it into words, and performs several checks to determine if the command is limited by duration. 
        Specifically, it checks if the command is of the SET type and excludes such commands from consideration. 
        Then, depending on the command's prefix (e.g., "ADCS", "TPL"), it delegates the determination of duration limitation to the corresponding 
        module-specific method (`ADCS.isLimitedByDuration` or `TPL.isLimitedByDuration`). The method assumes that the command's module-specific part 
        (excluding the prefix) is passed as an argument to these methods.

        Args:
            full_command (str): The full command name to check for duration limitation.

        Returns:
            bool: True if the command is determined to be limited by duration; otherwise, False.

        Note:
            This method relies on external modules (`ADCS`, `TPL`, etc) having implemented the `isLimitedByDuration` method, which expects the command's module-specific part as an argument. The method also assumes that the command name is structured in a way that allows splitting it into meaningful components (prefix, module-specific part).
        """
        if isinstance(full_command, str):
            words = full_command.split(' ')
        else:
            words = full_command.name.split(' ')

        if words[1] == "SET": return False  # Checks if the command is from the SET type and not ON/OFF

        command_without_module = ' '.join(words[2:])

        if words[0] == "ADCS": return ADCS.isLimitedByDuration(self.com_channel, command_without_module)
        if words[0] == "TPL": return TPL.isLimitedByDuration(self.com_channel, command_without_module)
        if words[0] == "COM": return COM.isLimitedByDuration(self.com_channel, command_without_module)

    def find_closest_none_type_item(self, current_index, num):
        """
        Finds the closest item in a list with a None value, starting from a specified index and moving forward by a specified number of steps.

        This method calculates a new index by adding a specified number to the current index. It then checks if this new index is within the bounds of the list. If it is, the method iterates through the list starting from the new index, looking for the first item that has a `None` value. If such an item is found, its index is returned. If the new index is out of bounds, the method returns `False`.

        Args:
            current_index (int): The starting index from which to begin the search for a `None` value.
            num (int): The number of steps to move forward from the current index in the search for a `None` value.

        Returns:
            int | False: The index of the closest item with a `None` value, or `False` if no such item is found or if the new index is out of bounds.

        Note:
            This method assumes that the list (`self.simulation`) contains items that can be evaluated for `None`.
        """
        # Calculate the new index based on the current index and the number
        new_index = current_index + num

        # Check if the new index is within the bounds of the list
        if new_index < len(self.simulation):
            # Iterate through the list starting from the new index
            for i in range(new_index, len(self.simulation)):
                # If a non-None value is found, return its index
                if self.simulation[i] is None:
                    return i
        else:
            # If the new index is out of bounds, return False
            return False

    def find_line_by_epoch(self, epoch_time):
        """
        Searches for a line in a text string that starts with a specified epoch time.

        This method takes an epoch time as input and searches through a text string (`self.simulation_txt`) for a line that begins with this epoch time. It converts the text string into a list of lines and iterates over each line to check if it starts with the given epoch time. If a matching line is found, it is returned immediately. If no matching line is found after iterating through all lines, the method returns `None`.

        Args:
            epoch_time (int): The epoch time to search for at the beginning of a line.

        Returns:
            str | None: The line that starts with the given epoch time, or `None` if no such line is found.

        Note:
            This method assumes that the text string (`self.simulation_txt`) is well-formed and contains lines separated by newline characters ('\n'). It also assumes that the epoch time can be meaningfully compared to the beginning of a line in the text string.
        """
        if self.loadingMode:
            content= self.readTxtFileContent(self.loadedCommandsName)
        else:
            content = self.simulation_txt
        
        # Convert the content string into a list of lines
        lines = content.split('\n')

        # Iterate over each line
        for line in lines:
            # Check if the line starts with the given epoch time
            if line.startswith(str(epoch_time)):
                # Return the matching line
                return line

        # If no matching line was found, return None
        return None

    def route_Command_To_Module(self, command):
        """
        Routes a command to its appropriate handler based on its prefix and executes the command.

        This method takes a command as input, splits it into words, and extracts the command without the module prefix. It then checks the prefix of the command to determine which handler to use for executing the command. Depending on the prefix ("ADCS" or "TPL"), it calls the corresponding handler method (`ADCS.ADCS_command_handler` or `TPL.TPL_command_handler`) with the communication channel and the command without the module as arguments. The result of the handler method call is stored in `commandToExecute` and returned.

        Args:
            command (str): The command to be executed, expected to be a string with space-separated words.

        Returns:
            str: The result of executing the command through the appropriate handler.

        Note:
            This method assumes that the command is structured in a way that allows splitting it into meaningful components (module prefix, command type, and command parameters). It also assumes that the `ADCS` and `TPL` modules have implemented the `ADCS_command_handler` and `TPL_command_handler` methods, respectively, which accept a communication channel and a command without the module as arguments.
        """
        commandToExecute = ""
        words = command.split()

        command_without_module = ' '.join(words[2:])
        
        # T: This section is good but instead of getting the command just send it to the module and it will be excuted there
        
        if words[0] == "ADCS":
            self.modules["ADCS"].ADCS_command_handler(command_without_module)
            
        elif words[0] == "TPL":
            self.modules["TPL"].TPL_command_handler(command_without_module)
            
        elif words[0] == "PI_PAYLOAD":
            self.modules["PI_PAYLOAD"].PI_PAYLOAD_command_handler(command_without_module)
            
        elif words[0] == "COM":
            self.modules["COM"].PI_PAYLOAD_command_handler(command_without_module)

       

    def start_server(self):
        """
        Starts a Ruby server process and waits for it to become operational.

        This method uses the `subprocess.Popen` function to initiate a Ruby server process by running a Ruby script (`main.rb`). It then calls a method (`wait_for_server`) to wait for the server to become operational on a specified host and port. If the server does not start within the expected timeframe, the method prints a message indicating failure, terminates the Ruby process using `ruby_process.terminate()`, and exits the program with a status code of 1. If the server starts successfully, it prints a confirmation message.

        Args:
            None

        Note:
            This method assumes that the Ruby environment is properly configured and accessible from the system where the script is run. It also assumes that the `main.rb` script is located in the same directory as the script calling this method or that its path is correctly specified. The `wait_for_server` method is expected to block until the server is ready or a timeout occurs.

        Raises:
            RuntimeError: If the server does not start in time and the process needs to be terminated.
        """
        # Start the Ruby server process
        global ruby_process1
        global ruby_process2
        import os
        prev_path = os.getcwd()
        config=configparser.ConfigParser()
        config.read('sim_config.ini')
        
        os.chdir(config.get('COSMOS_COM', 'cosmos_dir_PATH'))
      
        ruby_process1 = subprocess.Popen(['ruby', 'main.rb'], shell=False)
        ruby_process2 = subprocess.Popen(['ruby', 'datacollector.rb'], shell=False)
        
        os.chdir(prev_path)
        
        if not self.wait_for_server():
            print("Server did not start in time")
            self.stop_server()
            exit(1)
        print("server start")

    def stop_server(self):
        """
        Terminates a previously started Ruby server process.

        This method attempts to terminate the Ruby server process that was initiated by the `start_server` method. It does so by calling the `terminate()` method on the `ruby_process` object, which is assumed to be a global variable holding the subprocess.Popen instance of the Ruby server process.

        Args:
            None

        Note:
            This method assumes that the `ruby_process` variable is globally accessible and holds a valid subprocess.Popen instance representing the Ruby server process. It is important to ensure that the `ruby_process` variable is correctly initialized and assigned in the `start_server` method before attempting to terminate the process.

        Raises:
            RuntimeError: If the Ruby server process cannot be terminated due to errors or if the `ruby_process` variable is not set.
        """

        # Optionally, terminate the Ruby server process
        global ruby_process1
        global ruby_process2

        # Optionally, terminate the Ruby server process
        ruby_process2.terminate()
        ruby_process1.terminate()

    def wait_for_server(self, timeout=10):
        """
        Continuously attempts to establish a connection to a server at a specified host and port.

        This method tries to connect to a server running on a specified host and port using a socket connection. It enters a loop where it attempts to create a connection with a timeout of 1 second. If the connection attempt raises a `ConnectionRefusedError` or a `socket.timeout` exception, indicating that the server is not yet ready, the method sleeps for 100 milliseconds before retrying. The method keeps track of the elapsed time since the start of the attempt and stops retrying once the elapsed time exceeds a specified timeout. If the server becomes available within the timeout period, the method returns `True`. Otherwise, it returns `False`.

        Args:
            host (str): The hostname or IP address of the server.
            port (int): The port number on which the server is listening.
            timeout (float, optional): The maximum time in seconds to wait for the server to become available. Defaults to 10 seconds.

        Returns:
            bool: `True` if the server becomes available within the timeout period, `False` otherwise.

        Note:
            This method assumes that the server will eventually become available if it is running and reachable. It does not handle cases where the server is permanently unavailable or unreachable.
        """
        start_time = time.time()
        while True:
            try:
                with socket.create_connection((self.host, self.port), timeout=1):
                    return True
            except (ConnectionRefusedError, socket.timeout):
                if time.time() - start_time >= timeout:
                    return False
                time.sleep(0.1)

    def send_commend(self, commend):
        """
        Establishes a TCP/IP connection to a server, sends a command, receives a response, and closes the connection.

        This method creates a TCP/IP socket, connects to a server specified by `self.host` and `self.port`, appends a newline character to the command to ensure proper formatting, encodes the command to UTF-8, and sends it to the server. After sending the command, it prints the command sent. The method then waits to receive a response from the server, decodes the received bytes to a string, prints the received response, and finally closes the socket connection.

        Args:
            commend (str): The command to be sent to the server.

        Note:
            This method assumes that the server is reachable at `self.host` and `self.port` and that it is prepared to receive and respond to the command. It does not handle potential errors during the connection process, sending the command, receiving the response, or closing the connection.
        """
        host = self.host
        port = self.port
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        client_socket.connect((host, port))

        commend += '\n'
        client_socket.sendall(commend.encode('utf-8'))
        print(commend)

        # Receive a response from the server
        response = client_socket.recv(1024)
        print("Received from server:", response.decode('utf-8'))

        # Close the connection
        client_socket.close()
        
        

    def stop_all_modules(self):
        # Go over each command check if the command is limited by duration and if so create a off command and send it.
        
        for command in self.commands:
            is_limited_duration_command = self.isLimitedByDuration(command)
            
            # Check if the command is limited by duration
            if is_limited_duration_command:
                reset_command = Command(None, is_limited_duration_command, 0, 0)
                print(reset_command.name)
                self.route_Command_To_Module(reset_command.name)
                
    def loadSim(self, simCommandsFile:str):
        self.loadingMode=True
        self.loadedCommandsName=simCommandsFile 
        self.simulation_dic  = {}
        
        with open(simCommandsFile, 'r') as file:
            for line in file:
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    key, value = parts
                    self.simulation_dic [int(key)] = value
                    
        
    def readTxtFileContent(self, txtFilePath:str):
        try:
            with open(txtFilePath, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            print(f"Error: File not found at '{txtFilePath}'")
        except Exception as e:
            print(f"Error reading file: {e}")
        return None
        
 

  
        
