import React from 'react';
import styles from './CommandLogPanel.module.css';

const formatTime = (timestamp) => {
  const date = new Date(timestamp * 1000); // Convert seconds to ms
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

const CommandLogPanel = ({
  commands = [],
  isGreenOn = false,
  isRedOn = false,
}) => {
   // Sort using the new `id` field to preserve insertion order
  const sortedCommands = [...commands].sort((a, b) => {
    if (a.id !== undefined && b.id !== undefined) {
      return b.id - a.id;
    }
    return (a.timeCommandSent || 0) - (b.timeCommandSent || 0); // fallback
  }); // Reverse so newest on top

  return (
    <div className={styles.panel}>
      <h2 className={styles.title}>Command Log</h2>

      <div className={styles.commandList}>
        {sortedCommands.length === 0 ? (
          <p className={styles.empty}>No commands sent yet.</p>
        ) : (
          sortedCommands.map((cmd, idx) => (
            <div
              key={idx}
              className={`${styles.command} ${cmd.isRed ? styles.redText : ''} ${
                cmd.isGreen ? styles.redText : ''
              }`}
            >
              <div className={styles.commandName}>{cmd.command}</div>
              <div className={styles.commandTime}>
                {formatTime(cmd.timeCommandSent)}
              </div>
            </div>
          ))
        )}
      </div>

      <div className={styles.bulbContainer}>
        <div className={styles.bulbWithLabel}>
          <div
            className={`${styles.bulb} ${isGreenOn ? styles.onGreen : ''}`}
          ></div>
          <span className={styles.label}>
            {isGreenOn ? 'Attack Executed' : ''}
          </span>
        </div>
        <div className={styles.bulbWithLabel}>
          <div
            className={`${styles.bulb} ${isRedOn ? styles.onRed : ''}`}
          ></div>
          <span className={styles.label}>
            {isRedOn ? 'Attack Detected' : ''}
          </span>
        </div>
      </div>
    </div>
  );
};

export default CommandLogPanel;
