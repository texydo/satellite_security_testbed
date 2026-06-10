

def isLimitedByDuration(comm_channel, command_and_parameters):
        command = ""
        
        if ' ' in command_and_parameters: command = command_and_parameters.split()[0]
        else: command = command_and_parameters
        
        if command == "OBC_STORE_TELEMETRY"   : return " ".join(["OBC", "OFF",  "OBC_STORE_TELEMETRY"]   )# disable receiver
        
        return False

def OBC_STORE_TELEMETRY (comm_channel, state): #state could be either ON/ OFF
    command = f"{comm_channel} OBC_STORE_TELEMETRY with CCSDS_VERSION 0, CCSDS_TYPE CMD, CCSDS_SECONDARY_HEADER_FLAG TRUE, CCSDS_APID OBC, CCSDS_SEQUENCE_FLAG NOGROUP, CCSDS_SEQUENCE_COUNT 0, CCSDS_PACKET_DATA_LENGTH 12, CCSDS_TIMESTAMP_PREAMBLE 0, CCSDS_YEAR 0, CCSDS_MONTH 0, CCSDS_DAY_OF_MONTH 0, CCSDS_HOURS 0, CCSDS_MINUTES 0, CCSDS_SECONDS 0, CCSDS_VERSION_NUMBER_MAJOR 4, CCSDS_VERSION_NUMBER_MINOR 0, CCSDS_VERSION_NUMBER_PATCH 0, CCSDS_PACKET_ID 1, PARAMETER_OBC_STORE_TELEMETRY {state}"
    return command