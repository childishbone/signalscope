import type { IndicatorKey, SignalKey } from "./types";

export const DISCLAIMER =
  "Technical signals are generated algorithmically for informational purposes and do not constitute investment advice.";

export const INDICATOR_ORDER: IndicatorKey[] = ["dma", "rsi", "ichimoku", "elliott"];

export const SIGNAL_LABELS: Record<SignalKey, string> = {
  dma: "DMA",
  rsi: "RSI",
  ichimoku: "Ichimoku",
  elliott: "Elliott Wave",
  overall: "Overall",
};