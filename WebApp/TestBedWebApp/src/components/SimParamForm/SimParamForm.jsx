import { Form, redirect, useNavigate } from 'react-router-dom';
import styles from './SimParamForm.module.css';
import { useDispatch, useSelector } from 'react-redux';
import store from '../../store/index.jsx';
import { simActions } from '../../store/sim-slice';
import AttackManager from '../AttackManager/AttackManager';
import { useState } from 'react';
import { tleToEpochSeconds } from '../../utils/utils';

export default function SimParamForm() {
  const dispatch = useDispatch();
  const attacks = useSelector((state) => state.sim.attacks);
  const [epochTime, setEpochTime] = useState(0);
  const [simulationDuration, setSimulationDuration] = useState('90');
  const [commandFileAction, setCommandFileAction] = useState('none');
  const [commandFileName, setCommandFileName] = useState('');
  const [commandFileContent, setCommandFileContent] = useState('');
  const navigate = useNavigate();
  const durationLocked = attacks.length > 0;

  function handleUserTLE(event) {
    const file = event.target.files[0];
    if (file && file.type === 'text/plain') {
      const reader = new FileReader();
      reader.onload = (e) => {
        const rawText = e.target.result;
        const tleLines = rawText
          .trim()
          .split('\n')
          .map((line) => line.trim());
        dispatch(simActions.setTLE(tleLines));
        setEpochTime(tleToEpochSeconds(tleLines[1]));
      };
      reader.onerror = (e) => {
        console.error('Error reading file:', e.target.error);
      };
      reader.readAsText(file);
    } else {
      alert('Please upload a valid .txt file');
    }
  }

  function handleDemoParamSet() {
    dispatch(simActions.loadDemoParams());
    navigate('/Sim');
  }

  function handleCommandFileUpload(event) {
    const file = event.target.files[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      setCommandFileName(file.name);
      setCommandFileContent(e.target.result);
      setCommandFileAction('load');
    };
    reader.onerror = (e) => {
      console.error('Error reading command file:', e.target.error);
    };
    reader.readAsText(file);
  }

  return (
    <Form method="post" className={styles.form}>
      <h2 className={styles.header}>🛰️ Simulation Configuration</h2>

      <p className={styles.formGroup}>
        <label htmlFor="tleFile">Choose TLE file</label>
        <input
          id="tleFile"
          type="file"
          accept=".txt"
          name="tleFile"
          required
          onChange={handleUserTLE}
        />
      </p>

      <p className={styles.formGroup}>
        <label htmlFor="simulationDuration">
          Simulation Duration (minutes)
        </label>
        <input
          id="simulationDuration"
          type="number"
          name="simulationDuration"
          value={simulationDuration}
          min="1"
          readOnly={durationLocked}
          className={durationLocked ? styles.lockedInput : undefined}
          onChange={(event) => setSimulationDuration(event.target.value)}
        />
        {durationLocked && (
          <span className={styles.fieldNote}>
            Duration is locked while attacks are scheduled.
          </span>
        )}
      </p>

      <p className={styles.formGroup}>
        <label htmlFor="startEpochTime">Start Epoch Time</label>
        <input
          id="startEpochTime"
          type="number"
          name="startEpochTime"
          value={epochTime}
          onChange={(event) => setEpochTime(event.target.value)}
          required
        />
      </p>

      <p className={styles.formGroup}>
        <label htmlFor="numSimulations">Number of Simulations</label>
        <input
          id="numSimulations"
          type="number"
          name="numSimulations"
          defaultValue={1}
          required
        />
      </p>

      <label className={styles.checkboxGroup}>
        <input id="saveToMongo" type="checkbox" name="saveToMongo" />
        <span>Save simulation data to MongoDB</span>
      </label>

      <div className={styles.commandFileControls}>
        <label htmlFor="commandFileName">Manager command file name</label>
        <input
          id="commandFileName"
          type="text"
          name="commandFileName"
          placeholder="latest_commands.txt"
          value={commandFileName}
          onChange={(event) => setCommandFileName(event.target.value)}
        />
        {commandFileAction === 'load' && (
          <label className={styles.filePickerButton}>
            Choose saved file
            <input
              type="file"
              accept=".txt"
              onChange={handleCommandFileUpload}
            />
          </label>
        )}
        <input
          type="hidden"
          name="commandFileAction"
          value={commandFileAction}
        />
        <div className={styles.commandFileButtons}>
          <button
            type="button"
            className={`${styles.commandFileButton} ${
              commandFileAction === 'save' ? styles.commandFileButtonActive : ''
            }`}
            onClick={() =>
              setCommandFileAction(
                commandFileAction === 'save' ? 'none' : 'save'
              )
            }
          >
            Save generated file
          </button>
          <button
            type="button"
            className={`${styles.commandFileButton} ${
              commandFileAction === 'load' ? styles.commandFileButtonActive : ''
            }`}
            onClick={() =>
              setCommandFileAction(
                commandFileAction === 'load' ? 'none' : 'load'
              )
            }
          >
            Load saved file
          </button>
        </div>
      </div>

      <input
        type="hidden"
        name="saveCommandFile"
        value={commandFileAction === 'save' ? 'on' : ''}
      />
      <input
        type="hidden"
        name="loadCommandFile"
        value={commandFileAction === 'load' ? 'on' : ''}
      />
      <input
        type="hidden"
        name="commandFileContent"
        value={commandFileContent}
      />

      <div className={styles.attackManager}>
        <AttackManager simDuration={simulationDuration} />
      </div>

      <div className={styles.buttonGroup}>
        <button type="submit" className={styles.saveButton}>
          🚀 Start Simulation
        </button>
        <button
          type="button"
          className={styles.demoButton}
          onClick={handleDemoParamSet}
        >
          🎮 Demo
        </button>
      </div>
    </Form>
  );
}

export async function action({ request, params }) {
  const data = await request.formData();

  const simParams = {
    tleFileName: data.get('tleFile'),
    simulationDuration: data.get('simulationDuration'),
    numSimulations: data.get('numSimulations'),
    startEpochTime: data.get('startEpochTime'),
    saveToMongo: data.get('saveToMongo') === 'on',
    saveCommandFile: data.get('saveCommandFile') === 'on',
    loadCommandFile: data.get('loadCommandFile') === 'on',
    commandFileName: data.get('commandFileName'),
    commandFileContent: data.get('commandFileContent'),
  };

  store.dispatch(simActions.setSimInitialParams(simParams));

  return redirect('/Sim');
}
