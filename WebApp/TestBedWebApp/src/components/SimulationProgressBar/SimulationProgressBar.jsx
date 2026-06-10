import React from 'react';
import styles from './SimulationProgressBar.module.css';

function formatDuration(totalSeconds) {
  const safeSeconds = Math.max(0, Math.floor(Number(totalSeconds) || 0));
  const hours = Math.floor(safeSeconds / 3600);
  const minutes = Math.floor((safeSeconds % 3600) / 60);
  const seconds = safeSeconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m ${seconds}s`;
  }

  if (minutes > 0) {
    return `${minutes}m ${seconds}s`;
  }

  return `${seconds}s`;
}

export default function SimulationProgressBar({
  currentSeconds,
  totalSeconds,
  isStarting,
  isRunning,
  isPaused,
}) {
  const numericTotal = Math.max(0, Number(totalSeconds) || 0);
  const numericCurrent = Math.max(0, Number(currentSeconds) || 0);
  const clampedCurrent =
    numericTotal > 0 ? Math.min(numericCurrent, numericTotal) : 0;
  const remainingSeconds =
    numericTotal > 0 ? Math.max(numericTotal - clampedCurrent, 0) : 0;
  const progress = numericTotal > 0 ? clampedCurrent / numericTotal : 0;
  const percentage = Math.round(progress * 100);

  let statusText = 'Ready';
  if (isStarting) {
    statusText = 'Starting';
  } else if (isRunning && isPaused) {
    statusText = 'Paused';
  } else if (isRunning) {
    statusText = 'Running';
  } else if (percentage >= 100) {
    statusText = 'Complete';
  }

  return (
    <div className={styles.progressContainer}>
      <div className={styles.progressHeader}>
        <span>Simulation Timer</span>
        <strong>{statusText}</strong>
      </div>

      <div className={styles.progressBody}>
        <div className={styles.progressBarBackground}>
          <div
            className={styles.progressBarFill}
            style={{
              width: `${percentage}%`,
            }}
          />
        </div>
        <div className={styles.progressText}>{percentage}%</div>
      </div>

      <div className={styles.timeLine}>
        <span>E {formatDuration(clampedCurrent)}</span>
        <span>R {formatDuration(remainingSeconds)}</span>
        <span>T {formatDuration(numericTotal)}</span>
      </div>
    </div>
  );
}
