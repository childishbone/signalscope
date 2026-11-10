"use client";

import { X } from "lucide-react";

import { SignalBadge } from "@/components/signal-badge";
import type { ApiIndicatorResult } from "@/lib/api";
import { BACKTEST_NOTE } from "@/lib/indicator-info";
import type { IndicatorInfo } from "@/lib/indicator-info";

interface SignalDetailPanelProps {
  tickerLabel: string;
  indicatorLabel: string;
  info?: IndicatorInfo;
  result: ApiIndicatorResult;
  onClose: () => void;
}

export function SignalDetailPanel({
  tickerLabel,
  indicatorLabel,
  info,
  result,
  onClose,
}: SignalDetailPanelProps) {
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
            <h2 className="text-lg font-semibold">{indicatorLabel}</h2>
            {info && <p className="text-xs text-muted">{info.role} signal</p>}
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
          <SignalBadge state={result.state} />
          <span className="text-sm text-muted">
            Score: {result.score.toFixed(2)}
          </span>
        </div>

        {info && <p className="mb-4 text-sm text-muted">{info.meaning}</p>}

        <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">
          Why this signal
        </p>
        <ul className="space-y-2 text-sm">
          {result.reasons.map((reason, index) => (
            <li key={index} className="rounded-lg bg-panel-hover px-3 py-2">
              {reason}
            </li>
          ))}
        </ul>

        {info && (
          <>
            <p className="mb-2 mt-5 text-xs font-medium uppercase tracking-wide text-muted">
              What history says
            </p>
            <p className="rounded-lg bg-panel-hover px-3 py-2 text-sm">
              {info.history}
            </p>
            <p className="mt-2 text-xs text-muted">{BACKTEST_NOTE}</p>
          </>
        )}
      </div>
    </div>
  );
}