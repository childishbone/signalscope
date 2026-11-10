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

/** Simple moving average of the closes, once a full window exists. */
export function sma(
  dates: string[],
  closes: number[],
  period: number,
): LinePoint[] {
  const points: LinePoint[] = [];
  for (let i = period - 1; i < closes.length; i += 1) {
    const window = closes.slice(i - period + 1, i + 1);
    points.push({
      time: dates[i],
      value: window.reduce((sum, value) => sum + value, 0) / period,
    });
  }
  return points;
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

/** Wilder's RSI, matching the API. The first value lands on bar `period`. */
export function rsiSeries(
  dates: string[],
  closes: number[],
  period = 14,
): LinePoint[] {
  const points: LinePoint[] = [];
  if (closes.length <= period) return points;

  const fromAverages = (gain: number, loss: number): number => {
    if (gain === 0 && loss === 0) return 50;
    if (loss === 0) return 100;
    return 100 - 100 / (1 + gain / loss);
  };

  let avgGain = 0;
  let avgLoss = 0;
  for (let i = 1; i <= period; i += 1) {
    const delta = closes[i] - closes[i - 1];
    avgGain += Math.max(delta, 0);
    avgLoss += Math.max(-delta, 0);
  }
  avgGain /= period;
  avgLoss /= period;
  points.push({ time: dates[period], value: fromAverages(avgGain, avgLoss) });

  for (let i = period + 1; i < closes.length; i += 1) {
    const delta = closes[i] - closes[i - 1];
    avgGain = (avgGain * (period - 1) + Math.max(delta, 0)) / period;
    avgLoss = (avgLoss * (period - 1) + Math.max(-delta, 0)) / period;
    points.push({ time: dates[i], value: fromAverages(avgGain, avgLoss) });
  }
  return points;
}

export interface IchimokuLines {
  tenkan: LinePoint[];
  kijun: LinePoint[];
  senkouA: LinePoint[];
  senkouB: LinePoint[];
}

/**
 * Ichimoku lines, matching the API: midpoints of rolling high/low ranges.
 * The two cloud edges (Senkou A and B) are drawn `displacement` bars later
 * than they are calculated, so only the part that lands on existing bars is
 * returned (the extra stretch into the future is not drawn).
 */
export function ichimokuLines(
  dates: string[],
  highs: number[],
  lows: number[],
  tenkanPeriod = 9,
  kijunPeriod = 26,
  senkouBPeriod = 52,
  displacement = 26,
): IchimokuLines {
  const mid = (period: number, i: number): number => {
    const windowHighs = highs.slice(i - period + 1, i + 1);
    const windowLows = lows.slice(i - period + 1, i + 1);
    return (Math.max(...windowHighs) + Math.min(...windowLows)) / 2;
  };

  const tenkan: LinePoint[] = [];
  const kijun: LinePoint[] = [];
  const senkouA: LinePoint[] = [];
  const senkouB: LinePoint[] = [];

  for (let i = 0; i < dates.length; i += 1) {
    const tenkanValue = i >= tenkanPeriod - 1 ? mid(tenkanPeriod, i) : null;
    const kijunValue = i >= kijunPeriod - 1 ? mid(kijunPeriod, i) : null;
    if (tenkanValue !== null) {
      tenkan.push({ time: dates[i], value: tenkanValue });
    }
    if (kijunValue !== null) {
      kijun.push({ time: dates[i], value: kijunValue });
    }
    const shown = i + displacement;
    if (shown >= dates.length) continue;
    if (tenkanValue !== null && kijunValue !== null) {
      senkouA.push({
        time: dates[shown],
        value: (tenkanValue + kijunValue) / 2,
      });
    }
    if (i >= senkouBPeriod - 1) {
      senkouB.push({ time: dates[shown], value: mid(senkouBPeriod, i) });
    }
  }

  return { tenkan, kijun, senkouA, senkouB };
}