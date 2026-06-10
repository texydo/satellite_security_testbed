import { createSlice } from '@reduxjs/toolkit';

const satInitialState = {
  time: 0,
  longitude: 0,
  latitude: 0,
  elevation: 0,
  solarIntensity: 0,
  magneticField_X: 0,
  magneticField_Y: 0,
  magneticField_Z: 0,
};

const satSlice = createSlice({
  name: 'sat',
  initialState: satInitialState,
  reducers: {
    updateSatState(state, action) {
      const msg = action.payload;
      state.time = msg.Time;
      state.longitude = msg.Longitude;
      state.latitude = msg.Latitude;
      state.elevation = msg.Altitude;
      state.solarIntensity = msg['Solar Intensity'];
      state.magneticField_X = msg['Magnetic Field X'];
      state.magneticField_Y = msg['Magnetic Field Y'];
      state.magneticField_Z = msg['Magnetic Field Z'];
    },
  },
});

export const satActions = satSlice.actions;

export default satSlice;
