import configparser
import struct
from pathlib import Path

import msgpack


def receive_msgpack(comp_socket) -> dict:
    """
    Receives a MsgPack-encoded message from a socket and unpacks it into a Python dictionary.

    This function reads the length of the incoming MsgPack message, then receives the data in chunks
    and unpacks it from the MsgPack format into a Python dictionary.

    Args:
        comp_socket (socket.socket): The socket object from which the message will be received.

    Returns:
        dict: The decoded message as a Python dictionary. Returns an empty dictionary if no message is received or an error occurs.

    Notes:
        - The function expects the message to be prefixed with its length (as a 4-byte integer).
        - The function handles receiving data in chunks to deal with large messages.
        - If the message cannot be received or unpacked, the function returns an empty dictionary.
        - The `raw=False` option in `msgpack.unpackb` ensures that byte data is converted to UTF-8 strings, if applicable.

    Raises:
        socket.error: If there is an issue while receiving data over the socket.
        msgpack.exceptions.UnpackException: If the received data cannot be unpacked from MsgPack format.
    """
    length_bytes = comp_socket.recv(4)
    if not length_bytes:
        return {}
    length = struct.unpack("I", length_bytes)[0]

    packed_data = b""
    while len(packed_data) < length:
        chunk = comp_socket.recv(length - len(packed_data))
        if not chunk:
            break
        packed_data += chunk

    if packed_data:
        msg = msgpack.unpackb(packed_data, raw=False)
        return msg
    return {}


def send_msgpack(comp_socket, msg):
    """
    Sends a MsgPack-encoded message over a socket.

    This function packs the provided message using MsgPack encoding, prepends the length of the
    packed data, and sends the resulting byte sequence over the specified socket.

    Args:
        comp_socket (socket.socket): The socket object through which the message will be sent.
        msg (any): The message to be sent. This can be any serializable Python object that can
                   be packed using the MsgPack format.

    Notes:
        - The message is packed using the MsgPack format, which is efficient for serialization.
        - The length of the packed data is prepended to the message to facilitate receiving the data
          in a way that the receiver knows the full size of the message.
        - The `use_bin_type=True` option in `msgpack.packb` ensures that binary data is handled correctly.

    Raises:
        socket.error: If there is an issue with sending the data over the socket.
        msgpack.exceptions.PackException: If the message cannot be packed correctly.
    """

    packed_data = msgpack.packb(msg, use_bin_type=True)
    length = struct.pack("I", len(packed_data))
    comp_socket.sendall(length + packed_data)


def get_value_from_config_ini(
    sectionIdentifier: str, varIdentifier: str, varType: str = "string"
) -> any:
    """
    Retrieves a configuration value from the 'manager_config.ini' file.

    This function reads the configuration file and fetches the value of a specified variable
    in a given section, converting it to the specified type.

    Args:
        sectionIdentifier (str): The section name in the INI file where the variable is located.
        varIdentifier (str): The variable name within the section to fetch.
        varType (str): The type to convert the variable to. Defaults to "string". Options are:
            - "int": Returns the value as an integer.
            - "string": Returns the value as a string.
            - "float": Returns the value as a float.
            - "boolean": Returns the value as a boolean.

    Returns:
        any: The value of the variable, converted to the specified type.

    Raises:
        ValueError: If the type is not one of the supported values ("int", "string", "float", "boolean").
        configparser.NoSectionError: If the section doesn't exist in the config file.
        configparser.NoOptionError: If the variable doesn't exist within the section.

    Notes:
        - The function expects the configuration file to be located at "<script_directory>/config/manager_config.ini".
        - The conversion is done using the methods provided by the `configparser` module.
    """
    configFilePath = Path(__file__).parent.parent / "config" / "manager_config.ini"
    config = configparser.ConfigParser()
    config.read(configFilePath)

    if varType == "int":
        return config.getint(sectionIdentifier, varIdentifier)
    if varType == "string":
        return config.get(sectionIdentifier, varIdentifier)
    if varType == "float":
        return config.getfloat(sectionIdentifier, varIdentifier)
    if varType == "boolean":
        return config.getboolean(sectionIdentifier, varIdentifier)
