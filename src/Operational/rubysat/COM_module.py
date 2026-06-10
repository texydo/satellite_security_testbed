class COM:
    def __init__(self, comm_channel, send_func):
        """
        Initialize the COM class with a communication channel.
        
        Args:
            comm_channel (str): The communication channel identifier.
        """
        self.comm_channel = comm_channel
        
        self.send_func  = send_func

    def isLimitedByDuration(self, command_and_parameters):
        """
        Checks if a command is limited by duration and if so returns a line to reset the action.

        This method takes a command and parameters string, identifies the command type, and returns a boolean indicating whether the command is limited by duration.

        Args:
            command_and_parameters (str): The original command and parameters string.

        Returns:
            str: A string command to reset the action or `False` if the command is not limited by duration.
        """
        command = ""

        if ' ' in command_and_parameters:
            command = command_and_parameters.split()[0]
        else:
            command = command_and_parameters

        if command == "COM_ENABLE_RECEIVER":
            return " ".join(["COM", "OFF", "COM_DISABLE_RECEIVER"])  # disable receiver
        if command == "COM_ENABLE_TRANSMITTER":
            return " ".join(["COM", "OFF", "COM_DISABLE_TRANSMITTER"])  # disable transmitter

        return False

    def COM_command_handler(self, command):
        """
        Handles COM commands by delegating to specific methods based on the command type.

        This method takes a command string, identifies the command type, and delegates to the appropriate method to generate the command string for execution. 
        
        Args:
            command (str): The command string to be handled.

        Returns:
            str: The generated command string for execution.
        """
        command_type = ""
        parameters = ""

        if ' ' in command:
            command_type, parameters = command.split()
        else:
            command_type = command

        if command_type == "COM_ENABLE_RECEIVER":
            self.COM_ENABLE_RECEIVER()
        if command_type == "COM_DISABLE_RECEIVER":
            self.COM_DISABLE_RECEIVER()
        if command_type == "COM_ENABLE_TRANSMITTER":
            self.COM_ENABLE_TRANSMITTER()
        if command_type == "COM_DISABLE_TRANSMITTER":
            self.COM_DISABLE_TRANSMITTER()

        return "Unknown command"

    def COM_ENABLE_RECEIVER(self):
        """
        Constructs a command string to enable a receiver on a given communication channel.
        
        Returns:
            str: The constructed command string.
        """
        command = (f"{self.comm_channel} COM_ENABLE_RECEIVER with CCSDS_VERSION 0, CCSDS_TYPE CMD, "
                   f"CCSDS_SECONDARY_HEADER_FLAG TRUE, CCSDS_APID COM, CCSDS_SEQUENCE_FLAG NOGROUP, "
                   f"CCSDS_SEQUENCE_COUNT 0, CCSDS_PACKET_DATA_LENGTH 11, CCSDS_TIMESTAMP_PREAMBLE 0, "
                   f"CCSDS_YEAR 0, CCSDS_MONTH 0, CCSDS_DAY_OF_MONTH 0, CCSDS_HOURS 0, CCSDS_MINUTES 0, "
                   f"CCSDS_SECONDS 0, CCSDS_VERSION_NUMBER_MAJOR 1, CCSDS_VERSION_NUMBER_MINOR 0, "
                   f"CCSDS_VERSION_NUMBER_PATCH 0, CCSDS_PACKET_ID 4")
        self.send_func(command)

    def COM_DISABLE_RECEIVER(self):
        """
        Constructs a command string to disable a receiver on a given communication channel.
        
        Returns:
            str: The constructed command string.
        """
        command = (f"{self.comm_channel} COM_DISABLE_RECEIVER with CCSDS_VERSION 0, CCSDS_TYPE CMD, "
                   f"CCSDS_SECONDARY_HEADER_FLAG TRUE, CCSDS_APID COM, CCSDS_SEQUENCE_FLAG NOGROUP, "
                   f"CCSDS_SEQUENCE_COUNT 0, CCSDS_PACKET_DATA_LENGTH 11, CCSDS_TIMESTAMP_PREAMBLE 0, "
                   f"CCSDS_YEAR 0, CCSDS_MONTH 0, CCSDS_DAY_OF_MONTH 0, CCSDS_HOURS 0, CCSDS_MINUTES 0, "
                   f"CCSDS_SECONDS 0, CCSDS_VERSION_NUMBER_MAJOR 1, CCSDS_VERSION_NUMBER_MINOR 0, "
                   f"CCSDS_VERSION_NUMBER_PATCH 0, CCSDS_PACKET_ID 5")
        self.send_func(command)

    def COM_ENABLE_TRANSMITTER(self):
        """
        Constructs a command string to enable a transmitter on a given communication channel.
        
        Returns:
            str: The constructed command string.
        """
        command = (f"{self.comm_channel} COM_ENABLE_TRANSMITTER with CCSDS_VERSION 0, CCSDS_TYPE CMD, "
                   f"CCSDS_SECONDARY_HEADER_FLAG TRUE, CCSDS_APID COM, CCSDS_SEQUENCE_FLAG NOGROUP, "
                   f"CCSDS_SEQUENCE_COUNT 0, CCSDS_PACKET_DATA_LENGTH 11, CCSDS_TIMESTAMP_PREAMBLE 0, "
                   f"CCSDS_YEAR 0, CCSDS_MONTH 0, CCSDS_DAY_OF_MONTH 0, CCSDS_HOURS 0, CCSDS_MINUTES 0, "
                   f"CCSDS_SECONDS 0, CCSDS_VERSION_NUMBER_MAJOR 1, CCSDS_VERSION_NUMBER_MINOR 0, "
                   f"CCSDS_VERSION_NUMBER_PATCH 0, CCSDS_PACKET_ID 2")
        self.send_func(command)

    def COM_DISABLE_TRANSMITTER(self):
        """
        Constructs a command string to disable a transmitter on a given communication channel.
        
        Returns:
            str: The constructed command string.
        """
        command = (f"{self.comm_channel} COM_DISABLE_TRANSMITTER with CCSDS_VERSION 0, CCSDS_TYPE CMD, "
                   f"CCSDS_SECONDARY_HEADER_FLAG TRUE, CCSDS_APID COM, CCSDS_SEQUENCE_FLAG NOGROUP, "
                   f"CCSDS_SEQUENCE_COUNT 0, CCSDS_PACKET_DATA_LENGTH 11, CCSDS_TIMESTAMP_PREAMBLE 0, "
                   f"CCSDS_YEAR 0, CCSDS_MONTH 0, CCSDS_DAY_OF_MONTH 0, CCSDS_HOURS 0, CCSDS_MINUTES 0, "
                   f"CCSDS_SECONDS 0, CCSDS_VERSION_NUMBER_MAJOR 1, CCSDS_VERSION_NUMBER_MINOR 0, "
                   f"CCSDS_VERSION_NUMBER_PATCH 0, CCSDS_PACKET_ID 3")
        self.send_func(command)
