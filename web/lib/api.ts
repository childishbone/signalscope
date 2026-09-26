const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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

export interface ApiWatchlistItem {
  id: number;
  added_at: string;
  security: ApiSecurity;
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
