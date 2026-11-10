export interface LinePoint {
  time: string;
  value: number;
}

export interface BollingerLines {
  upper: LinePoint[];
  middle: LinePoint[];
  lower: LinePoint[];
}

/**
 * Bollinger Bands, matching the API's rule: a simple moving average of the
 * closes, plus and minus `stdevs` population standard deviations.
 */
export function bollingerBands(
  dates: string[],
  closes: number[],
  period = 20,
  stdevs = 2,
): BollingerLines {
  const upper: LinePoint[] = [];
  const middle: LinePoint[] = [];
  const lower: LinePoint[] = [];

  for (let i = period - 1; i < closes.length; i += 1) {
    const window = closes.slice(i - period + 1, i + 1);
    const mean = window.reduce((sum, value) => sum + value, 0) / period;
    const variance =
      window.reduce((sum, value) => sum + (value - mean) ** 2, 0) / period;
    const spread = stdevs * Math.sqrt(variance);
    upper.push({ time: dates[i], value: mean + spread });
    middle.push({ time: dates[i], value: mean });
    lower.push({ time: dates[i], value: mean - spread });
  }

  return { upper, middle, lower };
}

/** Highest close of the trailing `window` days, once a full window exists. */
export function rollingHigh(
  dates: string[],
  closes: number[],
  window = 252,
): LinePoint[] {
  const points: LinePoint[] = [];
  for (let i = window - 1; i < closes.length; i += 1) {
    points.push({
      time: dates[i],
      value: Math.max(...closes.slice(i - window + 1, i + 1)),
    });
  }
  return points;
}