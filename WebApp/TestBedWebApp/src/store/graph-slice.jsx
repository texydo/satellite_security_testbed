import { createSlice } from '@reduxjs/toolkit';
import { createSetAttackFactorMsg } from '../assets/msgForServer';

const graphInitialState = {
  graphs: {},
  commandsReceived: [],
  redDotFlags: {
    EPS_BATTERY_TOTAL_VOLTAGE: [],
    EPS_BATTERY_CURRENT: [],
  },
  currentAttackFactor: 1,
};

let commandCounter = 0;

const graphSlice = createSlice({
  name: 'graphs',
  initialState: graphInitialState,
  reducers: {
    handleNewCommand(state, action) {
      const newCommand = {
        ...action.payload,
        id: commandCounter++, // Add sequential ID
      };
      state.commandsReceived.push(newCommand);
    },
    handleGraphUpdate(state, action) {
      const graphs = action.payload;
      state.graphs = graphs;
    },
    resetState(state) {
      state.graphs = {};
      state.commandsReceived = [];
      commandCounter = 0;
    },
    flagRedDotsForKey(state, action) {
      const { key, factor, duration, isDetected} = action.payload;
      const now = Math.floor(Date.now() / 1000);
  
      if (!state.redDotFlags[key]) {
        state.redDotFlags[key] = [];
      }

      state.redDotFlags[key].push({
        factor,
        startTime: now,
        endTime: now + duration,
        isDetected,
      });
    },
    clearExpiredRedDots(state) {
      const now = Math.floor(Date.now() / 1000);
      for (const key in state.redDotFlags) {
        state.redDotFlags[key] = state.redDotFlags[key].filter(
          (dot) => dot.endTime > now
        );
      }
    },
    setCurrentAttackFactor(state, action) {
      const newFactor = action.payload;
      state.currentAttackFactor = newFactor;
    
      const msg = createSetAttackFactorMsg(newFactor);
    
      // Use correct WebSocket wrapper
      const socket = window.simSocket; // <-- reference set in StatusPanel or wherever you open it
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(msg));
      }
    },    
  },
});

export const graphActions = graphSlice.actions;

export default graphSlice;
