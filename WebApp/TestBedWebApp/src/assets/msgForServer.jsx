import store from '../store/index.jsx';

export const setRequestedGraphsData = {
  stage: 'setRequestedGraphs',
  type: 'request',
  data: {
    requestedGraphs: [
      'EPS_BATTERY_TOTAL_VOLTAGE',
      'EPS_BATTERY_CURRENT',
      'EPS_SOLAR_PANEL_1_TEMPERATURE',
      'EPS_SOLAR_PANEL_2_TEMPERATURE',
      'EPS_SOLAR_PANEL_1_OUTPUT_CURRENT',
      'EPS_SOLAR_PANEL_2_OUTPUT_CURRENT',
      'EPS_SOLAR_PANEL_1_VOLTAGE',
      'EPS_SOLAR_PANEL_2_VOLTAGE',
      'OBC_PROCESSOR_TEMPERATURE',
      'OBC_PROCESSOR_VOLTAGE',
      'TPL_CURRENT_TEMPERATURE',
      'EPS_SOLAR_PANEL_2_TEMPERATURE',
    ],
  },
};

export const pauseData = {
  stage: 'pause',
  type: 'request',
  data: {},
};

export const resumeData = {
  stage: 'resume',
  type: 'request',
  data: {},
};

export const stopData = {
  stage: 'stop',
  type: 'request',
  data: {},
};

export function createSetAttackFactorMsg(factor) {
  return {
    stage: 'setAttackFactor',
    type: 'request',
    data: {
      attackFactor: factor,
    },
  };
}

export function createStartMsg() {
  const state = store.getState();
  const simState = state.sim;

  return {
    stage: 'start',
    type: 'request',
    data: {
      simDuration: simState.simDuration,
      tle: simState.tle,
      tleFileName: simState.tleFileName,
      attacks: simState.attacks,
      time: parseTLETimeToUTC(simState.tle),
      startEpochTime: +simState.startEpochTime,
      night_probability: 100,
      playbackSpeed: simState.playbackSpeed,
      demoMode: simState.demoMode ? 1 : 0,
      saveToMongo: simState.saveToMongo ? 1 : 0,
      saveCommandFile: simState.saveCommandFile ? 1 : 0,
      loadCommandFile: simState.loadCommandFile ? 1 : 0,
      commandFileName: simState.commandFileName,
      commandFileContent: simState.commandFileContent,
    },
  };
}

function parseTLETimeToUTC(tle) {
  const line1 = tle[1];
  const epochStr = line1.slice(18, 32); // Extract YYDDD.DDDDDDDD

  const yearShort = parseInt(epochStr.slice(0, 2), 10);
  const year = yearShort < 57 ? 2000 + yearShort : 1900 + yearShort;

  const dayOfYear = parseFloat(epochStr.slice(2)); // DDD.DDDDDDDD

  const startOfYear = new Date(Date.UTC(year, 0, 1)); // Jan 1st UTC
  const millis = (dayOfYear - 1) * 24 * 60 * 60 * 1000;
  const epochDate = new Date(startOfYear.getTime() + millis);

  const Y = epochDate.getUTCFullYear();
  const M = epochDate.getUTCMonth() + 1;
  const D = epochDate.getUTCDate();
  const h = epochDate.getUTCHours();
  const m = epochDate.getUTCMinutes();
  const s = epochDate.getUTCSeconds() + epochDate.getUTCMilliseconds() / 1000;

  return [Y, M, D, h, m, parseFloat(s.toFixed(1))];
}
