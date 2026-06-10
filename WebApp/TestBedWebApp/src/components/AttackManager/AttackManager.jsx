import React, { useEffect, useMemo, useState } from 'react';
import styles from './AttackManager.module.css';
import { useDispatch, useSelector } from 'react-redux';
import { simActions } from '../../store/sim-slice';

const predefinedAttacks = [
  'HeaterUp',
  'malUP',
  'CPUHigh',
  'commdown',
  'RFLeakage',
  'CPUHighTarget',
  'camUpatk',
  'magUP',
];

const DEFAULT_ATTACK_DURATION_SECONDS = 60;
const DEFAULT_SIM_DURATION_MINUTES = 90;
const SECONDS_IN_MINUTE = 60;

function getTimelineLimitSeconds(value) {
  const parsedMinutes = Number(value);
  const safeMinutes =
    Number.isFinite(parsedMinutes) && parsedMinutes > 0
      ? parsedMinutes
      : DEFAULT_SIM_DURATION_MINUTES;

  return Math.max(1, Math.round(safeMinutes * SECONDS_IN_MINUTE));
}

function isValidSimulationDuration(value) {
  const parsedMinutes = Number(value);
  return Number.isFinite(parsedMinutes) && parsedMinutes > 0;
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function parseNumberList(value) {
  return String(value || '')
    .split(',')
    .map((item) => Number(item.trim()))
    .filter((item) => Number.isFinite(item));
}

function getAttackTimeUnit(attack) {
  return attack?.scheduleUnit === 'seconds' ? 'seconds' : 'minutes';
}

function getAttackScheduleValues(attack, key) {
  const values = parseNumberList(attack?.[key]);

  if (getAttackTimeUnit(attack) === 'seconds') {
    return values;
  }

  return values.map((value) => value * SECONDS_IN_MINUTE);
}

function formatSeconds(totalSeconds) {
  const seconds = Math.max(0, Math.round(totalSeconds));
  const minutes = Math.floor(seconds / SECONDS_IN_MINUTE);
  const remainder = seconds % SECONDS_IN_MINUTE;

  if (minutes === 0) {
    return `${remainder}s`;
  }

  if (remainder === 0) {
    return `${minutes}m`;
  }

  return `${minutes}m ${remainder}s`;
}

function formatSecondList(values) {
  return values.map((value) => String(Math.round(value))).join(',');
}

function getFirstSchedule(attack, timelineLimitSeconds) {
  const firstOccurrence = getAttackScheduleValues(attack, 'occurrence')[0] ?? 0;
  const firstDuration =
    getAttackScheduleValues(attack, 'duration')[0] ??
    Math.min(DEFAULT_ATTACK_DURATION_SECONDS, timelineLimitSeconds);
  const occurrence = clamp(
    Math.round(firstOccurrence),
    0,
    timelineLimitSeconds - 1
  );
  const maxDuration = Math.max(1, timelineLimitSeconds - occurrence);

  return {
    occurrence,
    duration: clamp(Math.round(firstDuration), 1, maxDuration),
  };
}

function buildTimelineSegments(attacks, timelineLimitSeconds) {
  return attacks.flatMap((attack, attackIndex) => {
    const occurrences = getAttackScheduleValues(attack, 'occurrence');
    const durations = getAttackScheduleValues(attack, 'duration');
    const segmentCount = Math.min(occurrences.length, durations.length);

    return Array.from({ length: segmentCount }, (_, segmentIndex) => {
      const occurrence = clamp(
        Math.round(occurrences[segmentIndex]),
        0,
        timelineLimitSeconds
      );
      const duration = Math.max(Math.round(durations[segmentIndex]), 0);
      const visibleDuration = Math.min(duration, timelineLimitSeconds - occurrence);

      if (visibleDuration <= 0) {
        return null;
      }

      return {
        attackIndex,
        segmentIndex,
        name: attack.name,
        occurrence,
        duration,
      };
    }).filter(Boolean);
  });
}

function getTimelineTicks(timelineLimitSeconds, count) {
  return Array.from({ length: count }, (_, index) => {
    const value = Math.round((timelineLimitSeconds / (count - 1)) * index);
    return {
      value,
      left: (value / timelineLimitSeconds) * 100,
    };
  });
}

function withUpdatedSegment(attack, segmentIndex, occurrence, duration) {
  const occurrences = getAttackScheduleValues(attack, 'occurrence');
  const durations = getAttackScheduleValues(attack, 'duration');
  occurrences[segmentIndex] = occurrence;
  durations[segmentIndex] = duration;

  return {
    ...attack,
    occurrence: formatSecondList(occurrences),
    duration: formatSecondList(durations),
    scheduleUnit: 'seconds',
  };
}

export default function AttackManager({ simDuration }) {
  const attacks = useSelector((state) => state.sim.attacks);
  const dispatch = useDispatch();
  const timelineLimitSeconds = getTimelineLimitSeconds(simDuration);
  const durationIsValid = isValidSimulationDuration(simDuration);
  const timelineSegments = useMemo(
    () => buildTimelineSegments(attacks, timelineLimitSeconds),
    [attacks, timelineLimitSeconds]
  );
  const compactTicks = useMemo(
    () => getTimelineTicks(timelineLimitSeconds, 3),
    [timelineLimitSeconds]
  );
  const largeTicks = useMemo(
    () => getTimelineTicks(timelineLimitSeconds, 10),
    [timelineLimitSeconds]
  );

  const [isTimelineOpen, setIsTimelineOpen] = useState(false);
  const [isClearConfirmOpen, setIsClearConfirmOpen] = useState(false);
  const [clearConfirmed, setClearConfirmed] = useState(false);
  const [editIndex, setEditIndex] = useState(null);
  const [newAttackName, setNewAttackName] = useState(predefinedAttacks[0]);
  const [sliderOccurrence, setSliderOccurrence] = useState(0);
  const [sliderDuration, setSliderDuration] = useState(
    DEFAULT_ATTACK_DURATION_SECONDS
  );
  const [error, setError] = useState('');
  const [dragState, setDragState] = useState(null);

  const maxDurationForOccurrence = Math.max(
    1,
    timelineLimitSeconds - sliderOccurrence
  );
  const largeTimelineWidth = Math.max(1280, timelineLimitSeconds * 0.45);

  const setSingleSchedule = (occurrence, duration) => {
    const safeOccurrence = clamp(
      Math.round(Number(occurrence) || 0),
      0,
      timelineLimitSeconds - 1
    );
    const safeDuration = clamp(
      Math.round(Number(duration) || DEFAULT_ATTACK_DURATION_SECONDS),
      1,
      Math.max(1, timelineLimitSeconds - safeOccurrence)
    );

    setSliderOccurrence(safeOccurrence);
    setSliderDuration(safeDuration);
  };

  const loadAttackForEdit = (index = null) => {
    const attack = index !== null ? attacks[index] : null;
    const firstSchedule = getFirstSchedule(attack, timelineLimitSeconds);

    setEditIndex(index);
    setNewAttackName(attack?.name || predefinedAttacks[0]);
    setSliderOccurrence(firstSchedule.occurrence);
    setSliderDuration(firstSchedule.duration);
    setError('');
  };

  const openTimeline = (index = null) => {
    if (!durationIsValid) {
      setError('Set a valid simulation duration before adding attacks.');
      return;
    }

    loadAttackForEdit(index);
    setIsTimelineOpen(true);
  };

  const closeTimeline = () => {
    setIsTimelineOpen(false);
    setDragState(null);
    setError('');
  };

  const updateExistingAttackWindow = (attackIndex, segmentIndex, occurrence, duration) => {
    const attack = attacks[attackIndex];
    if (!attack) {
      return;
    }

    const updatedAttack = withUpdatedSegment(
      attack,
      segmentIndex,
      occurrence,
      duration
    );
    dispatch(
      simActions.updateAttack({
        index: attackIndex,
        attack: updatedAttack,
      })
    );
  };

  useEffect(() => {
    if (!dragState) {
      return undefined;
    }

    const handlePointerMove = (event) => {
      const secondsDelta = Math.round(
        ((event.clientX - dragState.startX) / dragState.timelineWidth) *
          timelineLimitSeconds
      );
      let nextOccurrence = dragState.startOccurrence;
      let nextDuration = dragState.startDuration;

      if (dragState.mode === 'move') {
        nextOccurrence = clamp(
          dragState.startOccurrence + secondsDelta,
          0,
          timelineLimitSeconds - dragState.startDuration
        );
      } else {
        nextDuration = clamp(
          dragState.startDuration + secondsDelta,
          1,
          timelineLimitSeconds - dragState.startOccurrence
        );
      }

      updateExistingAttackWindow(
        dragState.attackIndex,
        dragState.segmentIndex,
        nextOccurrence,
        nextDuration
      );

      if (editIndex === dragState.attackIndex) {
        setSliderOccurrence(nextOccurrence);
        setSliderDuration(nextDuration);
      }
    };

    const handlePointerUp = () => {
      setDragState(null);
    };

    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerUp);

    return () => {
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
    };
  }, [dragState, editIndex, attacks, timelineLimitSeconds]);

  const handleOccurrenceSliderChange = (value) => {
    setSingleSchedule(value, sliderDuration);
  };

  const handleDurationSliderChange = (value) => {
    setSingleSchedule(sliderOccurrence, value);
  };

  const handleSaveAttack = () => {
    if (!durationIsValid) {
      setError('Set a valid simulation duration before adding attacks.');
      return;
    }

    if (sliderOccurrence + sliderDuration > timelineLimitSeconds) {
      setError(
        `Attack window must stay inside 0-${timelineLimitSeconds} seconds.`
      );
      return;
    }

    const attack = {
      name: newAttackName,
      duration: String(sliderDuration),
      occurrence: String(sliderOccurrence),
      scheduleUnit: 'seconds',
    };

    if (editIndex !== null) {
      dispatch(simActions.updateAttack({ index: editIndex, attack }));
    } else {
      dispatch(simActions.addAttack(attack));
      setEditIndex(attacks.length);
    }

    setError('');
  };

  const handleDelete = (indexToDelete) => {
    dispatch(simActions.removeAttack(indexToDelete));
    if (editIndex === indexToDelete) {
      loadAttackForEdit(null);
    } else if (editIndex > indexToDelete) {
      setEditIndex(editIndex - 1);
    }
  };

  const openClearConfirm = () => {
    setClearConfirmed(false);
    setIsClearConfirmOpen(true);
  };

  const closeClearConfirm = () => {
    setClearConfirmed(false);
    setIsClearConfirmOpen(false);
  };

  const handleClearAllAttacks = () => {
    if (!clearConfirmed) {
      return;
    }

    dispatch(simActions.clearAttacks());
    setEditIndex(null);
    setDragState(null);
    setIsTimelineOpen(false);
    closeClearConfirm();
  };

  const startDrag = (event, segment, mode) => {
    const timelineElement = event.currentTarget.closest(
      `.${styles.timelineTrack}`
    );
    const timelineWidth = timelineElement?.getBoundingClientRect().width;

    if (!timelineWidth) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    loadAttackForEdit(segment.attackIndex);
    setDragState({
      mode,
      attackIndex: segment.attackIndex,
      segmentIndex: segment.segmentIndex,
      startX: event.clientX,
      timelineWidth,
      startOccurrence: segment.occurrence,
      startDuration: segment.duration,
    });
  };

  const renderTimeline = (isLarge = false) => {
    const timelineHeight = Math.max(
      80,
      timelineSegments.length * (isLarge ? 42 : 34) + 38
    );
    const timelineWidth = isLarge ? largeTimelineWidth : '100%';
    const ticks = isLarge ? largeTicks : compactTicks;

    return (
      <div className={styles.timelineViewport}>
        <div
          className={`${styles.timelineTrack} ${
            isLarge ? styles.timelineTrackLarge : ''
          }`}
          style={{
            height: `${timelineHeight}px`,
            width:
              typeof timelineWidth === 'number'
                ? `${timelineWidth}px`
                : timelineWidth,
          }}
        >
          <div className={styles.timelineAxis}>
            {ticks.map((tick) => (
              <span
                key={tick.value}
                className={styles.timelineTick}
                style={{ left: `${tick.left}%` }}
              >
                {formatSeconds(tick.value)}
              </span>
            ))}
          </div>

          {timelineSegments.length === 0 ? (
            <p className={styles.timelineEmpty}>No attack windows on the timeline</p>
          ) : (
            timelineSegments.map((segment, index) => {
              const left = (segment.occurrence / timelineLimitSeconds) * 100;
              const width = Math.max(
                (segment.duration / timelineLimitSeconds) * 100,
                isLarge ? 0.7 : 2
              );
              const isSelected = editIndex === segment.attackIndex;

              return (
                <div
                  key={`${segment.attackIndex}-${segment.segmentIndex}`}
                  role="button"
                  tabIndex={0}
                  className={`${styles.timelineBlock} ${
                    isLarge ? styles.timelineBlockLarge : ''
                  } ${isSelected ? styles.timelineBlockSelected : ''}`}
                  style={{
                    left: `${left}%`,
                    width: `${width}%`,
                    top: `${30 + index * (isLarge ? 42 : 34)}px`,
                  }}
                  onClick={() => {
                    if (isLarge) {
                      loadAttackForEdit(segment.attackIndex);
                    } else {
                      openTimeline(segment.attackIndex);
                    }
                  }}
                  onPointerDown={(event) =>
                    isLarge ? startDrag(event, segment, 'move') : undefined
                  }
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      if (isLarge) {
                        loadAttackForEdit(segment.attackIndex);
                      } else {
                        openTimeline(segment.attackIndex);
                      }
                    }
                  }}
                  title={`${segment.name}: starts ${segment.occurrence}s, lasts ${segment.duration}s`}
                >
                  <span>{segment.name}</span>
                  <small>
                    {formatSeconds(segment.occurrence)}-
                    {formatSeconds(segment.occurrence + segment.duration)}
                  </small>
                  {isLarge && (
                    <span
                      className={styles.resizeHandle}
                      onPointerDown={(event) => startDrag(event, segment, 'resize')}
                    />
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={styles.manager}>
      <h3 className={styles.title}>Cyber Attacks</h3>

      <div className={styles.timelineHeader}>
        <span>Attack timeline</span>
        <span>
          {durationIsValid
            ? formatSeconds(timelineLimitSeconds)
            : 'Set duration first'}
        </span>
      </div>

      {!durationIsValid && (
        <p className={styles.warning}>
          Set a valid simulation duration before adding attacks.
        </p>
      )}

      {renderTimeline(false)}

      <button
        type="button"
        onClick={() => openTimeline(editIndex)}
        className={styles.timelineOpenButton}
        disabled={!durationIsValid}
      >
        Open timeline editor
      </button>

      {attacks.length === 0 ? (
        <p className={styles.empty}>No attacks were selected yet</p>
      ) : (
        <ul className={styles.attackList}>
          {attacks.map((attack, index) => (
            <li key={index} className={styles.attackItem}>
              <button
                type="button"
                className={styles.attackSummary}
                onClick={() => openTimeline(index)}
              >
                <strong>{attack.name}</strong>
                <span>
                  Duration: {formatSecondList(getAttackScheduleValues(attack, 'duration'))} sec
                </span>
                <span>
                  Occurrence: {formatSecondList(getAttackScheduleValues(attack, 'occurrence'))} sec
                </span>
              </button>
              <button
                type="button"
                onClick={() => handleDelete(index)}
                className={styles.deleteButton}
                aria-label={`Delete ${attack.name}`}
              >
                X
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className={styles.managerActions}>
        <button
          type="button"
          onClick={() => openTimeline(null)}
          className={styles.addButton}
          disabled={!durationIsValid}
        >
          Add attack
        </button>
        {attacks.length > 0 && (
          <button
            type="button"
            onClick={openClearConfirm}
            className={styles.clearAllButton}
          >
            Remove all attacks
          </button>
        )}
      </div>

      {isTimelineOpen && (
        <div className={styles.modalOverlay}>
          <div className={styles.timelineModalContent}>
            <div className={styles.timelineModalHeader}>
              <h4>Attack Timeline Editor</h4>
              <button
                type="button"
                onClick={closeTimeline}
                className={styles.closeButton}
              >
                X
              </button>
            </div>

            <div className={styles.timelineEditorLayout}>
              <div className={styles.timelineEditorSurface}>
                {renderTimeline(true)}
              </div>

              <aside className={styles.editorPanel}>
                <div className={styles.editorPanelHeader}>
                  <h5>{editIndex !== null ? 'Edit Attack' : 'New Attack'}</h5>
                  <button
                    type="button"
                    onClick={() => loadAttackForEdit(null)}
                    className={styles.secondaryButton}
                    disabled={!durationIsValid}
                  >
                    New
                  </button>
                </div>

                <label>
                  Attack Name
                  <select
                    value={newAttackName}
                    onChange={(e) => setNewAttackName(e.target.value)}
                  >
                    {predefinedAttacks.map((name) => (
                      <option key={name} value={name}>
                        {name}
                      </option>
                    ))}
                  </select>
                </label>

                <div className={styles.sliderGroup}>
                  <div className={styles.sliderLabel}>
                    <span>Start second</span>
                    <strong>{formatSeconds(sliderOccurrence)}</strong>
                  </div>
                  <div className={styles.sliderControl}>
                    <input
                      type="range"
                      min="0"
                      max={Math.max(0, timelineLimitSeconds - 1)}
                      step="1"
                      value={sliderOccurrence}
                      onChange={(e) => handleOccurrenceSliderChange(e.target.value)}
                    />
                    <input
                      className={styles.sliderNumber}
                      type="number"
                      min="0"
                      max={Math.max(0, timelineLimitSeconds - 1)}
                      step="1"
                      value={sliderOccurrence}
                      onChange={(e) => handleOccurrenceSliderChange(e.target.value)}
                    />
                  </div>
                </div>

                <div className={styles.sliderGroup}>
                  <div className={styles.sliderLabel}>
                    <span>Duration seconds</span>
                    <strong>{formatSeconds(sliderDuration)}</strong>
                  </div>
                  <div className={styles.sliderControl}>
                    <input
                      type="range"
                      min="1"
                      max={maxDurationForOccurrence}
                      step="1"
                      value={Math.min(sliderDuration, maxDurationForOccurrence)}
                      onChange={(e) => handleDurationSliderChange(e.target.value)}
                    />
                    <input
                      className={styles.sliderNumber}
                      type="number"
                      min="1"
                      max={maxDurationForOccurrence}
                      step="1"
                      value={Math.min(sliderDuration, maxDurationForOccurrence)}
                      onChange={(e) => handleDurationSliderChange(e.target.value)}
                    />
                  </div>
                </div>

                <div className={styles.previewBar}>
                  <span
                    style={{
                      left: `${(sliderOccurrence / timelineLimitSeconds) * 100}%`,
                      width: `${Math.max(
                        (sliderDuration / timelineLimitSeconds) * 100,
                        2
                      )}%`,
                    }}
                  />
                </div>

                {error && <p className={styles.error}>{error}</p>}

                <div className={styles.editorActions}>
                  {attacks.length > 0 && (
                    <button
                      type="button"
                      onClick={openClearConfirm}
                      className={styles.secondaryButton}
                    >
                      Remove All
                    </button>
                  )}
                  {editIndex !== null && (
                    <button
                      type="button"
                      onClick={() => handleDelete(editIndex)}
                      className={styles.cancelBtn}
                    >
                      Delete
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={handleSaveAttack}
                    className={styles.saveBtn}
                    disabled={!durationIsValid}
                  >
                    {editIndex !== null ? 'Save Changes' : 'Add Attack'}
                  </button>
                </div>
              </aside>
            </div>
          </div>
        </div>
      )}

      {isClearConfirmOpen && (
        <div className={styles.modalOverlay}>
          <div className={styles.confirmModalContent}>
            <h4>Remove All Attacks</h4>
            <p>
              This will delete every scheduled attack from the current setup.
              After they are removed, the simulation duration can be edited
              again.
            </p>
            <label className={styles.confirmCheck}>
              <input
                type="checkbox"
                checked={clearConfirmed}
                onChange={(event) => setClearConfirmed(event.target.checked)}
              />
              <span>I understand that all scheduled attacks will be removed.</span>
            </label>
            <div className={styles.modalActions}>
              <button
                type="button"
                onClick={closeClearConfirm}
                className={styles.cancelBtn}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleClearAllAttacks}
                className={styles.saveBtn}
                disabled={!clearConfirmed}
              >
                Remove All
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
