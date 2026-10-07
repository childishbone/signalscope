"use client";

import { useEffect, useState } from "react";

import { CanslimBadge, CanslimLegend } from "@/components/canslim-badge";
import { CanslimDetailPanel } from "@/components/canslim-detail-panel";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import {
  type ApiCanslimLetterResult,
  type ApiSecurityCanslim,
  getCanslimWatchlist,
} from "@/lib/api";
import { CANSLIM_LETTER_LABELS, CANSLIM_LETTER_ORDER } from "@/lib/constants";

export default function CanslimPage() {
  const [rows, setRows] = useState<ApiSecurityCanslim[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selected, setSelected] = useState<{
    row: ApiSecurityCanslim;
    letter: string;
  } | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await getCanslimWatchlist();
        if (cancelled) return;
        setRows(data);
        setLoadError(null);
      } catch (err) {
        if (cancelled) return;
        setLoadError(
          err instanceof Error ? err.message : "Could not load CANSLIM data",
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedResult: ApiCanslimLetterResult | undefined = selected
    ? selected.row.letters[selected.letter]
    : undefined;

  return (
    <>
      <PageHeader
        title="CANSLIM"
        description="William O'Neil's CANSLIM checklist, scored per security. Each letter is Pass, Fail, or Insufficient Data — insufficient-data letters are excluded from the score rather than counted against it."
        sampleData={false}
      />

      <div className="mb-4">
        <CanslimLegend />
      </div>

      {loadError && (
        <p className="mb-4 text-sm text-signal-bearish">
          Could not load CANSLIM data: {loadError}
        </p>
      )}

      <Panel>
        {loading ? (
          <p className="px-4 py-6 text-sm text-muted">
            Loading CANSLIM checklist…
          </p>
        ) : rows.length === 0 && !loadError ? (
          <p className="px-4 py-6 text-sm text-muted">
            Your watchlist is empty. Add securities from the Watchlist page to
            see CANSLIM scores here.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted">
                  <th className="px-4 py-3 font-medium">Ticker</th>
                  {CANSLIM_LETTER_ORDER.map((letter) => (
                    <th
                      key={letter}
                      className="px-4 py-3 text-center font-medium"
                      title={CANSLIM_LETTER_LABELS[letter]}
                    >
                      {letter}
                    </th>
                  ))}
                  <th className="px-4 py-3 text-center font-medium">Score</th>
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
                    {CANSLIM_LETTER_ORDER.map((letter) => {
                      const result = row.letters[letter];
                      if (!result) {
                        return (
                          <td key={letter} className="px-4 py-3 text-center" />
                        );
                      }
                      return (
                        <td key={letter} className="px-4 py-3 text-center">
                          <button
                            onClick={() => setSelected({ row, letter })}
                            className="cursor-pointer"
                          >
                            <CanslimBadge verdict={result.verdict} compact />
                          </button>
                        </td>
                      );
                    })}
                    <td className="px-4 py-3 text-center">
                      {row.score_pct === null ? (
                        <span
                          title="No letters could be evaluated for this security"
                          className="text-xs text-muted"
                        >
                          —
                        </span>
                      ) : (
                        <div>
                          <span className="font-mono font-medium">
                            {row.score_pct.toFixed(0)}%
                          </span>
                          <span className="block text-xs text-muted">
                            {row.criteria_evaluated}/{row.criteria_total} evaluated
                          </span>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      {selected && selectedResult && (
        <CanslimDetailPanel
          tickerLabel={`${selected.row.security.symbol} — ${selected.row.security.name}`}
          letter={selected.letter}
          result={selectedResult}
          onClose={() => setSelected(null)}
        />
      )}
    </>
  );
}