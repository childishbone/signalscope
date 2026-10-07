import { Check, CircleHelp, X, type LucideIcon } from "lucide-react";

import type { CanslimVerdict } from "@/lib/types";

interface VerdictStyle {
  label: string;
  legend: string;
  Icon: LucideIcon;
  className: string;
}

const VERDICT_STYLES: Record<CanslimVerdict, VerdictStyle> = {
  pass: {
    label: "Pass",
    legend: "Green = Pass",
    Icon: Check,
    className: "bg-signal-bullish/15 text-signal-bullish ring-signal-bullish/30",
  },
  fail: {
    label: "Fail",
    legend: "Red = Fail",
    Icon: X,
    className: "bg-signal-bearish/15 text-signal-bearish ring-signal-bearish/30",
  },
  insufficient_data: {
    label: "Insufficient Data",
    legend: "Gray = Insufficient data (excluded from the score)",
    Icon: CircleHelp,
    className: "bg-muted/15 text-muted ring-muted/30",
  },
};

export function CanslimBadge({
  verdict,
  compact = false,
}: {
  verdict: CanslimVerdict;
  compact?: boolean;
}) {
  const { label, Icon, className } = VERDICT_STYLES[verdict];
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

export function CanslimLegend() {
  const verdicts: CanslimVerdict[] = ["pass", "fail", "insufficient_data"];
  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-muted">
      {verdicts.map((verdict) => (
        <span key={verdict} className="flex items-center gap-2">
          <CanslimBadge verdict={verdict} compact />
          {VERDICT_STYLES[verdict].legend}
        </span>
      ))}
    </div>
  );
}