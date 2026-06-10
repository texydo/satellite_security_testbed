import { configureStore } from '@reduxjs/toolkit';

import satSlice from './sat-slice';
import systemSlice from './system-slice';
import simSlice from './sim-slice';
import graphSlice from './graph-slice';

const store = configureStore({
  reducer: {
    sat: satSlice.reducer,
    system: systemSlice.reducer,
    sim: simSlice.reducer,
    graphs: graphSlice.reducer,
  },
});

export default store;
