"use client";

import {
  AlertCircle,
  Loader2,
  RefreshCw,
  Search,
  Trash2,
  X,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { PriceChart } from "@/components/price-chart";
import {
  addToWatchlist,
  ApiError,
  type ApiBar,
  type ApiSecurityMatch,
  type ApiWatchlistItem,
  getSecurityBars,
  getWatchlist,
  refreshWatchlistItem,
  removeFromWatchlist,
  searchSecurities,
} from "@/lib/api";
import {
  formatChange,
  formatPercent,
  formatPrice,
  formatVolume,
} from "@/lib/format";
import { useAdminKey } from "@/lib/use-admin-key";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="mt-1 font-mono text-sm">{value}</dd>
    </div>
  );
}

export default function WatchlistPage() {
  const { ensureAdminKey } = useAdminKey();

  const [watchlist, setWatchlist] = useState<ApiWatchlistItem[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ApiSecurityMatch[]>([]);
  const [searching, setSearching] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const [selectedId, setSelectedId] = useState<number | null>(null);

  const [bars, setBars] = useState<ApiBar[]>([]);
  const [barsLoading, setBarsLoading] = useState(false);
  const [barsError, setBarsError] = useState<string | null>(null);

  const refreshWatchlist = useCallback(async () => {
    try {
      const items = await getWatchlist();
      setWatchlist(items);
      setLoadError(null);
      setSelectedId(
        (current) => current ?? (items.length > 0 ? items[0].id : null),
      );
    } catch (err) {
      setLoadError(
        err instanceof Error ? err.message : "Failed to load watchlist",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Fetching data on mount is a standard, endorsed use of useEffect; the
    // eventual setState calls inside refreshWatchlist aren't "synchronous
    // within the effect body" in the way this rule is meant to catch.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshWatchlist();
  }, [refreshWatchlist]);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      const timeout = setTimeout(() => setResults([]), 0);
      return () => clearTimeout(timeout);
    }

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSearching(true);
    const timeout = setTimeout(async () => {
      try {
        const matches = await searchSecurities(trimmed);
        setResults(matches);
      } catch {
        setResults([]);
      } finally {
        setSearching(false);
      }
    }, 350); // debounce: wait for a pause in typing before calling the API

    return () => clearTimeout(timeout);
  }, [query]);

  useEffect(() => {
    if (selectedId === null) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setBars([]);
      setBarsError(null);
      return;
    }

    let cancelled = false;
    setBarsLoading(true);
    setBarsError(null);

    getSecurityBars(selectedId)
      .then((data) => {
        if (cancelled) return;
        setBars(data);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setBars([]);
        setBarsError(
          err instanceof Error ? err.message : "Failed to load price history",
        );
      })
      .finally(() => {
        if (cancelled) return;
        setBarsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  async function handleAdd(match: ApiSecurityMatch) {
    const key = ensureAdminKey();
    if (!key) return;
    setActionError(null);
    try {
      const item = await addToWatchlist(match.provider_symbol, key);
      setQuery("");
      setResults([]);
      await refreshWatchlist();
      setSelectedId(item.id);
    } catch (err) {
      setActionError(
        err instanceof ApiError ? err.message : "Failed to add security",
      );
    }
  }

  async function handleRemove(itemId: number) {
    const key = ensureAdminKey();
    if (!key) return;
    setActionError(null);
    try {
      await removeFromWatchlist(itemId, key);
      if (selectedId === itemId) setSelectedId(null);
      await refreshWatchlist();
    } catch (err) {
      setActionError(
        err instanceof ApiError ? err.message : "Failed to remove security",
      );
    }
  }

  async function handleRefreshData(itemId: number) {
    const key = ensureAdminKey();
    if (!key) return;
    setActionError(null);
    setRefreshing(true);
    try {
      await refreshWatchlistItem(itemId, key);
      await refreshWatchlist();
      if (itemId === selectedId) {
        const data = await getSecurityBars(itemId);
        setBars(data);
      }
    } catch (err) {
      setActionError(
        err instanceof ApiError ? err.message : "Failed to refresh data",
      );
    } finally {
      setRefreshing(false);
    }
  }

  const selectedItem = watchlist.find((w) => w.id === selectedId);
  const selected = selectedItem?.security;
  const quote = selectedItem?.quote;

  return (
    <>
      <PageHeader
        title="Watchlist"
        description="Search for securities and manage your list."
        sampleData={false}
      />

      {loadError && (
        <div className="mb-4 flex items-center gap-2 rounded-md border border-signal-bearish/30 bg-signal-bearish/10 px-3 py-2 text-sm text-signal-bearish">
          <AlertCircle className="h-4 w-4 shrink-0" aria-hidden />
          Could not reach the API: {loadError}
        </div>
      )}
      {actionError && (
        <div className="mb-4 flex items-center justify-between gap-2 rounded-md border border-signal-bearish/30 bg-signal-bearish/10 px-3 py-2 text-sm text-signal-bearish">
          <span className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" aria-hidden />
            {actionError}
          </span>
          <button onClick={() => setActionError(null)} aria-label="Dismiss">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
        <Panel>
          <div className="relative border-b border-border p-3">
            <label className="relative block">
              <span className="sr-only">Search securities</span>
              <Search
                className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
                aria-hidden
              />
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search by name or ticker (e.g. Toyota, AAPL)"
                className="w-full rounded-md border border-border bg-background py-2 pl-9 pr-9 text-sm placeholder:text-muted"
              />
              {searching && (
                <Loader2
                  className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-muted"
                  aria-hidden
                />
              )}
            </label>

            {results.length > 0 && (
              <ul className="absolute inset-x-3 top-full z-10 mt-1 max-h-72 overflow-y-auto rounded-md border border-border bg-panel shadow-lg">
                {results.map((match) => (
                  <li key={match.provider_symbol}>
                    <button
                      type="button"
                      onClick={() => handleAdd(match)}
                      className="block w-full px-3 py-2 text-left text-sm hover:bg-panel-hover"
                    >
                      <span className="font-mono font-medium">
                        {match.symbol}
                      </span>
                      <span className="text-muted"> — {match.name}</span>
                      <span className="block text-xs text-muted">
                        {match.exchange_name} — {match.country}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {loading ? (
            <p className="p-8 text-center text-sm text-muted">
              Loading watchlist…
            </p>
          ) : watchlist.length === 0 ? (
            <p className="p-8 text-center text-sm text-muted">
              Your watchlist is empty. Search above to add a security.
            </p>
          ) : (
            <ul>
              {watchlist.map((item) => (
                <li
                  key={item.id}
                  className="flex items-center border-b border-border last:border-b-0"
                >
                  <button
                    type="button"
                    onClick={() => setSelectedId(item.id)}
                    aria-pressed={selectedId === item.id}
                    className={`flex-1 px-4 py-3 text-left transition-colors ${
                      selectedId === item.id
                        ? "bg-panel-hover"
                        : "hover:bg-panel-hover"
                    }`}
                  >
                    <span className="font-mono text-sm font-medium">
                      {item.security.symbol}
                    </span>
                    <span className="text-sm text-muted">
                      {" "}
                      — {item.security.name}
                    </span>
                    <span className="block text-xs text-muted">
                      {item.security.exchange_name} — {item.security.country}
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleRemove(item.id)}
                    aria-label={`Remove ${item.security.symbol}`}
                    className="px-3 py-3 text-muted hover:text-signal-bearish"
                  >
                    <Trash2 className="h-4 w-4" aria-hidden />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel>
          {selected ? (
            <div className="p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h2 className="text-lg font-semibold">{selected.name}</h2>
                  <p className="text-sm text-muted">
                    <span className="font-mono">{selected.symbol}</span> ·{" "}
                    {selected.exchange_name} · {selected.country}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    selectedItem && handleRefreshData(selectedItem.id)
                  }
                  disabled={refreshing}
                  className="flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1.5 text-xs text-muted hover:bg-panel-hover disabled:opacity-50"
                >
                  <RefreshCw
                    className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`}
                    aria-hidden
                  />
                  {refreshing ? "Refreshing…" : "Refresh data"}
                </button>
              </div>

              {quote ? (
                <>
                  <div className="mt-4 flex items-baseline gap-3">
                    <p className="font-mono text-2xl font-semibold">
                      {formatPrice(
                        Number(quote.latest_price),
                        selected.currency,
                      )}
                    </p>
                    <p
                      className={`font-mono text-sm ${
                        Number(quote.change) >= 0
                          ? "text-signal-bullish"
                          : "text-signal-bearish"
                      }`}
                    >
                      {formatChange(Number(quote.change))} (
                      {formatPercent(Number(quote.change_pct))})
                    </p>
                  </div>
                  <p className="text-xs text-muted">
                    As of {quote.latest_date}
                  </p>

                  <dl className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3">
                    <Stat label="Volume" value={formatVolume(quote.volume)} />
                    <Stat
                      label="52-week high"
                      value={formatPrice(
                        Number(quote.high_52w),
                        selected.currency,
                      )}
                    />
                    <Stat
                      label="52-week low"
                      value={formatPrice(
                        Number(quote.low_52w),
                        selected.currency,
                      )}
                    />
                  </dl>
                </>
              ) : (
                <div className="mt-6 rounded-md border border-dashed border-border p-4 text-sm text-muted">
                  No price data yet. Click &quot;Refresh data&quot; to fetch it.
                </div>
              )}

              <div className="mt-4">
                {barsLoading ? (
                  <div className="flex h-56 items-center justify-center rounded-md border border-dashed border-border text-sm text-muted">
                    <Loader2
                      className="mr-2 h-4 w-4 animate-spin"
                      aria-hidden
                    />
                    Loading chart…
                  </div>
                ) : barsError ? (
                  <div className="flex h-56 items-center justify-center rounded-md border border-dashed border-border text-sm text-signal-bearish">
                    {barsError}
                  </div>
                ) : bars.length === 0 ? (
                  <div className="flex h-56 items-center justify-center rounded-md border border-dashed border-border text-sm text-muted">
                    No price history yet. Click &quot;Refresh data&quot; to
                    fetch it.
                  </div>
                ) : (
                  <div className="rounded-md border border-border p-2">
                    <PriceChart bars={bars} />
                  </div>
                )}
              </div>
            </div>
          ) : (
            <p className="p-8 text-center text-sm text-muted">
              Select a security to see its details.
            </p>
          )}
        </Panel>
      </div>
    </>
  );
}
