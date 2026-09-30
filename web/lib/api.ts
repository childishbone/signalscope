const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

import type { SignalState } from "./types";

export interface ApiSecurity {
  id: number;
  symbol: string;
  exchange_code: string;
  exchange_name: string;
  country: string;
  currency: string;
  name: string;
  asset_type: string;
  provider_symbol: string;
}

export interface ApiQuote {
  latest_price: string;
  latest_date: string;
  change: string;
  change_pct: string;
  volume: number;
  high_52w: string;
  low_52w: string;
}

export interface ApiWatchlistItem {
  id: number;
  added_at: string;
  security: ApiSecurity;
  quote: ApiQuote | null;
}

export interface ApiSecurityMatch {
  symbol: string;
  provider_symbol: string;
  name: string;
  exchange_code: string;
  exchange_name: string;
  country: string;
  currency: string;
  asset_type: string;
}

export interface ApiIndicatorResult {
  state: SignalState;
  score: number;
  reasons: string[];
  values: Record<string, number>;
}

export interface ApiSecuritySignals {
  security: ApiSecurity;
  bars_used: number;
  dma: ApiIndicatorResult;
  rsi: ApiIndicatorResult;
  ichimoku: ApiIndicatorResult;
  elliott: ApiIndicatorResult;
  overall: ApiIndicatorResult;
}

export interface ApiSignalEvent {
  id: number;
  security: ApiSecurity;
  indicator: string;
  from_state: SignalState;
  to_state: SignalState;
  as_of_date: string;
  created_at: string;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(body?.detail ?? response.statusText, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function getWatchlist(): Promise<ApiWatchlistItem[]> {
  return request<ApiWatchlistItem[]>("/api/watchlist");
}

export function searchSecurities(query: string): Promise<ApiSecurityMatch[]> {
  const params = new URLSearchParams({ q: query });
  return request<ApiSecurityMatch[]>(`/api/securities/search?${params}`);
}

export function addToWatchlist(
  providerSymbol: string,
  adminKey: string,
): Promise<ApiWatchlistItem> {
  return request<ApiWatchlistItem>("/api/watchlist", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Admin-Key": adminKey },
    body: JSON.stringify({ provider_symbol: providerSymbol }),
  });
}

export function removeFromWatchlist(
  itemId: number,
  adminKey: string,
): Promise<void> {
  return request<void>(`/api/watchlist/${itemId}`, {
    method: "DELETE",
    headers: { "X-Admin-Key": adminKey },
  });
}

export function refreshWatchlistItem(
  itemId: number,
  adminKey: string,
): Promise<{ bars_written: number; signal_changes: number }> {
  return request<{ bars_written: number; signal_changes: number }>(
    `/api/watchlist/${itemId}/refresh`,
    {
      method: "POST",
      headers: { "X-Admin-Key": adminKey },
    },
  );
}

export function getSecuritySignals(
  securityId: number,
): Promise<ApiSecuritySignals> {
  return request<ApiSecuritySignals>(`/api/securities/${securityId}/signals`);
}

export function getRecentSignalEvents(limit = 20): Promise<ApiSignalEvent[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  return request<ApiSignalEvent[]>(`/api/signal-events?${params}`);
}
