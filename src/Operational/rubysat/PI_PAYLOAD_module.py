class PI_PAYLOAD:
    def __init__(self, comm_channel, send_func):
        """
        Initialize the PI_PAYLOAD class with a default communication channel.
        """
        self.comm_channel = self.get_pi_com_channel()
        
        self.send_func = send_func

    def PI_PAYLOAD_CAMERA(self, camera_activity_duration):
        """
        Constructs a command to control the PI_PAYLOAD camera.

        Args:
            camera_activity_duration (int): Duration for which the camera should be active.

        Returns:
            str: A command string to control the camera.
        """
        command = (f"{self.comm_channel} PI_PAYLOAD_CAMERA with CCSDS_VERSION 0, CCSDS_TYPE CMD, "
                   f"CCSDS_SECONDARY_HEADER_FLAG TRUE, CCSDS_APID 7, CCSDS_SEQUENCE_FLAG NOGROUP, "
                   f"CCSDS_SEQUENCE_COUNT 0, CCSDS_PACKET_DATA_LENGTH 13, CCSDS_TIMESTAMP_PREAMBLE 0, "
                   f"CCSDS_YEAR 0, CCSDS_MONTH 0, CCSDS_DAY_OF_MONTH 0, CCSDS_HOURS 0, CCSDS_MINUTES 0, "
                   f"CCSDS_SECONDS 0, CCSDS_VERSION_NUMBER_MAJOR 3, CCSDS_VERSION_NUMBER_MINOR 0, "
                   f"CCSDS_VERSION_NUMBER_PATCH 0, CCSDS_PACKET_ID 12, PARAMETER_PI_PAYLOAD_CAMERA_SET_TIME {camera_activity_duration}")
        
        self.send_func(command) 

    @staticmethod
    def get_pi_com_channel():
        """
        Provides the communication channel specific for this module.

        Returns:
            str: The communication channel identifier.
        """
        return "ESAT10_WIFI"

    def PI_PAYLOAD_command_handler(self, command):
        """
        Handles PI_PAYLOAD commands by delegating to specific methods based on the command type.

        Args:
            command (str): The command string to be handled.

        Returns:
            str: The generated command string for execution.
        """
        parts = command.split()
        command_type, parameters = parts

        if command_type == "PI_PAYLOAD_CAMERA":
            self.PI_PAYLOAD_CAMERA(int(parameters))
        else:
            return "Unknown command"
