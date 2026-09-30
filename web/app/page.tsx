"use client";

import { ArrowRight } from "lucide-react";
import { useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { SignalBadge } from "@/components/signal-badge";
import {
  ApiError,
  type ApiSignalEvent,
  type ApiWatchlistItem,
  getRecentSignalEvents,
  getSecuritySignals,
  getWatchlist,
} from "@/lib/api";
import { SIGNAL_LABELS } from "@/lib/constants";
import type { SignalState } from "@/lib/types";

const TONE: Record<SignalState, string> = {
  bullish: "text-signal-bullish",
  neutral: "text-signal-neutral",
  bearish: "text-signal-bearish",
};

type OverallStatus = "loading" | SignalState | "insufficient" | "error";

export default function DashboardPage() {
  const [items, setItems] = useState<ApiWatchlistItem[]>([]);
  const [overallByItemId, setOverallByItemId] = useState<
    Record<number, OverallStatus>
  >({});
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [signalEvents, setSignalEvents] = useState<ApiSignalEvent[]>([]);
  const [signalEventsLoading, setSignalEventsLoading] = useState(true);
  const [signalEventsError, setSignalEventsError] = useState<string | null>(
    null,
  );

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const watchlist = await getWatchlist();
        if (cancelled) return;
        setItems(watchlist);
        setLoading(false);
        setOverallByItemId(
          Object.fromEntries(
            watchlist.map((item) => [item.id, "loading" as OverallStatus]),
          ),
        );

        for (const item of watchlist) {
          try {
            const signals = await getSecuritySignals(item.security.id);
            if (cancelled) return;
            setOverallByItemId((prev) => ({
              ...prev,
              [item.id]: signals.overall.state,
            }));
          } catch (err) {
            if (cancelled) return;
            const insufficient = err instanceof ApiError && err.status === 422;
            setOverallByItemId((prev) => ({
              ...prev,
              [item.id]: insufficient ? "insufficient" : "error",
            }));
          }
        }
      } catch {
        if (!cancelled) {
          setLoading(false);
          setLoadError(
            "Could not load the watchlist. Try refreshing the page.",
          );
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadSignalEvents() {
      try {
        const events = await getRecentSignalEvents(10);
        if (!cancelled) setSignalEvents(events);
      } catch {
        if (!cancelled)
          setSignalEventsError("Could not load recent signal changes.");
      } finally {
        if (!cancelled) setSignalEventsLoading(false);
      }
    }

    void loadSignalEvents();
    return () => {
      cancelled = true;
    };
  }, []);

  const overallStatuses = Object.values(overallByItemId);
  const counts: Record<SignalState, number> = {
    bullish: 0,
    neutral: 0,
    bearish: 0,
  };
  for (const status of overallStatuses) {
    if (status === "bullish" || status === "neutral" || status === "bearish") {
      counts[status] += 1;
    }
  }
  const signalsStillLoading = overallStatuses.some(
    (status) => status === "loading",
  );

  const stats = [
    {
      label: "Watchlist Securities",
      value: items.length,
      tone: "text-foreground",
      pending: loading,
    },
    {
      label: "Bullish Signals",
      value: counts.bullish,
      tone: TONE.bullish,
      pending: loading || signalsStillLoading,
    },
    {
      label: "Neutral Signals",
      value: counts.neutral,
      tone: TONE.neutral,
      pending: loading || signalsStillLoading,
    },
    {
      label: "Bearish Signals",
      value: counts.bearish,
      tone: TONE.bearish,
      pending: loading || signalsStillLoading,
    },
  ];

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Overview of your watchlist and its latest technical signals (Overall)."
        sampleData={false}
      />

      {loadError && (
        <div className="mb-4 rounded-md border border-signal-bearish/30 bg-signal-bearish/10 px-3 py-2 text-sm text-signal-bearish">
          Could not reach the API: {loadError}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map((stat) => (
          <Panel key={stat.label} className="p-4">
            <p className="text-xs text-muted">{stat.label}</p>
            {stat.pending ? (
              <span className="mt-2 inline-block h-8 w-12 animate-pulse rounded bg-panel-hover" />
            ) : (
              <p
                className={`mt-2 font-mono text-3xl font-semibold ${stat.tone}`}
              >
                {stat.value}
              </p>
            )}
          </Panel>
        ))}
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Panel title="Recent Signal Changes">
          {signalEventsLoading ? (
            <p className="px-4 py-6 text-sm text-muted">Loading…</p>
          ) : signalEventsError ? (
            <p className="px-4 py-6 text-sm text-signal-bearish">
              {signalEventsError}
            </p>
          ) : signalEvents.length === 0 ? (
            <p className="px-4 py-6 text-sm text-muted">
              No signal changes recorded yet. Changes appear here once a
              security&apos;s signal differs from what was last recorded --
              click &quot;Refresh data&quot; on the Watchlist page to check for
              updates.
            </p>
          ) : (
            <ul className="divide-y divide-border">
              {signalEvents.map((event) => (
                <li
                  key={event.id}
                  className="flex flex-wrap items-center gap-x-3 gap-y-2 px-4 py-3"
                >
                  <span className="w-14 font-mono text-sm font-medium">
                    {event.security.symbol}
                  </span>
                  <span className="w-24 text-sm text-muted">
                    {SIGNAL_LABELS[
                      event.indicator as keyof typeof SIGNAL_LABELS
                    ] ?? event.indicator}
                  </span>
                  <span className="flex items-center gap-2">
                    <SignalBadge state={event.from_state} />
                    <ArrowRight
                      className="h-3.5 w-3.5 text-muted"
                      aria-hidden
                    />
                    <SignalBadge state={event.to_state} />
                  </span>
                  <span className="ml-auto font-mono text-xs text-muted">
                    {event.as_of_date}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title="Recent Alerts">
          <p className="px-4 py-6 text-sm text-muted">
            No alerts yet — Telegram notifications will appear here once
            they&apos;re wired up in a later phase.
          </p>
        </Panel>
      </div>
    </>
  );
}
