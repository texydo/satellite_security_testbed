

export function tleToEpochSeconds(tleLine1) {
  const epochStr = tleLine1.substring(18, 32).trim();

  const yearStr = epochStr.substring(0, 2);
  const dayOfYearStr = epochStr.substring(2);

  const year = 2000 + parseInt(yearStr, 10);
  const dayOfYear = parseFloat(dayOfYearStr);

  const date = new Date(Date.UTC(year, 0));
  date.setUTCDate(date.getUTCDate() + Math.floor(dayOfYear) - 1);

  const fractionalDay = dayOfYear % 1;
  const secondsInDay = 86400;
  const additionalSeconds = fractionalDay * secondsInDay;
  const epochMillis = date.getTime() + additionalSeconds * 1000;

  return Math.floor(epochMillis / 1000);
}

