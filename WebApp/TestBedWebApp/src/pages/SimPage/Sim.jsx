import React, { useEffect } from 'react';
import CommandLogPanel from '../../components/CommandLogPanel/CommandLogPanel';
import MiddlePanel from '../../components/MiddlePanel/MiddlePanel';
import StatusPanel from '../../components/StatusPanel/StatusPanel';
import styles from './Sim.module.css';
import { useSelector, useDispatch } from 'react-redux';
import { simActions } from '../../store/sim-slice';
import AttackTrigger from '../../components/AttackTrigger/AttackTrigger';

export default function SimPage() {
  const { isGreenOn, isRedOn } = AttackTrigger();

  const dispatch = useDispatch();

  const simDurationMinutes = useSelector(
    (state) => Number(state.sim.simDuration || 0)
  );
  const simRunning = useSelector((state) => state.sim.simRunning);
  const simPaused = useSelector((state) => state.sim.simPaused);

  const graphData = useSelector((state) => state.graphs.graphs);
  const commandsData = useSelector((state) => state.graphs.commandsReceived);

  useEffect(() => {
    if (!simRunning || simPaused) {
      return undefined;
    }

    const interval = setInterval(() => {
      dispatch(
        simActions.setSimPassedSeconds((seconds) =>
          Math.min(seconds + 1, simDurationMinutes * 60)
        )
      );
    }, 1000);

    return () => clearInterval(interval);
  }, [dispatch, simRunning, simPaused, simDurationMinutes]);

  return (
    <div className={styles.simPage}>
      <div className={styles.left}>
        <CommandLogPanel
          commands={commandsData}
          isGreenOn={isGreenOn}
          isRedOn={isRedOn}
        />
      </div>
      <div className={styles.center}>
        <MiddlePanel data={graphData} />
      </div>
      <div className={styles.right}>
        <StatusPanel />
      </div>
    </div>
  );
}
