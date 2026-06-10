import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { satActions } from '../../store/sat-slice.jsx';
import { graphActions } from '../../store/graph-slice.jsx';
import store from '../../store/index.jsx';
import WorldMap from '../WorldMap/WorldMap.jsx';
import SimulationProgressBar from '../SimulationProgressBar/SimulationProgressBar.jsx';
import styles from './StatusPanel.module.css';
import { useNavigate } from 'react-router-dom';

import {
  stopData,
  pauseData,
  resumeData,
  setRequestedGraphsData,
  createStartMsg,
} from '../../assets/msgForServer.jsx';
import { simActions } from '../../store/sim-slice.jsx';

export default function StatusPanel() {
  const WS_URL = `ws://127.0.0.1:8765`;
  const simStarting = useSelector((state) => state.sim.simStarting);
  const simRunning = useSelector((state) => state.sim.simRunning);
  const simPaused = useSelector((state) => state.sim.simPaused);
  const simDurationMinutes = useSelector((state) =>
    Number(state.sim.simDuration || 0)
  );
  const simPassedSeconds = useSelector((state) => state.sim.simPassedSeconds);
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { sendJsonMessage, lastJsonMessage, readyState } = useWebSocket(WS_URL);

  useEffect(() => {
    if (lastJsonMessage !== null) {
      handleServerMessage(lastJsonMessage, dispatch, navigate);
    }
  }, [lastJsonMessage, dispatch, navigate]);

  useEffect(() => {
    if (simRunning && readyState === ReadyState.OPEN) {
      sendJsonMessage(setRequestedGraphsData);
    }
  }, [simRunning, readyState, sendJsonMessage]);

  function handleStartStop() {
    if (simStarting) {
      return;
    }

    if (simRunning) {
      sendJsonMessage(stopData);
      dispatch(graphActions.resetState());
      dispatch(simActions.stopSimulation());
    } else {
      let startMsg = createStartMsg();
      console.log(startMsg);
      sendJsonMessage(startMsg);
      sendJsonMessage(setRequestedGraphsData);
      dispatch(simActions.startSimulationPending());
    }
  }

  function handlePauseResume() {
    if (simPaused) {
      sendJsonMessage(resumeData);
    } else {
      sendJsonMessage(pauseData);
    }
    dispatch(simActions.toggleSimPaused());
  }

  function handleGoBack() {
    if (simRunning) {
      handleStartStop();
    } else if (simStarting) {
      sendJsonMessage(stopData);
      dispatch(simActions.stopSimulation());
    }
    navigate('/SimConfig');
  }

  return (
    <div className={styles.panel}>
      <h2 className={styles.title}>Satellite Status</h2>

      <div className={styles.mapSection}>
        <WorldMap />
      </div>

      <div className={styles.controlDock}>
        <SimulationProgressBar
          currentSeconds={simPassedSeconds}
          totalSeconds={simDurationMinutes * 60}
          isStarting={simStarting}
          isRunning={simRunning}
          isPaused={simPaused}
        />

        <div className={styles.controlsRow}>
          <button
            className={`${styles.controlButton} ${
              simRunning ? styles.stopButton : styles.startButton
            }`}
            onClick={handleStartStop}
            disabled={readyState !== ReadyState.OPEN || simStarting}
          >
            <span className={styles.buttonText}>
              {simStarting ? 'Starting' : simRunning ? 'Stop' : 'Start'}
            </span>
          </button>

          <button
            className={`${styles.controlButton} ${
              simPaused ? styles.resumeButton : styles.pauseButton
            }`}
            onClick={handlePauseResume}
            disabled={!simRunning || readyState !== ReadyState.OPEN}
          >
            <span className={styles.buttonText}>
              {simPaused ? 'Resume' : 'Pause'}
            </span>
          </button>

          <button
            className={`${styles.controlButton} ${styles.backButton}`}
            onClick={handleGoBack}
          >
            <span className={styles.buttonText}>Back</span>
          </button>
        </div>
      </div>
    </div>
  );
}

function handleServerMessage(msg, dispatch, navigate) {
  if (msg === null) {
    return;
  }

  if (msg.stage === 'simulationComplete') {
    const message =
      msg.data?.message || 'Simulation completed successfully.';
    dispatch(simActions.completeSimulation(message));
    dispatch(graphActions.resetState());
    navigate('/SimConfig');
  } else if (msg.stage === 'simulationStarted') {
    dispatch(simActions.startSimulation());
  } else if ('Time' in msg) {
    store.dispatch(satActions.updateSatState(msg));
  } else if ('command' in msg) {
    store.dispatch(graphActions.handleNewCommand(msg));
  } else if ('EPS_BATTERY_TOTAL_VOLTAGE' in msg) {
    store.dispatch(graphActions.handleGraphUpdate(msg));
  }
}
