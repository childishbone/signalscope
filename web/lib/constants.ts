import type { IndicatorKey, SignalKey } from "./types";

export const INDICATOR_ORDER: IndicatorKey[] = [
  "dma",
  "rsi",
  "ichimoku",
  "elliott",
];

export const SIGNAL_LABELS: Record<SignalKey, string> = {
  dma: "DMA",
  rsi: "RSI",
  ichimoku: "Ichimoku",
  elliott: "Elliott Wave",
  overall: "Overall",
};

export const CANSLIM_LETTER_ORDER = ["C", "A", "N", "S", "L", "M"] as const;

export const CANSLIM_LETTER_LABELS: Record<string, string> = {
  C: "Current Quarterly Earnings",
  A: "Annual Earnings Growth",
  N: "New Highs",
  S: "Supply & Demand",
  L: "Leader (Relative Strength)",
  M: "Market Direction",
};