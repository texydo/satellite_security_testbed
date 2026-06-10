import queue
import socket
import time

from utils.ManagerClass import ManagerServerData
from utils.utils import get_value_from_config_ini, receive_msgpack, send_msgpack

def bootup_computers():
    """
    Initiates the boot-up process for the three components computers(Operational, enviroment and orbital)
    by sending a 'main' command along with
    the manager computer's IP address to each daemon server.

    This function performs the following steps:
    1. Retrieves the list of daemon server parameters (IP, port, computer name, etc.).
    2. Retrieves the manager computer's IP address from the configuration file.
    3. Iterates over each daemon server and attempts to connect via a TCP socket, activation of the daemon server runs the component script.
    4. If the connection is successful, sends a MsgPack-encoded message to the server.
    5. If the connection fails due to a network error, prints an error message with the server name.

    Exceptions handled:
        - ConnectionResetError
        - ConnectionAbortedError
        - TimeoutError
    """
    daemonServersParameters = getDaemonServersParameters()
    manager_ip = get_value_from_config_ini("GENERAL", "manager_comp_ip")

    for daemonServerParameters in daemonServersParameters:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as daemonSocket:
                daemonSocket.settimeout(1)
                print("Start attempt connecting to: ", daemonServerParameters)
                daemonSocket.connect(
                    (daemonServerParameters["ip"], daemonServerParameters["port"])
                )
                send_msgpack(daemonSocket, ["main", manager_ip])
        except (ConnectionResetError, ConnectionAbortedError, TimeoutError) as e:
            print("couldn't connect to ", daemonServerParameters["computerName"])


def getDaemonServersParameters() -> list[dict[str, any]]:
    """
    Retrieves the configuration parameters for all daemon servers involved in the system.

    Returns:
        list[dict[str, any]]: A list of dictionaries, each containing:
            - "computerName" (str): A label identifying the computer (e.g., 'orbital', 'operational', 'cyber').
            - "ip" (str): The IP address of the corresponding daemon server, read from the configuration file.
            - "port" (int): The port number used to communicate with the daemon server, also read from the config.

    Notes:
        - This function uses `get_value_from_config_ini` to fetch IP and port values from a config file.
        - The expected section in the config file is 'GENERAL', with specific keys for each computer's IP and port.
    """
    return [
        {
            "computerName": "orbital",
            "ip": get_value_from_config_ini("GENERAL", "dataConv_comp_IP"),
            "port": get_value_from_config_ini(
                "GENERAL", "daemon_server_PORT_ENV", varType="int"
            ),
        },
        {
            "computerName": "operational",
            "ip": get_value_from_config_ini("GENERAL", "operational_comp_IP"),
            "port": get_value_from_config_ini(
                "GENERAL", "daemon_server_PORT_OP", varType="int"
            ),
        },
        {
            "computerName": "cyber",
            "ip": get_value_from_config_ini("GENERAL", "cyber_comp_IP"),
            "port": get_value_from_config_ini(
                "GENERAL", "daemon_server_PORT_CYBER", varType="int"
            ),
        },
    ]


def getCompPrepMsg(compName: str, managerObj: ManagerServerData):
    """
    Constructs and returns a preparation message for a specific computer based on its role.

    Args:
        compName (str): The name of the target computer. Expected values are:
                        - "orbital"
                        - "operational"
                        - "cyber"
        managerObj (ManagerServerData): An object containing all necessary data (TLE, time, probabilities, etc.)
                                        used to populate the message payload.

    Returns:
        dict: A dictionary representing the message to send, with the following structure:
              {
                  "stage": "prep",
                  "type": "SEND",
                  "data": {...}  # Varies depending on the computer
              }

              - For "orbital": includes 'tle', 'time', 'min', 'max'
              - For "operational": includes 'time', 'tle', 'night_probability'
              - For "cyber": includes 'time', 'tle', 'attacks'
    """
    time = managerObj.get_datetime_list_from_epoch()
    if compName == "orbital":
        return {
            "stage": "prep",
            "type": "SEND",
            "data": {
                "tle": managerObj.tle,
                "time": time,
                "min": managerObj.min,  # Minimun solar intensity in the upcoming simulation
                "max": managerObj.max,  # Maximun solar intensity in the upcoming simulation
                "demo": managerObj.demoMode,
            },
        }
    if compName == "operational":
        return {
            "stage": "prep",
            "type": "SEND",
            "data": {
                "time": time,
                "tle": managerObj.tle,
                "command" : False,
                "attacks time logs": False,
                "night_probability": managerObj.night_probability,
                "simulation_duration": int(float(managerObj.simDuration) * 60),
                "load_command_file": managerObj.loadCommandFile,
                "command_file_content": managerObj.getSavedCommandFileContent(),
            },
        }
    if compName == "cyber":
        return {
            "stage": "prep",
            "type": "SEND",
            "data": {
                "time": time,
                "tle": managerObj.tle,
                "attacks": managerObj.attacks,
            },
        }


def prepConnectedComp(conn: socket, managerObj: ManagerServerData):
    """
    Handles the preparation phase for a connected component by responding to a 'prep' request.

    Listens on the provided socket connection for a MsgPack-encoded message from the client.
    If the message indicates that the component is in the 'prep' stage, the function constructs
    and sends back a preparation message using the provided manager object.

    Args:
        conn (socket): The socket object representing the connection to the component.
        managerObj (ManagerServerData): An object containing data needed to construct the preparation message
                                        (e.g., TLE, time, attacks, etc).

    Returns:
        str: The name of the component (e.g., "orbital", "operational", "cyber") once preparation is complete.

    Behavior:
        - Waits for a valid dictionary message with "stage": "prep".
        - Extracts the component name from the message.
        - Sends a corresponding preparation message built using `getCompPrepMsg()`.
        - Returns the component name to indicate which component was prepared.
    """
    while True:
        response = receive_msgpack(conn)
        if response and isinstance(response, dict) and response.get("stage") == "prep":
            compName = response["comp"]
            prepMsg = getCompPrepMsg(compName, managerObj)

            send_msgpack(conn, prepMsg)
            return compName


def getManagerIP_and_PORT() -> tuple[str, int]:
    """
    Retrieves the IP address and port number of the manager computer from the configuration file.

    Returns:
        tuple[str, int]: A tuple containing:
            - host (str): The manager computer's IP address.
            - port (int): The port number used for manager communication.

    Notes:
        - Values are read from the "GENERAL" section of the config file using `get_value_from_config_ini`.
        - The 'manager_PORT' value is explicitly cast to an integer.
    """
    host = get_value_from_config_ini("GENERAL", "manager_comp_ip")
    port = get_value_from_config_ini("GENERAL", "manager_PORT", "int")

    return host, port


def connectToComponents(managerObj: ManagerServerData) -> list:
    """
    Boots up all component computers, listens for their connections, and prepares them for operation.

    This function performs the following:
    1. Sends boot-up messages to all daemon servers.
    2. Starts a server socket using the manager's IP and port (from the config).
    3. Accepts incoming connections from component computers.
    4. For each connection, performs a preparation handshake using `prepConnectedComp`.
    5. Stores and returns information about each connected and prepared computer.

    Args:
        managerObj (ManagerServerData): An object containing all the relevant data to be sent to components
                                        during their preparation phase (e.g., TLE, time, min, max, etc.).

    Returns:
        list[dict]: A list of dictionaries, each representing a connected computer with:
            - "compName" (str): The name of the component (e.g., "orbital", "operational", "cyber").
            - "socket" (socket): The socket object representing the connection.
            - "addr" (tuple): The (IP, port) address of the connected client.

    Notes:
        - Expects exactly 3 computers to connect and complete preparation.
        - Assumes `bootup_computers` will successfully initiate each component.
        - This function blocks until all components are connected and ready.
    """
    computers = []
    numberOfComputers = 3

    bootup_computers()

    host, port = getManagerIP_and_PORT()

    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen()

    while len(computers) < numberOfComputers:
        conn, addr = server_socket.accept()
        compName = prepConnectedComp(conn, managerObj)
        computers.append({"compName": compName, "socket": conn, "addr": addr})

    return computers


def handle_simulation_execution(wsCommToSimThreadQ: queue, simThreadToWsCommQ: queue):
    simulationRunning = False

    while True:
        simulationRunning, managerObj, computers = waitForStartCommand(
            wsCommToSimThreadQ
        )
        managerObj.reset_simulation_clock()
        simThreadToWsCommQ.put(
            {
                "stage": "simulationStarted",
                "type": "event",
                "data": {"message": "All components are ready. Simulation started."},
            }
        )

        while simulationRunning and managerObj.simCompleted is False:

            time.sleep(0.5)
            
            updatesFromWsThread = checkMsgFromWs(wsCommToSimThreadQ, managerObj)
            simulationRunning = updatesFromWsThread.get("action") != "stopSimulation"
            if simulationRunning is False:
                break

            componentsUpdates = checkUpdatesFromComponents(computers)
            if componentsUpdates is None:
                print("A component disconnected. Ending the simulation...")
                managerObj.close_all_computers_sockets()
                simThreadToWsCommQ.put(
                    {
                        "stage": "simulationComplete",
                        "type": "event",
                        "data": {"message": "Simulation ended because a component disconnected."},
                    }
                )
                simulationRunning = False
                break
            managerObj.updateSimState(componentsUpdates, simThreadToWsCommQ)
            sendUpdatesToComponents(computers, managerObj)

        if managerObj.simCompleted is True:
            print("Ending the simulation...")
            simThreadToWsCommQ.put(
                {
                    "stage": "simulationComplete",
                    "type": "event",
                    "data": {"message": "Simulation completed."},
                }
            )
            managerObj.close_all_computers_sockets()
            simulationRunning = False
            continue
                    


def waitForStartCommand(wsCommToSimThreadQ: queue):
    """
    Waits for a 'start' command message from the simulation WebSocket thread queue.

    This function blocks until a message is received from the `wsCommToSimThreadQ` queue.
    It expects the message to be a dictionary with a key `"stage"` set to `"start"`.
    If the condition is met, it initializes the simulation manager object and connects to components.

    Args:
        wsCommToSimThreadQ (queue): A queue used to receive messages from the WebSocket communication thread.

    Returns:
        tuple:
            - simulationRunning (bool): True if the start command was received and processed.
            - managerObj (ManagerServerData or None): The initialized manager object, or None if the message was invalid.
            - computers (dict or None): The connected components, or None if the message was invalid.
    """
    while True:
        msg = wsCommToSimThreadQ.get()
        if isinstance(msg, dict) and msg.get("stage") == "start":
            break
        print(f"Ignoring message while waiting for simulation start: {msg}")

    simulationRunning = True
    managerObj = ManagerServerData(startMsg=msg)
    computers = connectToComponents(managerObj)

    managerObj.computers = computers
    return simulationRunning, managerObj, computers


def checkMsgFromWs(wsCommToSimThreadQ: queue, managerObj: ManagerServerData):
    """
    Checks for a message from the WebSocket communication thread queue and handles simulation control commands.

    This function retrieves a message from the queue if available and checks its "stage" field.
    Based on the value of "stage", it performs actions such as stopping or pausing the simulation.

    Args:
        wsCommToSimThreadQ (queue): A queue used to receive control messages from the WebSocket communication thread.

    Returns:
        dict: A dictionary containing actions to be performed based on the message.
              Returns {"action": "stopSimulation"} if the simulation should stop.
              Returns an empty dict if no relevant action is needed or the queue is empty.
    """
    if wsCommToSimThreadQ.empty():
        return {}

    msg = wsCommToSimThreadQ.get()

    stage = msg["stage"]
    if stage == "stop":
        # PLACEHOLDER: Let the components know the sim is done / close the sockets
        print("Stopping the simulation...")
        managerObj.close_all_computers_sockets()
        return {"action": "stopSimulation"}
    if stage == "pause":
        handlePause(wsCommToSimThreadQ)
        print("resume the sim...")
        return {}
    if stage == "setRequestedGraphs":
        requestedGraphs = msg["data"]["requestedGraphs"]
        managerObj.requestedGraphs = list(requestedGraphs)
        return {}
    if stage == "setAttackFactor":
        new_factor = msg["data"]["attackFactor"]
        # print("Attack factor updated to:", new_factor)
        managerObj.attack_factor = new_factor
        return {}


def handlePause(wsCommToSimThreadQ: queue):
    """
    Handles the pause state of the simulation.

    This function blocks the simulation loop when a "pause" command is received.
    It continuously waits for a "resume" command to be received from the queue to continue execution.

    Args:
        wsCommToSimThreadQ (queue): A queue used to receive control messages from the WebSocket communication thread.
    """
    # PLACEHOLDER: Let the components know the sim is being paused and again when it being resumed
    print("pause the sim!")
    while True:
        if (msg := wsCommToSimThreadQ.get())["stage"] == "resume":
            break


def checkUpdatesFromComponents(computers: list):
    """_summary_
    Go over each computer and check for a message...
    get the message and do stuff with it if needed
    done

    Args:
        computers (list): _description_
        managerObj (ManagerServerData): _description_
    """
    updates = []

    # print("start reading messages from computers..")

    for computer in computers:
        compName = computer["compName"]
        compSocket = computer["socket"]

        response = receive_msgpack(compSocket)
        if not response:
            return None

        updateLoad = response.get("data", {}).get("options")
        if updateLoad is None:
            print(f"Skipping malformed update from {compName}: {response}")
            continue

        updates.append({"compName": compName, "update": updateLoad})
    # print("finished reading messages from computers..")

    return updates


def sendUpdatesToComponents(computers: list, managerObj: ManagerServerData, updates={}):
    """
    Sends execution stage updates to all connected component computers.

    This function prepares a message containing the current simulation time and minute,
    and sends it to each component using its associated socket.

    Args:
        computers (list): A list of dictionaries, each containing information about a component,
                          including its name ("compName") and socket connection ("socket").
        managerObj (ManagerServerData): An object that manages simulation state and provides timing info.
        updates (dict, optional): Reserved for future use to include additional update data.
    """
    # print("Sending updates to all components computers..")

    currentSecond = int(time.time()) - managerObj.SYSTEM_INIT_START_TIME_EPOCH
    currentMinute = int(currentSecond / 60)

    for computer in computers:
        compName = computer["compName"]
        compSocket = computer["socket"]
        
        # If this computer is the operational unit, send the simulation time without applying the playback speed effect.
        currentSimTime = managerObj.get_datetime_list_from_epoch(
            noPlayBackSpeedFlag=(compName == "operational")
        )
        response = {
            "stage": "execution",
            "type": "SEND",
            "comp": compName,
            "data": {
                "time": currentSimTime,
                "current_minute": currentMinute,
                "current_second": currentSecond,
            },
        }

        send_msgpack(compSocket, response)
    # print("Finished sending updates to all components computers..")
