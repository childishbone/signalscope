import { Minus, TrendingDown, TrendingUp, type LucideIcon } from "lucide-react";

import type { SignalState } from "@/lib/types";

interface SignalStyle {
  label: string;
  legend: string;
  Icon: LucideIcon;
  className: string;
}

const SIGNAL_STYLES: Record<SignalState, SignalStyle> = {
  bullish: {
    label: "Bullish",
    legend: "Green = Bullish",
    Icon: TrendingUp,
    className: "bg-signal-bullish/15 text-signal-bullish ring-signal-bullish/30",
  },
  neutral: {
    label: "Neutral",
    legend: "Yellow = Neutral / Inconclusive",
    Icon: Minus,
    className: "bg-signal-neutral/15 text-signal-neutral ring-signal-neutral/30",
  },
  bearish: {
    label: "Bearish",
    legend: "Red = Bearish",
    Icon: TrendingDown,
    className: "bg-signal-bearish/15 text-signal-bearish ring-signal-bearish/30",
  },
};

export function SignalBadge({
  state,
  compact = false,
}: {
  state: SignalState;
  compact?: boolean;
}) {
  const { label, Icon, className } = SIGNAL_STYLES[state];
  return (
    <span
      title={label}
      role={compact ? "img" : undefined}
      aria-label={compact ? label : undefined}
      className={`inline-flex items-center justify-center gap-1.5 rounded-full text-xs font-medium ring-1 ring-inset ${
        compact ? "h-7 w-10" : "px-2.5 py-1"
      } ${className}`}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden />
      {!compact && label}
    </span>
  );
}

export function SignalLegend() {
  const states: SignalState[] = ["bullish", "neutral", "bearish"];
  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-muted">
      {states.map((state) => (
        <span key={state} className="flex items-center gap-2">
          <SignalBadge state={state} compact />
          {SIGNAL_STYLES[state].legend}
        </span>
      ))}
    </div>
  );
}