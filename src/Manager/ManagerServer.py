import asyncio
import queue
import threading
import time

from simHandlers.simExecutionHandler import handle_simulation_execution

from simHandlers.webAppComHandler import startWsServer

if __name__ == "__main__":
    wsCommToSimThread = queue.Queue()
    simThreadToWsComm = queue.Queue()

    ws_thread = threading.Thread(
        target=startWsServer, args=(wsCommToSimThread, simThreadToWsComm)
    )
    sim_handle_thread = threading.Thread(
        target=handle_simulation_execution, args=(wsCommToSimThread, simThreadToWsComm)
    )

    ws_thread.start()
    sim_handle_thread.start()

    while True:
        time.sleep(1)
