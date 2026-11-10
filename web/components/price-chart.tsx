"use client";

import {
  CandlestickSeries,
  createChart,
  LineSeries,
  LineStyle,
  type IChartApi,
} from "lightweight-charts";
import { useEffect, useRef, useState } from "react";
import type { ApiBar } from "@/lib/api";
import { bollingerBands, rollingHigh } from "@/lib/indicators";

interface PriceChartProps {
  bars: ApiBar[];
  high52?: number | null;
}

function toggleClass(active: boolean): string {
  return `rounded-full border border-border px-3 py-1 ${
    active ? "bg-panel-hover text-foreground" : "text-muted hover:text-foreground"
  }`;
}

export function PriceChart({ bars, high52 }: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [showBands, setShowBands] = useState(false);
  const [showHigh, setShowHigh] = useState(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      layout: {
        background: { color: "transparent" },
        textColor: "#9ca3af",
      },
      grid: {
        vertLines: { color: "#27272a" },
        horzLines: { color: "#27272a" },
      },
      width: container.clientWidth,
      height: 224,
      timeScale: {
        borderColor: "#27272a",
      },
      rightPriceScale: {
        borderColor: "#27272a",
      },
    });
    chartRef.current = chart;

    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    series.setData(
      bars.map((bar) => ({
        time: bar.trade_date,
        open: Number(bar.open),
        high: Number(bar.high),
        low: Number(bar.low),
        close: Number(bar.close),
      })),
    );

    const dates = bars.map((bar) => bar.trade_date);
    const closes = bars.map((bar) => Number(bar.close));

    if (showBands) {
      const bands = bollingerBands(dates, closes);
      const edge = {
        color: "#60a5fa",
        lineWidth: 1 as const,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      };
      chart.addSeries(LineSeries, edge).setData(bands.upper);
      chart.addSeries(LineSeries, edge).setData(bands.lower);
      chart
        .addSeries(LineSeries, { ...edge, lineStyle: LineStyle.Dotted })
        .setData(bands.middle);
    }

    if (showHigh) {
      chart
        .addSeries(LineSeries, {
          color: "#f59e0b",
          lineWidth: 1,
          lineStyle: LineStyle.Dashed,
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
        })
        .setData(high52 && dates.length > 1 ? [{ time: dates[0], value: high52 }, { time: dates[dates.length - 1], value: high52 }] : rollingHigh(dates, closes));
    }

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (!containerRef.current) return;
      chart.applyOptions({ width: containerRef.current.clientWidth });
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartRef.current = null;
    };
  }, [bars, high52, showBands, showHigh]);

  return (
    <div>
      <div className="mb-2 flex flex-wrap gap-2 text-xs">
        <button
          onClick={() => setShowBands((value) => !value)}
          className={toggleClass(showBands)}
          title="20-day average with lines 2 standard deviations either side. Price near the lower line is the 'dip-buy' reading."
        >
          Bollinger Bands
        </button>
        <button
          onClick={() => setShowHigh((value) => !value)}
          className={toggleClass(showHigh)}
          title="Highest close of the past year (shown once a full year of prices exists)."
        >
          52-week high
        </button>
      </div>
      <div ref={containerRef} className="h-56 w-full" />
    </div>
  );
}