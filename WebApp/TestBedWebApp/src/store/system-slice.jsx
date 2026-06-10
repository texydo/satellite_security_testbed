import { createSlice } from '@reduxjs/toolkit';

const systemInitialState = {
  isOpConnected: false,
  isCyberConncted: false,
  isEnvConncted: false,
};

const systemSlice = createSlice({
  name: 'system',
  initialState: systemInitialState,
  reducers: {
    updateComputerState(state, action) {
      if (action.payload === 'operational') {
        state.isOpConnected = !state.isOpConnected;
      } else if (action.payload === 'enviroment') {
        state.isEnvConncted = !state.isEnvConncted;
      } else if (action.payload === 'cyber') {
        state.isCyberConncted = !state.isCyberConncted;
      }
    },
  },
});

export const systemActions = systemSlice.actions;

export default systemSlice;
