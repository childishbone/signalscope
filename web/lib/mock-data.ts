import type { AlertItem, SecurityQuote, SignalChange, SignalRow } from "./types";

export const SECURITIES: SecurityQuote[] = [
  {
    ticker: "AAPL", name: "Apple Inc.", exchange: "NASDAQ", country: "United States",
    currency: "USD", price: 247.18, change: 1.32, changePct: 0.54,
    volume: 48_200_000, high52w: 260.1, low52w: 169.2,
  },
  {
    ticker: "NVDA", name: "NVIDIA Corporation", exchange: "NASDAQ", country: "United States",
    currency: "USD", price: 131.4, change: -2.1, changePct: -1.57,
    volume: 210_000_000, high52w: 152.9, low52w: 86.6,
  },
  {
    ticker: "TSLA", name: "Tesla, Inc.", exchange: "NASDAQ", country: "United States",
    currency: "USD", price: 219.6, change: -6.4, changePct: -2.83,
    volume: 95_000_000, high52w: 299.3, low52w: 138.8,
  },
  {
    ticker: "7203", name: "Toyota Motor Corporation", exchange: "Tokyo Stock Exchange",
    country: "Japan", currency: "JPY", price: 2890, change: 24, changePct: 0.84,
    volume: 18_500_000, high52w: 3120, low52w: 2210,
  },
  {
    ticker: "0700", name: "Tencent Holdings Ltd.", exchange: "Hong Kong Stock Exchange",
    country: "Hong Kong", currency: "HKD", price: 412.6, change: 5.2, changePct: 1.28,
    volume: 21_000_000, high52w: 468, low52w: 289.4,
  },
  {
    ticker: "D05", name: "DBS Group Holdings Ltd", exchange: "Singapore Exchange",
    country: "Singapore", currency: "SGD", price: 41.85, change: 0.2, changePct: 0.48,
    volume: 4_100_000, high52w: 43.2, low52w: 32.9,
  },
];

export const SIGNAL_ROWS: SignalRow[] = [
  { ticker: "AAPL", signals: { dma: "bullish", rsi: "bullish", ichimoku: "neutral", elliott: "bullish" }, overall: "bullish" },
  { ticker: "NVDA", signals: { dma: "bullish", rsi: "bearish", ichimoku: "bullish", elliott: "neutral" }, overall: "neutral" },
  { ticker: "TSLA", signals: { dma: "bearish", rsi: "neutral", ichimoku: "bearish", elliott: "bearish" }, overall: "bearish" },
  { ticker: "7203", signals: { dma: "neutral", rsi: "neutral", ichimoku: "bullish", elliott: "neutral" }, overall: "neutral" },
  { ticker: "0700", signals: { dma: "bullish", rsi: "bullish", ichimoku: "bullish", elliott: "neutral" }, overall: "bullish" },
  { ticker: "D05", signals: { dma: "neutral", rsi: "bullish", ichimoku: "neutral", elliott: "bearish" }, overall: "neutral" },
];

export const SIGNAL_CHANGES: SignalChange[] = [
  { id: "c1", ticker: "AAPL", indicator: "rsi", from: "neutral", to: "bullish", date: "2026-09-18" },
  { id: "c2", ticker: "NVDA", indicator: "dma", from: "bullish", to: "neutral", date: "2026-09-17" },
  { id: "c3", ticker: "TSLA", indicator: "overall", from: "neutral", to: "bearish", date: "2026-09-17" },
  { id: "c4", ticker: "0700", indicator: "ichimoku", from: "neutral", to: "bullish", date: "2026-09-16" },
];

export const ALERTS: AlertItem[] = [
  { id: "a1", ticker: "AAPL", text: "RSI: Neutral → Bullish", sentAt: "2026-09-18 22:10" },
  { id: "a2", ticker: "TSLA", text: "Overall: Neutral → Bearish", sentAt: "2026-09-17 22:12" },
  { id: "a3", ticker: "NVDA", text: "DMA: Bullish → Neutral", sentAt: "2026-09-17 22:12" },
];