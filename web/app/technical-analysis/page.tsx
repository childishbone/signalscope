"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { SignalBadge, SignalLegend } from "@/components/signal-badge";
import { SignalDetailPanel } from "@/components/signal-detail-panel";
import { INDICATOR_ORDER, SIGNAL_LABELS } from "@/lib/constants";
import {
  ApiError,
  ApiIndicatorResult,
  ApiSecurity,
  getSecuritySignals,
  getWatchlist,
} from "@/lib/api";

type CoreIndicatorKey = "dma" | "rsi" | "ichimoku" | "elliott";
type IndicatorKey = CoreIndicatorKey | "overall";
type RowStatus = "loading" | "ready" | "insufficient" | "error";

interface Row {
  security: ApiSecurity;
  status: RowStatus;
  dma?: ApiIndicatorResult;
  rsi?: ApiIndicatorResult;
  ichimoku?: ApiIndicatorResult;
  elliott?: ApiIndicatorResult;
  overall?: ApiIndicatorResult;
}

export default function TechnicalAnalysisPage() {
  const [rows, setRows] = useState<Row[]>([]);
  const [listError, setListError] = useState<string | null>(null);
  const [selected, setSelected] = useState<{
    row: Row;
    key: IndicatorKey;
  } | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const items = await getWatchlist();
        if (cancelled) return;

        setRows(
          items.map((item) => ({ security: item.security, status: "loading" })),
        );

        for (const item of items) {
          try {
            const signals = await getSecuritySignals(item.security.id);
            if (cancelled) return;
            setRows((prev) =>
              prev.map((row) =>
                row.security.id === item.security.id
                  ? {
                      security: row.security,
                      status: "ready",
                      dma: signals.dma,
                      rsi: signals.rsi,
                      ichimoku: signals.ichimoku,
                      elliott: signals.elliott,
                      overall: signals.overall,
                    }
                  : row,
              ),
            );
          } catch (err) {
            if (cancelled) return;
            const insufficient = err instanceof ApiError && err.status === 422;
            setRows((prev) =>
              prev.map((row) =>
                row.security.id === item.security.id
                  ? {
                      security: row.security,
                      status: insufficient ? "insufficient" : "error",
                    }
                  : row,
              ),
            );
          }
        }
      } catch {
        if (!cancelled) {
          setListError(
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

  function renderCell(row: Row, key: IndicatorKey) {
    if (row.status === "loading") {
      return (
        <span className="inline-block h-7 w-10 animate-pulse rounded-full bg-panel-hover" />
      );
    }
    if (row.status === "insufficient") {
      return (
        <span
          title="Not enough price history yet to compute signals"
          className="text-xs text-muted"
        >
          —
        </span>
      );
    }
    if (row.status === "error") {
      return (
        <span
          title="Could not load this signal"
          className="text-xs text-signal-bearish"
        >
          !
        </span>
      );
    }
    const result = row[key];
    if (!result) return null;
    return (
      <button
        onClick={() => setSelected({ row, key })}
        className="cursor-pointer"
      >
        <SignalBadge state={result.state} compact />
      </button>
    );
  }

  return (
    <>
      <PageHeader
        title="Technical Analysis"
        description="Rule-based signals per indicator. These are outputs of defined rules, not recommendations."
        sampleData={false}
      />

      <div className="mb-4">
        <SignalLegend />
      </div>

      {listError && (
        <p className="mb-4 text-sm text-signal-bearish">{listError}</p>
      )}

      <Panel>
        {rows.length === 0 && !listError ? (
          <p className="px-4 py-6 text-sm text-muted">
            Your watchlist is empty. Add securities from the Watchlist page to
            see signals here.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted">
                  <th className="px-4 py-3 font-medium">Ticker</th>
                  {INDICATOR_ORDER.map((key: CoreIndicatorKey) => (
                    <th key={key} className="px-4 py-3 text-center font-medium">
                      {SIGNAL_LABELS[key]}
                    </th>
                  ))}
                  <th className="px-4 py-3 text-center font-medium">
                    {SIGNAL_LABELS.overall}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {rows.map((row) => (
                  <tr key={row.security.id} className="hover:bg-panel-hover">
                    <td className="px-4 py-3">
                      <span className="font-mono font-medium">
                        {row.security.symbol}
                      </span>
                      <span className="block text-xs text-muted">
                        {row.security.name}
                      </span>
                    </td>
                    {INDICATOR_ORDER.map((key: CoreIndicatorKey) => (
                      <td key={key} className="px-4 py-3 text-center">
                        {renderCell(row, key)}
                      </td>
                    ))}
                    <td className="px-4 py-3 text-center">
                      {renderCell(row, "overall")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      {selected?.row[selected.key] && (
        <SignalDetailPanel
          tickerLabel={`${selected.row.security.symbol} — ${selected.row.security.name}`}
          indicatorLabel={SIGNAL_LABELS[selected.key]}
          result={selected.row[selected.key]!}
          onClose={() => setSelected(null)}
        />
      )}
    </>
  );
}
