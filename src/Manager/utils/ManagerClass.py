import queue
import time
from pathlib import Path

from pymongo import MongoClient
from utils.ProcessDataClass import ProcessData
from utils.utils import get_value_from_config_ini
import random 

class ManagerServerData:
    def __init__(self, startMsg):
        # "data" is a dictionary sent from the WebApp.
        # Each key-value pair in the dictionary is used to set an instance variable,
        # where the key becomes the variable name and the value is assigned to it.
        data = startMsg["data"]
        for varName, varValue in data.items():
            setattr(self, varName, varValue)
        self.saveToMongo = self.resolve_mongo_write_flag(data.get("saveToMongo"))
        self.saveCommandFile = self.resolve_bool_flag(data.get("saveCommandFile"))
        self.loadCommandFile = self.resolve_bool_flag(data.get("loadCommandFile"))
        self.commandFileName = data.get("commandFileName")
        self.commandFileContent = data.get("commandFileContent")
        self.savedCommandFilesDir = Path(__file__).parent.parent / "saved_command_files"
        self.savedCommandFilePath = self.getCommandFilePath(self.commandFileName)

        # Load the satellite information using the TLE
        self.processDataObject = ProcessData(self.tle)

        # Set the initial Satellite state
        self.satState = self.processDataObject.get_satellite_snapshot(
            self.startEpochTime
        )

        # Set the demo state
        self.demoMode = (
            self.demoMode == 1
        )  # Because you cant send boolean variables i sent either 1 for True or 0 for False

        # Mongo Settings
        self.collection = None
        self.runId = None
        if self.saveToMongo or self.demoMode:
            self.handle_mongoDB_configuration()

        self.simCurrentEpochTime = self.startEpochTime
        self.SYSTEM_INIT_START_TIME_EPOCH = int(time.time())
        self.simCurrentMinute = 0

        self.handle_graphs_configuration()

        self.commandsSentFromGS = []
        self.connectedCompsStatus = None
        self.currentAttack = None
        self.simCompleted = False
        self.min, self.max = self.calculateSolarIntensityLimits()

        self.attack_factor = 1.0  # default: no attack

    def reset_simulation_clock(self):
        """Start the simulation clock after all components completed prep."""
        self.SYSTEM_INIT_START_TIME_EPOCH = int(time.time())
        self.simCurrentEpochTime = self.startEpochTime
        self.simTimeNoPlayBack = self.startEpochTime
        self.simCurrentMinute = 0

    def updateSimState(self, componentsUpdates: list, simThreadToWsCommQ: queue):
        """
        Update the simulation's current time and satellite state based on component updates.

        This function calculates the elapsed simulation time since the system initialization,
        updates the current epoch time for the simulation, retrieves the current satellite state,
        and processes updates from various components (e.g., operational, orbital, cyber).

        Args:
            componentsUpdates (list): A list of dictionaries, where each dictionary contains:
                - 'compName' (str): The name of the component (e.g., "operational", "orbital", "cyber").
                - 'update' (dict or any): The update data associated with the component.
        """
        timeSinceSimStarted = int(time.time()) - self.SYSTEM_INIT_START_TIME_EPOCH

        self.simCurrentEpochTime = self.startEpochTime + (
            timeSinceSimStarted * self.playbackSpeed
        )
        self.simTimeNoPlayBack = self.startEpochTime + timeSinceSimStarted 
        self.satState = self.processDataObject.get_satellite_snapshot(
            self.simCurrentEpochTime
        )
        simThreadToWsCommQ.put(self.satState)  # Send satllite snapshot to the WebApp

        calcSimCurrentMinute = int(timeSinceSimStarted / 60) 
        if calcSimCurrentMinute > self.simCurrentMinute:
            self.simCurrentMinute = calcSimCurrentMinute
            print(f"Simulation Minute: {self.simCurrentMinute}")
        self.simCompleted = self.simCurrentMinute >= int(self.simDuration)

        # Process each computer update
        for comp in componentsUpdates:
            compName = comp.get("compName")
            update = comp.get("update")

            if compName == "operational":
                cyberUpdate = self.getCyberUpdateFromUpdates(componentsUpdates)
                self.handleOperationalUpdate(update, simThreadToWsCommQ)
                self.updateMongoDB(
                    cyberUpdate=cyberUpdate,
                    cosmosData=update.get("cosmos_data"), command=update.get("command"), pi_metrics=update.get("pi_metrics")
                )
            elif compName == "orbital" and update:
                # print("ENV", update)
                pass
            elif compName == "cyber" and update['attacks']:
                print("Cyber", update)
                pass

    def handleOperationalUpdate(self, update: dict, simThreadToWsCommQ: queue):
        """
        Process the operational update received from the component.

        This method extracts command and cosmos data from the update. If a command is present,
        it is appended to the list of commands sent from the ground station along with the
        current simulation time. If cosmos data is included, it is passed to the appropriate
        handler function for further processing.

        Args:
            update (dict): A dictionary containing operational update information. It may contain:
                - 'command' (str or any): The command sent from the ground station.
                - 'cosmos_data' (dict or any): The cosmos data to be processed.
        """
        cosmosData = update.get("cosmos_data")
        commandExist = update.get("command")
        commandFileContent = update.get("command_file_content")

        if commandFileContent:
            self.saveLatestCommandFile(commandFileContent)

        if commandExist:
            command = {
                "command": commandExist,
                "timeCommandSent": self.simCurrentEpochTime,
            }
            self.commandsSentFromGS.append(command)
            simThreadToWsCommQ.put(command)
        
        if cosmosData and self.demoMode is False:
            self.handleCosmosDataUpdate(cosmosData)
            userRequestedGraphs = {
                graphTitle: graphData
                for graphTitle, graphData in self.graphs.items()
                if graphTitle in self.requestedGraphs
            }
            simThreadToWsCommQ.put(userRequestedGraphs)

        if self.demoMode is True:
            self.handleDemoGraphUpdate(simThreadToWsCommQ)

        if self.demoMode is True:
            self.handleDemoGraphUpdate(simThreadToWsCommQ)

    def getGraphsHeaders(self) -> dict:
        return {
            "EPS_PACKET": [
                "EPS_BATTERY_TOTAL_VOLTAGE",
                "EPS_BATTERY_CURRENT",
                "EPS_SOLAR_PANEL_1_TEMPERATURE",
                "EPS_SOLAR_PANEL_2_TEMPERATURE",
                "EPS_SOLAR_PANEL_1_OUTPUT_CURRENT",
                "EPS_SOLAR_PANEL_2_OUTPUT_CURRENT",
                "EPS_SOLAR_PANEL_1_VOLTAGE",
                "EPS_SOLAR_PANEL_2_VOLTAGE",
            ],
            "OBC_PROCESSOR_PACKET": [
                "OBC_PROCESSOR_TEMPERATURE",
                "OBC_PROCESSOR_VOLTAGE",
            ],
            "TPL_PACKET": ["TPL_CURRENT_TEMPERATURE"],
            "PI_PAYLOAD_STATUS_PACKET": ["RECEIVED_COUNT"],
        }

    def init_graphs(self):
        """
        Initialize the graphs with empty data.

        This method retrieves the headers for the available graphs and initializes
        each graph with empty x and y value lists. The graphs are stored in a
        dictionary where the graph title serves as the key, and each entry contains
        an empty list for 'x_values' and 'y_values'.

        The graph headers are fetched by calling the `getGraphsHeaders` method, which
        returns a dictionary where the keys are packet titles and the values are lists
        of graph titles associated with each packet.

        """
        graph_headers = self.getGraphsHeaders()

        for packetTitle, titleList in graph_headers.items():
            for graphTitle in titleList:
                self.graphs[graphTitle] = {"x_values": [], "y_values": []}
                self.demoGraphs[graphTitle] = {"x_values": [], "y_values": []}
                self.demoGraphs[graphTitle] = {"x_values": [], "y_values": []}

    def handleCosmosDataUpdate(self, cosmosData: dict):
        """
        Process and update graph data based on the received cosmos data.

        This method iterates over the cosmos data, extracting the attribute titles and
        their corresponding values. If the attribute title exists in the available graphs,
        the method appends the current simulation time (x_value) and the attribute value
        (y_value) to the respective graph's x and y value lists.

        Args:
            cosmosData (dict): A dictionary where each key is a packet name, and the value
                is a list of data attributes. Each attribute is represented as a tuple
                where the first element is the attribute title (str) and the second element
                is the attribute value (any).
        """
        for packetDataList in cosmosData.values():
            for packetDataAttr in packetDataList:
                attrTitle = packetDataAttr[0]
                if attrTitle in self.graphs.keys():
                    x_value = self.simCurrentEpochTime
                    y_value = packetDataAttr[1]
                    self.graphs[attrTitle]["x_values"].append(x_value)
                    self.graphs[attrTitle]["y_values"].append(y_value)

    def get_datetime_list_from_epoch(self, noPlayBackSpeedFlag = False) -> list:
        """
        Convert the current simulation epoch time to a list of date and time components.

        This method converts the simulation's current epoch time (in seconds) to a
        structured time format using UTC. It then returns the year, month, day,
        hour, minute, and second as a list.

        Returns:
            list: A list containing the following components:
                - Year (int)
                - Month (int)
                - Day of the month (int)
                - Hour (int)
                - Minute (int)
                - Second (int)
        """
        # Format the simulation time. This could either be the actual simulation time affected by playback speed,
        # or the simulated time as if the playback speed were 1 (real-time), depending on the flag.
        timeToFormat = self.simTimeNoPlayBack if noPlayBackSpeedFlag else self.simCurrentEpochTime
        time_struct = time.gmtime(timeToFormat) 
        
        return [
            time_struct.tm_year,
            time_struct.tm_mon,
            time_struct.tm_mday,
            time_struct.tm_hour,
            time_struct.tm_min,
            time_struct.tm_sec,
        ]

    def close_all_computers_sockets(self):
        """
        Closes the socket connection for all computers in the 'computers' list.

        Iterates through each computer in the self.computers list and closes
        the associated socket to ensure proper disconnection and resource cleanup.
        """
        for computer in self.computers:
            compSocket = computer["socket"]
            compSocket.close()

    def getLastestRunId(self):
        """
        Retrieves the latest run ID from the MongoDB collection.

        Queries the collection for the document with the highest 'run_id' value,
        which is assumed to indicate the most recent run.

        Returns:
            int: The highest run ID if found, otherwise 0 if the collection is empty.
        """
        highest_run = self.collection.find_one(sort=[("run_id", -1)])

        if highest_run:
            highest_run_id = highest_run["run_id"]
            return highest_run_id
        else:
            print("Collection is empty.")
            return 0

    def updateMongoDB(self, cyberUpdate=None, cosmosData=False, command=False, pi_metrics=False):
        """
        Inserts an updated simulation state into the MongoDB collection.

        This method prepares a document containing telemetry, command, attack, and
        state information, and inserts it into the database. The insertion is skipped
        if the simulation is in demo mode.

        Args:
            cyberUpdate (dict, optional): A dictionary potentially containing an "attacks" key
                with details of cyberattacks to log. Defaults to None.
            cosmosData (dict or bool, optional): Raw data received from the COSMOS system,
                structured as a dictionary of packet names and lists. Defaults to False.
            command (any, optional): Command data to include in the database update. Defaults to False.
        """
        if self.demoMode or not self.saveToMongo:
            return
        
        if cyberUpdate and "attacks" in cyberUpdate and cyberUpdate["attacks"]:
            cyberMongoUpdate = cyberUpdate["attacks"]
        else: 
            cyberMongoUpdate = None


        updateToMongo = {
            "cosmos_data": self.formatCosmosData(cosmosData) if cosmosData else None,
            "command": command if command else None,
            "pi_metrics": pi_metrics if pi_metrics else None
        }

        updateToMongo = {k: v for k, v in updateToMongo.items() if v is not None}

        regularUpdate = {
            "run_id": self.runId,
            "TLE File Name": self.tleFileName,
            "TLE": self.tle,
            "Epoch_Time": self.simCurrentEpochTime,
            "UTC_time": self.time,
            **updateToMongo,
            "satState": self.satState,
        }

        regularUpdate.update({"attacks" : cyberMongoUpdate}) if cyberMongoUpdate else None

        self.collection.insert_one(regularUpdate)

    def formatCosmosData(self, cosmosData: dict):
        """
        Reformats COSMOS telemetry data into a dictionary structure suitable for MongoDB.

        Each packet is converted from a list of key-value tuples into a flattened dictionary
        per packet name.

        Args:
            cosmosData (dict): A dictionary where each key is a packet name and the value is
                a list of (key, value) tuples representing telemetry data.

        Returns:
            dict: Reformatted dictionary with merged key-value pairs for each packet name.
        """
        formattedData = {}

        for packetName, packetList in cosmosData.items():
            formattedData[packetName] = {}
            for packet in packetList:
                formattedData[packetName].update({packet[0]: packet[1]})

        return formattedData

    def calculateSolarIntensityLimits(self):
        """
        Calculates the minimum and maximum solar intensity values during a 90-minute simulation.

        Samples solar intensity every 100 seconds throughout the simulated period, but only
        considers values above 1000 W/m² for the minimum and maximum determination.

        Returns:
            tuple: A pair (min_intensity, max_intensity), representing the lowest and highest
            solar intensity values found above the 1000 threshold. If none found, both are None.
        """
        full_simulation_duration = 60 * 90  # total duration in seconds (90 minutes)
        sampling_interval = 100  # seconds
        current_offset = 0

        min_intensity = None
        max_intensity = None

        while current_offset < full_simulation_duration:
            current_time = self.startEpochTime + current_offset
            intensity = self.processDataObject.get_intensity(current_time)

            if intensity > 1000:
                if min_intensity is None or intensity < min_intensity:
                    min_intensity = intensity
                if max_intensity is None or intensity > max_intensity:
                    max_intensity = intensity

            current_offset += sampling_interval

        return min_intensity, max_intensity
    
    def getAllDemoRunPosts(
        self,
    ):
        """
        Retrieves all MongoDB documents corresponding to the demo run ID.

        Returns:
            pymongo.cursor.Cursor: A cursor to all documents with the current demoRunId.
        """
        query = {"run_id": self.demoRunId}
        return self.collection.find(query)

    def loadDemoGraphs(self):
        """
        Loads COSMOS telemetry data for the demo run and populates internal demoGraphs.

        For each post containing "cosmos_data", it iterates through the telemetry values
        and appends x (epoch time) and y (data value) points to the corresponding graphs.
        Increments the epoch time with each data point.
        """
        demoPosts = self.getAllDemoRunPosts()
        currentTime = self.startEpochTime
        demoGraphs = self.demoGraphs

        for post in demoPosts:
            if "cosmos_data" not in post:
                continue
            for packetList in post["cosmos_data"].values():
                for attrTitle, y_value in packetList.items():
                    graph = demoGraphs.get(attrTitle)
                    if graph is not None:
                        graph["x_values"].append(currentTime)
                        graph["y_values"].append(y_value)
                        currentTime += 1
        

    def handleDemoGraphUpdate(self, simThreadToWsCommQ):
        """
        Sends a batch of demo graph data to the front-end via a queue.

        Trims the graph data to a specific time window based on the simulation time
        since startup, and only includes graphs requested by the user.

        For EPS-related graphs, applies the attack factor only to newly arriving
        data points and modifies them persistently. The rest are shown as-is.
        """
        trimmed_dict = {}
        timeSinceSimStarted = int(time.time()) - self.SYSTEM_INIT_START_TIME_EPOCH

        if not hasattr(self, "epsAttackModified"):
            self.epsAttackModified = {
                "EPS_BATTERY_TOTAL_VOLTAGE": set(),
                "EPS_BATTERY_CURRENT": set()
            }

        for graph_name, values in self.demoGraphs.items():
            x_vals = values["x_values"]
            y_vals = values["y_values"]
            end_index = timeSinceSimStarted + self.demoGraphsBatchSize

            if graph_name in ["EPS_BATTERY_TOTAL_VOLTAGE", "EPS_BATTERY_CURRENT"]:
                for i in range(timeSinceSimStarted, min(end_index, len(y_vals))):
                    if i not in self.epsAttackModified[graph_name]:
                        original_val = y_vals[i]
                        factor = self.attack_factor  # default fallback

                        if graph_name == "EPS_BATTERY_TOTAL_VOLTAGE":
                            if 0.7 <= self.attack_factor < 0.75:
                                factor = random.uniform(0.93, 0.95)  
                            elif 0.8 <= self.attack_factor < 0.85:
                                factor = random.uniform(0.96, 0.98)
                            else:
                                factor = self.attack_factor

                            y_vals[i] = original_val * factor

                        elif graph_name == "EPS_BATTERY_CURRENT":
                            if 0.7 <= self.attack_factor < 0.75:
                                factor = random.uniform(0.45, 0.55)  
                            elif 0.8 <= self.attack_factor < 0.85:
                                factor = random.uniform(0.55, 0.65)
                            else:
                                factor = self.attack_factor

                            if original_val >= 0:
                                y_vals[i] = original_val * factor
                            elif original_val > -100 and self.attack_factor != 1:
                                y_vals[i] = original_val * (4 - factor) 
                                # print("Original y val:", original_val)
                                # print("Multiplied y val:", y_vals[i]) 
                            elif original_val <= -100 and self.attack_factor != 1:
                                y_vals[i] = original_val * (3 - factor)
                                # print("Original y val:", original_val)
                                # print("Multiplied y val:", y_vals[i])
                            else:
                                y_vals[i] = original_val
                        self.epsAttackModified[graph_name].add(i)
                        # print(f"[ATTACK] Modified EPS graph: {graph_name}, index: {i}, Attack Factor: {self.attack_factor}")

            trimmed_dict[graph_name] = {
                "x_values": x_vals[timeSinceSimStarted:end_index],
                "y_values": y_vals[timeSinceSimStarted:end_index],
            }

        userRequestedGraphs = {
            graphTitle: graphData
            for graphTitle, graphData in trimmed_dict.items()
            if graphTitle in self.requestedGraphs
        }
        simThreadToWsCommQ.put(userRequestedGraphs)


    def getCyberUpdateFromUpdates(self, componentsUpdates):
        """
        Extracts the 'cyber' component's update from a list of component updates.

        Args:
            componentsUpdates (list): A list of dictionaries, each containing
                'compName' and 'update' keys.

        Returns:
            dict or None: The update dictionary for the cyber component if present;
            otherwise, returns None.
        """
        # Process each computer update
        for comp in componentsUpdates:
            compName = comp.get("compName")
            update = comp.get("update")

            if compName == "cyber" and update:
                return update
            
        return None

    def getSavedCommandFileContent(self):
        if not self.loadCommandFile:
            return None
        if self.commandFileContent:
            return self.commandFileContent
        if not self.savedCommandFilePath.exists():
            print(f"Saved command file not found: {self.savedCommandFilePath}")
            return None
        return self.savedCommandFilePath.read_text(encoding="utf-8")

    def saveLatestCommandFile(self, commandFileContent):
        if not self.saveCommandFile:
            return
        self.savedCommandFilePath.parent.mkdir(parents=True, exist_ok=True)
        self.savedCommandFilePath.write_text(commandFileContent, encoding="utf-8")
        print(f"Saved latest command file to: {self.savedCommandFilePath}")

    def getCommandFilePath(self, commandFileName):
        fileName = self.sanitize_command_file_name(commandFileName)
        return self.savedCommandFilesDir / fileName

    @staticmethod
    def resolve_mongo_write_flag(value):
        """
        Converts the WebApp MongoDB save option into a Python boolean.

        The WebApp currently sends 1 or 0, but this accepts booleans and strings as
        well so older/manual clients can use the same field safely.
        """
        if value is None:
            try:
                return get_value_from_config_ini(
                    "MONGO_CONFIG", "isWritingToMONGO", varType="boolean"
                )
            except Exception:
                return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value == 1
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return False

    @staticmethod
    def resolve_bool_flag(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value == 1
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return False

    @staticmethod
    def sanitize_command_file_name(commandFileName):
        if not commandFileName:
            return "latest_commands.txt"

        fileName = Path(str(commandFileName).strip()).name
        safeChars = []
        for char in fileName:
            if char.isalnum() or char in {"-", "_", ".", " "}:
                safeChars.append(char)

        fileName = "".join(safeChars).strip()
        if not fileName:
            return "latest_commands.txt"
        if "." not in fileName:
            fileName = f"{fileName}.txt"
        return fileName
    
    def handle_mongoDB_configuration(self, ):
        """
        Configures the MongoDB client and initializes the collection for data insertion.

        Reads MongoDB connection details (address, port, database, collection) from a config file
        using `get_value_from_config_ini`, establishes a connection using `pymongo.MongoClient`,
        and sets up the `self.collection` attribute for further use.

        Also sets `self.runId` to one more than the current highest run ID in the collection.
        """
        mongoDB_address = get_value_from_config_ini("MONGO_CONFIG", "mongoDB_address")
        mongoDB_port= get_value_from_config_ini("MONGO_CONFIG", "mongoDB_port", varType="int")
        mongoDB_DB =  get_value_from_config_ini("MONGO_CONFIG", "db")
        mongoDB_Collection = get_value_from_config_ini("MONGO_CONFIG", "collection")

        cluster = MongoClient(mongoDB_address, mongoDB_port)
        db = cluster[mongoDB_DB]
        self.collection = db[mongoDB_Collection]
        self.runId = self.getLastestRunId() + 1
    
    def handle_graphs_configuration(self,):
        """
        Initializes graph-related configuration for both demo and regular modes.

        Sets up internal variables such as `graphs`, `demoGraphs`, and `requestedGraphs`, and initializes
        the batch size for demo graph data from configuration. If in demo mode, loads demo graph data
        from the database.

        Also initializes the list of connected `computers`.
        """
        self.graphs = {}
        self.demoGraphsBatchSize = get_value_from_config_ini("DEMO_VARIABLES", "demoGraphsBatchSize", varType="int")
        self.demoGraphs = {}
        self.init_graphs()  # Init both the demo graphs and the regular graphs
        self.demoRunId = 4
        self.loadDemoGraphs() if self.demoMode else None
        self.requestedGraphs = list(self.graphs.keys())
        self.computers = []
        
