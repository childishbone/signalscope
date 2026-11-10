"use client";

import { ArrowDown, ArrowUp } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { SignalBadge, SignalLegend } from "@/components/signal-badge";
import { SignalDetailPanel } from "@/components/signal-detail-panel";
import { INDICATOR_ORDER, SIGNAL_LABELS } from "@/lib/constants";
import { INDICATOR_INFO } from "@/lib/indicator-info";
import {
  ApiError,
  ApiIndicatorResult,
  ApiSecurity,
  getSecuritySignals,
  getWatchlist,
} from "@/lib/api";
import type { SignalState } from "@/lib/types";

type IndicatorKey =
  | "dma"
  | "rsi"
  | "ichimoku"
  | "bollinger"
  | "overall"
  | "high52";
type RowStatus = "loading" | "ready" | "insufficient" | "error";
type SortDirection = "best" | "worst";
type StateFilter = "all" | SignalState;

interface Row {
  security: ApiSecurity;
  status: RowStatus;
  dma?: ApiIndicatorResult;
  rsi?: ApiIndicatorResult;
  ichimoku?: ApiIndicatorResult;
  bollinger?: ApiIndicatorResult;
  overall?: ApiIndicatorResult;
  high52?: ApiIndicatorResult;
}

// Column order: the three trend/momentum indicators, their combined
// Overall Trend, then the two separate readings (dip-buy and risk).
const COLUMNS: IndicatorKey[] = [...INDICATOR_ORDER, "overall", "bollinger", "high52"];

const STATE_RANK: Record<SignalState, number> = {
  bullish: 2,
  neutral: 1,
  bearish: 0,
};

const FILTER_OPTIONS: StateFilter[] = ["all", "bullish", "neutral", "bearish"];

export default function TechnicalAnalysisPage() {
  const [rows, setRows] = useState<Row[]>([]);
  const [listError, setListError] = useState<string | null>(null);
  const [selected, setSelected] = useState<{
    row: Row;
    key: IndicatorKey;
  } | null>(null);
  const [sort, setSort] = useState<{
    key: IndicatorKey;
    direction: SortDirection;
  } | null>(null);
  const [filter, setFilter] = useState<StateFilter>("all");

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
                      bollinger: signals.bollinger,
                      overall: signals.overall,
                      high52: signals.high52 ?? undefined,
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

  const visibleRows = useMemo(() => {
    let result = rows;
    if (filter !== "all") {
      result = result.filter((row) => row.overall?.state === filter);
    }
    if (sort) {
      const { key, direction } = sort;
      const rankOf = (row: Row): number | null => {
        const indicator = row[key];
        return indicator ? STATE_RANK[indicator.state] : null;
      };
      result = [...result].sort((a, b) => {
        const rankA = rankOf(a);
        const rankB = rankOf(b);
        if (rankA === null && rankB === null) return 0;
        if (rankA === null) return 1;
        if (rankB === null) return -1;
        return direction === "best" ? rankB - rankA : rankA - rankB;
      });
    }
    return result;
  }, [rows, sort, filter]);

  function toggleSort(key: IndicatorKey) {
    setSort((current) => {
      if (!current || current.key !== key) return { key, direction: "best" };
      if (current.direction === "best") return { key, direction: "worst" };
      return null;
    });
  }

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
          {"\u2014"}
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
    if (!result) {
      return (
        <span
          title="Needs a full year of price history"
          className="text-xs text-muted"
        >
          {"\u2014"}
        </span>
      );
    }
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
        <p className="mt-2 text-xs text-muted">
          Click any badge for details, or a column heading to sort. Bollinger
          Bands is a contrarian signal: Bullish means price is stretched toward
          its lower band (a possible bounce), so it can disagree with the trend
          indicators. 52-Week High is a risk gauge, not a buy or sell signal:
          stocks near their yearly high have historically had smaller dips than
          stocks far below it.
        </p>
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-2 text-xs">
        <span className="text-muted">{SIGNAL_LABELS.overall}:</span>
        {FILTER_OPTIONS.map((option) => (
          <button
            key={option}
            onClick={() => setFilter(option)}
            className={`rounded-full border border-border px-3 py-1 capitalize ${
              filter === option
                ? "bg-panel-hover text-foreground"
                : "text-muted hover:text-foreground"
            }`}
          >
            {option}
          </button>
        ))}
        {(sort || filter !== "all") && (
          <button
            onClick={() => {
              setSort(null);
              setFilter("all");
            }}
            className="text-muted underline hover:text-foreground"
          >
            Reset
          </button>
        )}
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
                  {COLUMNS.map((key) => (
                    <th key={key} className="px-4 py-3 text-center font-medium">
                      <button
                        onClick={() => toggleSort(key)}
                        title={
                          sort?.key === key
                            ? sort.direction === "best"
                              ? "Sorted Bullish first. Click for Bearish first."
                              : "Sorted Bearish first. Click to clear."
                            : "Click to sort Bullish first"
                        }
                        className="inline-flex items-center gap-1 hover:text-foreground"
                      >
                        {SIGNAL_LABELS[key]}
                        {sort?.key === key &&
                          (sort.direction === "best" ? (
                            <ArrowUp className="h-3 w-3" aria-hidden />
                          ) : (
                            <ArrowDown className="h-3 w-3" aria-hidden />
                          ))}
                      </button>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {visibleRows.map((row) => (
                  <tr key={row.security.id} className="hover:bg-panel-hover">
                    <td className="px-4 py-3">
                      <span className="font-mono font-medium">
                        {row.security.symbol}
                      </span>
                      <span className="block text-xs text-muted">
                        {row.security.name}
                      </span>
                    </td>
                    {COLUMNS.map((key) => (
                      <td key={key} className="px-4 py-3 text-center">
                        {renderCell(row, key)}
                      </td>
                    ))}
                  </tr>
                ))}
                {visibleRows.length === 0 && (
                  <tr>
                    <td
                      colSpan={COLUMNS.length + 1}
                      className="px-4 py-6 text-sm text-muted"
                    >
                      No securities match this filter.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      {selected?.row[selected.key] && (
        <SignalDetailPanel
          tickerLabel={`${selected.row.security.symbol} \u2014 ${selected.row.security.name}`}
          indicatorLabel={SIGNAL_LABELS[selected.key]}
          info={INDICATOR_INFO[selected.key]}
          result={selected.row[selected.key]!}
          onClose={() => setSelected(null)}
        />
      )}
    </>
  );
}