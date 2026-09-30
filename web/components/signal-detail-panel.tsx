"use client";

import { X } from "lucide-react";

import { SignalBadge } from "@/components/signal-badge";
import type { ApiIndicatorResult } from "@/lib/api";

interface SignalDetailPanelProps {
  tickerLabel: string;
  indicatorLabel: string;
  result: ApiIndicatorResult;
  onClose: () => void;
}

export function SignalDetailPanel({
  tickerLabel,
  indicatorLabel,
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

        <p className="mt-4 text-xs text-muted">
          Technical signals are generated algorithmically for informational
          purposes and do not constitute investment advice.
        </p>
      </div>
    </div>
  );
}
