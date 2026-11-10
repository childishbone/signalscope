import type { SignalKey } from "./types";

export interface IndicatorInfo {
  role: string;
  meaning: string;
  history: string;
}

export const BACKTEST_NOTE =
  "From a 5-year backtest (Nov 2021 to Nov 2026) of 23 stocks and ETFs, in a mostly rising market. It describes past behaviour and is not a forecast.";

export const INDICATOR_INFO: Record<SignalKey, IndicatorInfo> = {
  dma: {
    role: "Trend",
    meaning:
      "Is price above or below its moving averages, and are those averages rising? Bullish means an uptrend is in place.",
    history:
      "Bullish days had a smaller typical worst dip over the next 20 days (about -3.8%) than bearish days (about -4.5%), and fewer drops of 10% or more (10% of days vs 13%). It showed no reliable edge in predicting whether price goes up or down.",
  },
  rsi: {
    role: "Momentum",
    meaning:
      "How strong recent price moves have been, with a warning when a move looks stretched. Bullish means momentum is up without being overheated.",
    history:
      "No dependable edge. Bullish days returned less than the average day over 60 days, and their worst dips were no smaller than normal. Treat it as context only.",
  },
  ichimoku: {
    role: "Trend",
    meaning:
      "Where price sits relative to the Ichimoku cloud and its lines. Bullish means price is above the cloud with the lines aligned upward.",
    history:
      "Bullish days had a typical worst 20-day dip of about -4.1% vs -4.7% for bearish days, with 10%+ drops on 11.5% of bullish days vs 14.9% of bearish days. It showed no reliable edge in predicting direction.",
  },
  bollinger: {
    role: "Dip-buy",
    meaning:
      "Where price sits inside its recent volatility bands. Bullish means price is stretched toward the lower band (a possible bounce); Bearish means it is stretched toward the upper band. It is a contrarian reading, so it can disagree with the trend indicators.",
    history:
      "The only indicator whose bullish days beat its bearish days both before and after 2024. Bullish days averaged about +2.6% over the next 20 days vs +2.0% for an average day. The edge is small and shrank in the later period, and its bearish reading did not predict drops.",
  },
  overall: {
    role: "Trend",
    meaning:
      "A combined vote of DMA, RSI and Ichimoku. Bullish means most of them agree the trend is up. Bollinger Bands is shown separately because it reads the opposite way (dip-buy).",
    history:
      "The combined score has not been backtested on its own, and the individual indicators show no reliable edge in predicting direction, so read it as a summary and not a forecast.",
  },
};