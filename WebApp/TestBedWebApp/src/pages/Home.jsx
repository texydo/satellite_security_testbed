import { useEffect } from 'react';
import useWebSocket from 'react-use-websocket';

import {
  stopData,
  pauseData,
  resumeData,
  setRequestedGraphsData,
  createStartMsg,
} from '../assets/msgForServer.jsx';

export default function HomePage() {
  const WS_URL = `ws://127.0.0.1:8765`;
  const { sendJsonMessage, lastJsonMessage } = useWebSocket(WS_URL);

  useEffect(() => {
    console.log(lastJsonMessage);
  }, [lastJsonMessage]);

  function handleStartStop() {
    sendJsonMessage(createStartMsg());
  }
  function handleStop() {
    sendJsonMessage(stopData);
  }
  function handlePause() {
    sendJsonMessage(pauseData);
  }
  function handleResume() {
    sendJsonMessage(resumeData);
  }
  function handleSetGraphs() {
    sendJsonMessage(setRequestedGraphsData);
  }

  return (
    <>
      <h1>This is the Home page!</h1>
      <div>
        <button onClick={handleStartStop}>Start</button>
      </div>
      <div>
        <button onClick={handleStop}>Stop</button>
      </div>
      <div>
        <button onClick={handlePause}>Pause</button>
      </div>
      <div>
        <button onClick={handleResume}>Resume</button>
      </div>
      <div>
        <button onClick={handleSetGraphs}>setGraphs</button>
      </div>
    </>
  );
}
