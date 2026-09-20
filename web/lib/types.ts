export type SignalState = "bullish" | "neutral" | "bearish";
export type IndicatorKey = "dma" | "rsi" | "ichimoku" | "elliott";
export type SignalKey = IndicatorKey | "overall";

export interface Security {
  ticker: string;
  name: string;
  exchange: string;
  country: string;
  currency: string;
}

export interface SecurityQuote extends Security {
  price: number;
  change: number;
  changePct: number;
  volume: number;
  high52w: number;
  low52w: number;
}

export interface SignalRow {
  ticker: string;
  signals: Record<IndicatorKey, SignalState>;
  overall: SignalState;
}

export interface SignalChange {
  id: string;
  ticker: string;
  indicator: SignalKey;
  from: SignalState;
  to: SignalState;
  date: string;
}

export interface AlertItem {
  id: string;
  ticker: string;
  text: string;
  sentAt: string;
}