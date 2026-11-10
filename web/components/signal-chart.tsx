"use client";

import { useEffect, useMemo, useState } from "react";

import { PriceChart, type ChartOverlay } from "@/components/price-chart";
import { getSecurityBars, type ApiBar } from "@/lib/api";

interface SignalChartProps {
  securityId: number;
  overlay?: ChartOverlay;
}

// About two years of trading days, so the 200-day average has room to draw.
const BARS_TO_LOAD = 504;
const TRADING_DAYS_PER_YEAR = 252;

export function SignalChart({ securityId, overlay }: SignalChartProps) {
  const [bars, setBars] = useState<ApiBar[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getSecurityBars(securityId, BARS_TO_LOAD)
      .then((data) => {
        if (!cancelled) setBars(data);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [securityId]);

  // The same number the 52-Week High signal uses: the highest close of the
  // last year of prices.
  const high52 = useMemo(() => {
    if (!bars || bars.length < TRADING_DAYS_PER_YEAR) return null;
    return Math.max(
      ...bars.slice(-TRADING_DAYS_PER_YEAR).map((bar) => Number(bar.close)),
    );
  }, [bars]);

  if (failed) {
    return (
      <p className="mb-4 text-sm text-muted">Could not load the price chart.</p>
    );
  }
  if (!bars) {
    return <div className="mb-4 h-56 w-full animate-pulse rounded-lg bg-panel-hover" />;
  }

  return (
    <div className="mb-4">
      <PriceChart
        bars={bars}
        high52={high52}
        initialOverlays={overlay ? [overlay] : []}
      />
    </div>
  );
}