"use client";

import { X } from "lucide-react";

import { CanslimBadge } from "@/components/canslim-badge";
import type { ApiCanslimLetterResult } from "@/lib/api";
import { CANSLIM_LETTER_LABELS } from "@/lib/constants";

interface CanslimDetailPanelProps {
  tickerLabel: string;
  letter: string;
  result: ApiCanslimLetterResult;
  onClose: () => void;
}

export function CanslimDetailPanel({
  tickerLabel,
  letter,
  result,
  onClose,
}: CanslimDetailPanelProps) {
  const isFundAggregate = result.constituents !== null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
    >
      <div
        className="max-h-[80vh] w-full max-w-lg overflow-y-auto rounded-xl border border-border bg-panel p-6 shadow-xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between">
          <div>
            <p className="text-xs text-muted">{tickerLabel}</p>
            <h2 className="text-lg font-semibold">
              {letter} — {CANSLIM_LETTER_LABELS[letter] ?? letter}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1 text-muted hover:bg-panel-hover hover:text-foreground"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mb-4 flex items-center gap-3">
          <CanslimBadge verdict={result.verdict} />
        </div>

        {result.reasons.length > 0 && (
          <>
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">
              Why this verdict
            </p>
            <ul className="space-y-2 text-sm">
              {result.reasons.map((reason, index) => (
                <li key={index} className="rounded-lg bg-panel-hover px-3 py-2">
                  {reason}
                </li>
              ))}
            </ul>
          </>
        )}

        {isFundAggregate && result.constituents && result.constituents.length > 0 && (
          <div className="mt-5">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">
              Top holdings used for this letter
            </p>
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-muted">
                    <th className="px-3 py-2 font-medium">Holding</th>
                    <th className="px-3 py-2 text-right font-medium">Weight</th>
                    <th className="px-3 py-2 text-center font-medium">Verdict</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {result.constituents.map((constituent) => (
                    <tr key={constituent.symbol}>
                      <td className="px-3 py-2">
                        <span className="font-mono font-medium">
                          {constituent.symbol}
                        </span>
                        <span className="block text-xs text-muted">
                          {constituent.name}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-right font-mono">
                        {constituent.weight_pct.toFixed(1)}%
                      </td>
                      <td className="px-3 py-2 text-center">
                        <CanslimBadge verdict={constituent.verdict} compact />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {typeof result.values.coverage_pct === "number" && (
              <p className="mt-2 text-xs text-muted">
                Combined weight of these holdings covers{" "}
                {result.values.coverage_pct.toFixed(1)}% of the fund.
              </p>
            )}
          </div>
        )}

        {!isFundAggregate && Object.keys(result.values).length > 0 && (
          <div className="mt-5">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">
              Values
            </p>
            <dl className="grid grid-cols-2 gap-2 text-sm">
              {Object.entries(result.values).map(([key, value]) => (
                <div key={key} className="rounded-lg bg-panel-hover px-3 py-2">
                  <dt className="text-xs text-muted">{key}</dt>
                  <dd className="font-mono">{value}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}
      </div>
    </div>
  );
}