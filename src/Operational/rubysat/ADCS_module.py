class ADCS:
    
    def __init__(self, comm_channel, send_func):
        """
        Initializes the ADCS class with a communication channel.

        Args:
            comm_channel (str): The communication channel identifier.
        """
        # Set the comm channel 
        self.comm_channel = comm_channel
        
        # Set the function in which commands will be sent.
        self.send_func  = send_func 
        
    @staticmethod
    def isLimitedByDuration(comm_channel, command_and_parameters):
        """
        Constructs a command to reset parts of the ADCS subsystem.

        This method takes a command and parameters string, identifies the command type, and returns a new command string that disables the ADCS subsystem. 
        The command is constructed assuming a specific protocol format.

        Args:
            comm_channel (str): The communication channel identifier.
            command_and_parameters (str): The original command and parameters string.

        Returns:
            str: A command string to disable the ADCS subsystem.
        """
        command = command_and_parameters.split()[0]
        
        if command == "ADCS_WHEEL_SET_SPEED":
            return " ".join(["ADCS", "OFF", command, "0"])  # Set wheel speed to zero.
        if command == "ADCS_MAGNETORQUER_ENABLE":
            return " ".join(["ADCS", "OFF", command, "OFF"])  # Turn off
        if command == "ADCS_WHEEL_SET_DUTY_CYCLE":
            return " ".join(["ADCS", "OFF", command, "0"])  # Set duty cycle speed to zero.

    
    def ADCS_WHEEL_SET_SPEED(self, wheel_speed):
        """
        Constructs a command to set the wheel speed of the ADCS subsystem.

        This method generates a command string to set the wheel speed of the ADCS subsystem to a specified value. 
        The command follows a specific protocol format.

        Args:
            comm_channel (str): The communication channel identifier.
            wheel_speed (int): The desired wheel speed.

        Returns:
            str: A command string to set the wheel speed. 
        """
        command = (f"{self.comm_channel} ADCS_WHEEL_SET_SPEED with CCSDS_VERSION 0, CCSDS_TYPE CMD, "
                   f"CCSDS_SECONDARY_HEADER_FLAG TRUE, CCSDS_APID ADCS, CCSDS_SEQUENCE_FLAG NOGROUP, "
                   f"CCSDS_SEQUENCE_COUNT 0, CCSDS_PACKET_DATA_LENGTH 13, CCSDS_TIMESTAMP_PREAMBLE 0, "
                   f"CCSDS_YEAR 0, CCSDS_MONTH 0, CCSDS_DAY_OF_MONTH 0, CCSDS_HOURS 0, CCSDS_MINUTES 0, "
                   f"CCSDS_SECONDS 0, CCSDS_VERSION_NUMBER_MAJOR 3, CCSDS_VERSION_NUMBER_MINOR 0, "
                   f"CCSDS_VERSION_NUMBER_PATCH 0, CCSDS_PACKET_ID 33, PARAMETER_ADCS_WHEEL_SET_SPEED {wheel_speed}")
        
        self.send_func(command)
       

    
    def ADCS_WHEEL_SET_DUTY_CYCLE(self, duty_cycle_speed):
        """
        Constructs a command string to set the duty cycle speed of an ADCS wheel on a given communication channel.
        
        Parameters:
            comm_channel (str): The communication channel identifier.
            duty_cycle_speed (float): A floating-point number representing the desired duty cycle speed of the ADCS wheel.
            
        Returns:
            str: The constructed command string.
        """
        command = (f"{self.comm_channel} ADCS_WHEEL_SET_DUTY_CYCLE with CCSDS_VERSION 0, CCSDS_TYPE CMD, "
                   f"CCSDS_SECONDARY_HEADER_FLAG TRUE, CCSDS_APID ADCS, CCSDS_SEQUENCE_FLAG NOGROUP, "
                   f"CCSDS_SEQUENCE_COUNT 0, CCSDS_PACKET_DATA_LENGTH 15, CCSDS_TIMESTAMP_PREAMBLE 0, "
                   f"CCSDS_YEAR 0, CCSDS_MONTH 0, CCSDS_DAY_OF_MONTH 0, CCSDS_HOURS 0, CCSDS_MINUTES 0, "
                   f"CCSDS_SECONDS 0, CCSDS_VERSION_NUMBER_MAJOR 3, CCSDS_VERSION_NUMBER_MINOR 0, "
                   f"CCSDS_VERSION_NUMBER_PATCH 0, CCSDS_PACKET_ID 32, PARAMETER_ADCS_WHEEL_SET_DUTY_CYCLE {duty_cycle_speed}")
        
        self.send_func(command)


    def ADCS_MAGNETORQUER_ENABLE(self, state):  # state could be either ON/OFF 
        """
        Constructs a command to enable/disable the magnetorquer of the ADCS subsystem.

        This method generates a command string to enable or disable the magnetorquer of the ADCS subsystem based on the specified state. The command follows a specific protocol format.

        Args:
            comm_channel (str): The communication channel identifier.
            state (str): The state of the magnetorquer, either "ON" or "OFF".

        Returns:
            str: A command string to enable/disable the magnetorquer.
        """
        command = (f"{self.comm_channel} ADCS_MAGNETORQUER_ENABLE with CCSDS_VERSION 0, CCSDS_TYPE CMD, "
                   f"CCSDS_SECONDARY_HEADER_FLAG TRUE, CCSDS_APID ADCS, CCSDS_SEQUENCE_FLAG NOGROUP, "
                   f"CCSDS_SEQUENCE_COUNT 0, CCSDS_PACKET_DATA_LENGTH 12, CCSDS_TIMESTAMP_PREAMBLE 0, "
                   f"CCSDS_YEAR 0, CCSDS_MONTH 0, CCSDS_DAY_OF_MONTH 0, CCSDS_HOURS 0, CCSDS_MINUTES 0, "
                   f"CCSDS_SECONDS 0, CCSDS_VERSION_NUMBER_MAJOR 3, CCSDS_VERSION_NUMBER_MINOR 0, "
                   f"CCSDS_VERSION_NUMBER_PATCH 0, CCSDS_PACKET_ID 48, PARAMETER_ADCS_MAGNETORQUER_ENABLE {state}")

        self.send_func(command)
    
    
    def ADCS_command_handler(self, command):
        """
        Handles ADCS commands by delegating to specific methods based on the command type.

        This method takes a command string, identifies the command type, and delegates to the appropriate method to generate the command string for execution. Currently supports commands for setting wheel speed and enabling/disabling magnetorquers.

        Args:
            comm_channel (str): The communication channel identifier.
            command (str): The command string to be handled.

        Returns:
            str: The generated command string for execution.
        """
        
        parts = command.split()
        command_type, parameters = parts
        
        if command_type == "ADCS_WHEEL_SET_SPEED":
            self.ADCS_WHEEL_SET_SPEED(int(parameters))
        if command_type == "ADCS_WHEEL_SET_DUTY_CYCLE":
            self.ADCS_WHEEL_SET_DUTY_CYCLE(parameters)
        if command_type == "ADCS_MAGNETORQUER_ENABLE":
            self.ADCS_MAGNETORQUER_ENABLE(parameters)
