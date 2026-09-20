"use client";

import { Search } from "lucide-react";
import { useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { formatChange, formatPercent, formatPrice, formatVolume } from "@/lib/format";
import { SECURITIES } from "@/lib/mock-data";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="mt-1 font-mono text-sm">{value}</dd>
    </div>
  );
}

export default function WatchlistPage() {
  const [selected, setSelected] = useState<string | null>(SECURITIES[0]?.ticker ?? null);
  const security = SECURITIES.find((s) => s.ticker === selected);

  return (
    <>
      <PageHeader title="Watchlist" description="Search for securities and inspect them here." />

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
        <Panel>
          <div className="border-b border-border p-3">
            <label className="relative block">
              <span className="sr-only">Search securities</span>
              <Search
                className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
                aria-hidden
              />
              <input
                type="search"
                disabled
                placeholder="Search coming in a later phase"
                className="w-full rounded-md border border-border bg-background py-2 pl-9 pr-3 text-sm placeholder:text-muted disabled:cursor-not-allowed disabled:opacity-60"
              />
            </label>
          </div>

          <ul>
            {SECURITIES.map((s) => (
              <li key={s.ticker} className="border-b border-border last:border-b-0">
                <button
                  type="button"
                  onClick={() => setSelected(s.ticker)}
                  aria-pressed={selected === s.ticker}
                  className={`w-full px-4 py-3 text-left transition-colors ${
                    selected === s.ticker ? "bg-panel-hover" : "hover:bg-panel-hover"
                  }`}
                >
                  <span className="font-mono text-sm font-medium">{s.ticker}</span>
                  <span className="text-sm text-muted"> — {s.name}</span>
                  <span className="block text-xs text-muted">
                    {s.exchange} — {s.country}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel>
          {security ? (
            <div className="p-4">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <div>
                  <h2 className="text-lg font-semibold">{security.name}</h2>
                  <p className="text-sm text-muted">
                    <span className="font-mono">{security.ticker}</span> · {security.exchange} ·{" "}
                    {security.country}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-mono text-2xl font-semibold">
                    {formatPrice(security.price, security.currency)}
                  </p>
                  <p
                    className={`font-mono text-sm ${
                      security.change >= 0 ? "text-signal-bullish" : "text-signal-bearish"
                    }`}
                  >
                    {formatChange(security.change)} ({formatPercent(security.changePct)})
                  </p>
                </div>
              </div>

              <dl className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3">
                <Stat label="Volume" value={formatVolume(security.volume)} />
                <Stat label="52-week high" value={formatPrice(security.high52w, security.currency)} />
                <Stat label="52-week low" value={formatPrice(security.low52w, security.currency)} />
              </dl>

              <div className="mt-6 flex h-56 items-center justify-center rounded-md border border-dashed border-border text-sm text-muted">
                Price chart arrives in a later phase
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