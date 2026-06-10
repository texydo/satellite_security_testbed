import ast
import asyncio
import contextlib
import queue
from functools import partial
import json 

import msgpack
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed


async def handle_webapp_communication(
    websocket, wsCommToSimThreadQ, simThreadToWsCommQ
):
    """
    Handles bidirectional communication between the web application and the thread that responsible for the simulation excution.

    This coroutine sets up two asynchronous tasks:
    1. Receiving messages from the web application and placing them into `wsCommToSimThreadQ` if needed.
    2. Sending messages back to the web application via the websocket.

    Args:
        websocket: The WebSocket connection object used for communication with the frontend.
        wsCommToSimThreadQ (asyncio.Queue): Queue for forwarding messages received from the websocket thread
                                            to the simulation thread.
        simThreadToWsCommQ (asyncio.Queue): Queue for sending messages from the simulation thread
                                            back to the websocket thread.

    Behavior:
        - Uses asyncio tasks to handle sending and receiving concurrently.
        - Both directions of communication run until one task completes (or fails).

    Notes:
        - This function should be called in an environment where an event loop is running.
        - Make sure that both handler functions (`websocket_recv_handler`, `websocket_send_handler`)
          are properly implemented for graceful task termination and exception handling.
    """
    print(wsCommToSimThreadQ, simThreadToWsCommQ)
    recv_task = asyncio.create_task(
        websocket_recv_handler(websocket, wsCommToSimThreadQ, simThreadToWsCommQ)
    )
    send_task = asyncio.create_task(
        websocket_send_handler(websocket, wsCommToSimThreadQ, simThreadToWsCommQ)
    )

    done, pending = await asyncio.wait(
        {recv_task, send_task}, return_when=asyncio.FIRST_COMPLETED
    )

    for task in pending:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    for task in done:
        with contextlib.suppress(ConnectionClosed):
            task.result()


async def websocket_recv_handler(websocket, wsCommToSimThreadQ, simThreadToWsCommQ):
    """
    Asynchronously receives messages from the web application via WebSocket and processes them.

    For each incoming message:
    - Unpacks the MsgPack-encoded binary.
    - Passes the decoded message to `handleIncomingMessage` for further handling.

    Args:
        websocket: The WebSocket connection to the frontend.
        wsCommToSimThreadQ (asyncio.Queue): Queue used to pass control messages to the simulation thread.
        simThreadToWsCommQ (asyncio.Queue): ueue for sending messages from the simulation thread
                                            back to the websocket thread.

    Notes:
        - Assumes incoming messages are MsgPack-encoded and represent dictionaries with a "stage" field.
        - This coroutine should run indefinitely while the WebSocket is open.
    """
    try:
        async for message in websocket:
            incoming_message =  ast.literal_eval(message) if isinstance(message, str) else  msgpack.unpackb(message, raw=False)
            wsCommToSimThreadQ.put(incoming_message)
            # handleIncomingMessage(incoming_message, wsCommToSimThreadQ, simThreadToWsCommQ)
    except ConnectionClosed:
        pass


def handleIncomingMessage(message, wsCommToSimThreadQ, simThreadToWsCommQ):
    """
    Routes an incoming message to the appropriate handler based on its 'stage' field.

    Args:
        message (dict): The decoded message received from the WebSocket. Must contain a "stage" key.
        wsCommToSimThreadQ (asyncio.Queue): Queue to communicate actions or data to the simulation thread.
        simThreadToWsCommQ (asyncio.Queue): Queue used to send or modify graph-related data.

    Supported Stages:
        - "start": Begins simulation via `handleStartSim`.
        - "stop": Stops simulation via `handleStopSim`.
        - "changeGraphs": Prepares graphs via `handlePrepMessage`.
        - "getGraph": Responds to graph request via `handleGetGraphRequest`.

    Notes:
        - This function assumes all handlers are defined and correctly handle their respective logic.
    """
    stage = message["stage"]

    if stage == "start":
        wsCommToSimThreadQ.put(message)
    if stage == "pause":
        wsCommToSimThreadQ.put(message)
    elif stage == "resume":
        wsCommToSimThreadQ.put(message)
    elif stage == "setAttackFactor":
        wsCommToSimThreadQ.put(message)


async def websocket_send_handler(websocket, wsCommToSimThreadQ, simThreadToWsCommQ):
    while True:
        try:
            msg = simThreadToWsCommQ.get_nowait()
            await websocket.send(json.dumps(msg))
            # await websocket.send(msgpack.packb(msg))
        except ConnectionClosed:
            break
        except queue.Empty:
            await asyncio.sleep(0.01)


async def wsServerInit(wsCommToSimThreadQ, simThreadToWsCommQ):
    """
    Initializes and starts an asynchronous WebSocket server to handle communication between
    a web application and the websocket thread.

    This function uses the `websockets` library to create a WebSocket server that listens for
    incoming connections. It delegates the handling of messages to the `handle_webapp_communication`
    function using the provided communication queues.

    Args:
        wsCommToSimThreadQ (queue.Queue or asyncio.Queue): The queue used to send messages from the WebSocket thread
                                                           to the simulation excution thread.
        simThreadToWsCommQ (queue.Queue or asyncio.Queue): The queue used to send messages from the simulation thread
                                                           back to the WebSocket thread.

    Notes:
        - The function uses `partial` to create a version of `handle_webapp_communication` with preset parameters.
        - The WebSocket server listens on `localhost` at port `8765`.
        - The server will continue running indefinitely, processing WebSocket communication in the background.
        - `wsCommToSimThreadQ` and `simThreadToWsCommQ` are passed to `handle_webapp_communication` for further processing.

    Raises:
        websockets.exceptions.WebSocketException: If there are issues with the WebSocket connection or server.
        asyncio.CancelledError: If the server is canceled while running.
    """
    handle_webapp_communication_with_params = partial(
        handle_webapp_communication,
        wsCommToSimThreadQ=wsCommToSimThreadQ,
        simThreadToWsCommQ=simThreadToWsCommQ,
    )

    async with serve(
        handle_webapp_communication_with_params, "localhost", 8765
    ) as server:
        await server.serve_forever()


def startWsServer(wsCommToSimThreadQ: queue, simThreadToWsCommQ: queue):
    asyncio.run(wsServerInit(wsCommToSimThreadQ, simThreadToWsCommQ))
