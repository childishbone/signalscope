import { ArrowRight } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { SignalBadge } from "@/components/signal-badge";
import { SIGNAL_LABELS } from "@/lib/constants";
import { ALERTS, SECURITIES, SIGNAL_CHANGES, SIGNAL_ROWS } from "@/lib/mock-data";
import type { SignalState } from "@/lib/types";

const TONE: Record<SignalState, string> = {
  bullish: "text-signal-bullish",
  neutral: "text-signal-neutral",
  bearish: "text-signal-bearish",
};

export default function DashboardPage() {
  const counts: Record<SignalState, number> = { bullish: 0, neutral: 0, bearish: 0 };
  for (const row of SIGNAL_ROWS) counts[row.overall] += 1;

  const stats = [
    { label: "Watchlist Securities", value: SECURITIES.length, tone: "text-foreground" },
    { label: "Bullish Signals", value: counts.bullish, tone: TONE.bullish },
    { label: "Neutral Signals", value: counts.neutral, tone: TONE.neutral },
    { label: "Bearish Signals", value: counts.bearish, tone: TONE.bearish },
  ];

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Overview of your watchlist and its latest technical signals (Overall)."
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map((stat) => (
          <Panel key={stat.label} className="p-4">
            <p className="text-xs text-muted">{stat.label}</p>
            <p className={`mt-2 font-mono text-3xl font-semibold ${stat.tone}`}>{stat.value}</p>
          </Panel>
        ))}
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Panel title="Recent Signal Changes">
          <ul className="divide-y divide-border">
            {SIGNAL_CHANGES.map((change) => (
              <li key={change.id} className="flex flex-wrap items-center gap-x-3 gap-y-2 px-4 py-3">
                <span className="w-14 font-mono text-sm font-medium">{change.ticker}</span>
                <span className="w-24 text-sm text-muted">{SIGNAL_LABELS[change.indicator]}</span>
                <span className="flex items-center gap-2">
                  <SignalBadge state={change.from} />
                  <ArrowRight className="h-3.5 w-3.5 text-muted" aria-hidden />
                  <SignalBadge state={change.to} />
                </span>
                <span className="ml-auto font-mono text-xs text-muted">{change.date}</span>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title="Recent Alerts">
          <ul className="divide-y divide-border">
            {ALERTS.map((alert) => (
              <li key={alert.id} className="px-4 py-3">
                <div className="flex items-baseline justify-between gap-3">
                  <span className="font-mono text-sm font-medium">{alert.ticker}</span>
                  <span className="font-mono text-xs text-muted">{alert.sentAt}</span>
                </div>
                <p className="mt-1 text-sm text-muted">{alert.text}</p>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </>
  );
}