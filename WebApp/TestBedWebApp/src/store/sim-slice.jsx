import { createSlice } from '@reduxjs/toolkit';
import {
  demoTLE,
  demoTleFileName,
  demoStartEpochTime,
  demoDuration,
  demoPlaybackSpeed,
  demoAttacks,
} from '../config/demoParameters';

const simInitialState = {
  demoMode: false,
  simStarting: false,
  simRunning: false,
  simPaused: false,
  numPlannedSims: 0,
  MinutesBetweenSims: 0,
  simDuration: 0,
  tle: '',
  tleFileName: '',
  attacks: [],
  startEpochTime: 0,
  currentEpochTime: 0,
  playbackSpeed: 1,
  simPassedSeconds: 0,
  saveToMongo: false,
  saveCommandFile: false,
  loadCommandFile: false,
  commandFileName: '',
  commandFileContent: '',
  simulationCompleted: false,
  completionMessage: '',
};

const simSlice = createSlice({
  name: 'sat',
  initialState: simInitialState,
  reducers: {
    setSimInitialParams(state, action) {
      state.demoMode = false;
      state.playbackSpeed = 1;
      state.simStarting = false;
      state.simRunning = false;
      state.simPaused = false;
      state.simPassedSeconds = 0;
      state.simulationCompleted = false;
      state.completionMessage = '';
      const simParams = action.payload;

      state.tleFileName = simParams.tleFileName;
      state.simDuration = simParams.simulationDuration;
      state.startEpochTime = simParams.startEpochTime;
      state.numPlannedSims = simParams.numSimulations;
      state.saveToMongo = simParams.saveToMongo;
      state.saveCommandFile = simParams.saveCommandFile;
      state.loadCommandFile = simParams.loadCommandFile;
      state.commandFileName = simParams.commandFileName;
      state.commandFileContent = simParams.commandFileContent;
    },
    setTLE(state, action) {
      state.tle = action.payload;
    },
    addAttack(state, action) {
      const newAttack = action.payload;
      state.attacks = [...state.attacks, newAttack];
    },
    updateAttack(state, action) {
      const { index, attack } = action.payload;
      if (index >= 0 && index < state.attacks.length) {
        state.attacks[index] = attack;
      }
    },
    removeAttack(state, action) {
      state.attacks = state.attacks.filter((_, i) => i !== action.payload);
    },
    clearAttacks(state) {
      state.attacks = [];
    },
    startSimulation(state) {
      state.simStarting = false;
      state.simRunning = true;
      state.simPaused = false;
      state.simPassedSeconds = 0;
    },
    startSimulationPending(state) {
      state.simStarting = true;
      state.simRunning = false;
      state.simPaused = false;
      state.simPassedSeconds = 0;
    },
    stopSimulation(state) {
      state.simStarting = false;
      state.simRunning = false;
      state.simPaused = false;
      state.simPassedSeconds = 0;
    },
    toggleSimRunning(state) {
      state.simRunning = !state.simRunning;
    },
    toggleSimPaused(state) {
      state.simPaused = !state.simPaused;
    },
    completeSimulation(state, action) {
      state.simRunning = false;
      state.simPaused = false;
      state.simStarting = false;
      state.attacks = [];
      state.simPassedSeconds = 0;
      state.simulationCompleted = true;
      state.completionMessage =
        action.payload || 'Simulation completed successfully.';
    },
    dismissCompletion(state) {
      state.simulationCompleted = false;
      state.completionMessage = '';
    },
    loadDemoParams(state) {
      state.demoMode = true;
      state.simStarting = false;
      state.simRunning = false;
      state.simPaused = false;
      state.simPassedSeconds = 0;
      state.simulationCompleted = false;
      state.completionMessage = '';
      state.tle = demoTLE;
      state.tleFileName = demoTleFileName;
      state.startEpochTime = demoStartEpochTime;
      state.simDuration = demoDuration;
      state.playbackSpeed = demoPlaybackSpeed;
      state.attacks = demoAttacks;
      state.saveToMongo = false;
      state.saveCommandFile = false;
      state.loadCommandFile = false;
      state.commandFileName = '';
      state.commandFileContent = '';
    },
    setSimPassedSeconds(state, action) {
      state.simPassedSeconds = typeof action.payload === 'function'
        ? action.payload(state.simPassedSeconds)
        : action.payload;
    },
  },
});

export const simActions = simSlice.actions;

export default simSlice;
