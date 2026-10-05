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
