import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { SignalBadge, SignalLegend } from "@/components/signal-badge";
import { INDICATOR_ORDER, SIGNAL_LABELS } from "@/lib/constants";
import { SECURITIES, SIGNAL_ROWS } from "@/lib/mock-data";

export default function TechnicalAnalysisPage() {
  const names = new Map(SECURITIES.map((s) => [s.ticker, s.name]));

  return (
    <>
      <PageHeader
        title="Technical Analysis"
        description="Rule-based signals per indicator. These are outputs of defined rules, not recommendations."
      />

      <div className="mb-4">
        <SignalLegend />
      </div>

      <Panel>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted">
                <th className="px-4 py-3 font-medium">Ticker</th>
                {INDICATOR_ORDER.map((key) => (
                  <th key={key} className="px-4 py-3 text-center font-medium">
                    {SIGNAL_LABELS[key]}
                  </th>
                ))}
                <th className="px-4 py-3 text-center font-medium">{SIGNAL_LABELS.overall}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {SIGNAL_ROWS.map((row) => (
                <tr key={row.ticker} className="hover:bg-panel-hover">
                  <td className="px-4 py-3">
                    <span className="font-mono font-medium">{row.ticker}</span>
                    <span className="block text-xs text-muted">{names.get(row.ticker)}</span>
                  </td>
                  {INDICATOR_ORDER.map((key) => (
                    <td key={key} className="px-4 py-3 text-center">
                      <SignalBadge state={row.signals[key]} compact />
                    </td>
                  ))}
                  <td className="px-4 py-3 text-center">
                    <SignalBadge state={row.overall} compact />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}