class TPL:
    def __init__(self, comm_channel, send_func):
        """
        Initialize the TPL class with a communication channel.
        
        Args:
            comm_channel (str): The communication channel identifier.
        """
        self.comm_channel = comm_channel

        self.send_func  = send_func

    def TPL_command_handler(self, command):
        """
        Handles TPL commands by delegating to specific methods based on the command type.

        This method takes a command string, identifies the command type, and delegates to the appropriate method to generate the command string for execution. Currently supports commands for setting target temperatures.

        Args:
            command (str): The command string to be handled.

        Returns:
            str: The generated command string for execution.
        """
        parts = command.split()
        command_type, parameters = parts
        
        if command_type == "TPL_SET_TARGET_TEMPERATURE":
            self.TPL_SET_TARGET_TEMPERATURE(parameters)
        if command_type == "TPL_SET_RUN_MODE":
            self.TPL_SET_RUN_MODE(int(parameters))
        return "Unknown command"

    def isLimitedByDuration(self, command_and_parameters):
        """
        Checks if a command is limited by duration.

        This method takes a command and parameters string, identifies the command type, and returns a boolean indicating whether the command is limited by duration. Currently, it only handles the case for setting target temperature and returns `False` for this command.

        Args:
            command_and_parameters (str): The original command and parameters string.

        Returns:
            bool: `False` if the command is not limited by duration.
        """
        command = command_and_parameters.split()[0]
        
        if command == "TPL_SET_TARGET_TEMPERATURE":
            return False
        if command == "TPL_SET_RUN_MODE":
            return " ".join(["TPL", "OFF", command, "0"])  # Set state to STANDBY
        return False

    def TPL_SET_TARGET_TEMPERATURE(self, temperature):
        """
        Constructs a command to set the target temperature of the TPL subsystem.

        This method generates a command string to set the target temperature of the TPL subsystem to a specified value. The command follows a specific protocol format.

        Args:
            temperature (float): The desired target temperature.

        Returns:
            str: A command string to set the target temperature.
        """
        command = (f"{self.comm_channel} TPL_SET_TARGET_TEMPERATURE with CCSDS_VERSION 0, CCSDS_TYPE CMD, "
                   f"CCSDS_SECONDARY_HEADER_FLAG TRUE, CCSDS_APID TPL, CCSDS_SEQUENCE_FLAG NOGROUP, "
                   f"CCSDS_SEQUENCE_COUNT 0, CCSDS_PACKET_DATA_LENGTH 15, CCSDS_TIMESTAMP_PREAMBLE 0, "
                   f"CCSDS_YEAR 0, CCSDS_MONTH 0, CCSDS_DAY_OF_MONTH 0, CCSDS_HOURS 0, CCSDS_MINUTES 0, "
                   f"CCSDS_SECONDS 0, CCSDS_VERSION_NUMBER_MAJOR 1, CCSDS_VERSION_NUMBER_MINOR 0, "
                   f"CCSDS_VERSION_NUMBER_PATCH 0, CCSDS_PACKET_ID 1, PARAMETER_TPL_SET_TARGET_TEMPERATURE {temperature}")
        
        self.send_func(command)

    def TPL_SET_RUN_MODE(self, state_digit):
        """
        Constructs a command string to set the run mode of a heater on a given communication channel based on the provided state digit.
        
        Parameters:
            state_digit (int): An integer representing the desired state of the device. Possible values are 0 for STANDBY and 1 for NOMINAL.
            
        Returns:
            str: The constructed command string.
        """
        if state_digit == 0:
            state = "STANDBY"
        elif state_digit == 1:
            state = "NOMINAL"
        else:
            return "Invalid state digit"  # Handle invalid input

        command = (f"{self.comm_channel} TPL_SET_RUN_MODE with CCSDS_VERSION 0, CCSDS_TYPE CMD, "
                   f"CCSDS_SECONDARY_HEADER_FLAG TRUE, CCSDS_APID TPL, CCSDS_SEQUENCE_FLAG NOGROUP, "
                   f"CCSDS_SEQUENCE_COUNT 0, CCSDS_PACKET_DATA_LENGTH 12, CCSDS_TIMESTAMP_PREAMBLE 0, "
                   f"CCSDS_YEAR 0, CCSDS_MONTH 0, CCSDS_DAY_OF_MONTH 0, CCSDS_HOURS 0, CCSDS_MINUTES 0, "
                   f"CCSDS_SECONDS 0, CCSDS_VERSION_NUMBER_MAJOR 1, CCSDS_VERSION_NUMBER_MINOR 0, "
                   f"CCSDS_VERSION_NUMBER_PATCH 0, CCSDS_PACKET_ID 0, PARAMETER_TPL_SET_RUN_MODE {state}")
        self.send_func(command)
