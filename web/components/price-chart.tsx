"use client";

import {
  CandlestickSeries,
  createChart,
  LineSeries,
  LineStyle,
} from "lightweight-charts";
import { useEffect, useRef, useState } from "react";
import type { ApiBar } from "@/lib/api";
import { bollingerBands, rollingHigh, sma } from "@/lib/indicators";

export type ChartOverlay = "bands" | "high" | "dma";

interface PriceChartProps {
  bars: ApiBar[];
  high52?: number | null;
  initialOverlays?: ChartOverlay[];
}

const DMA_LINES = [
  { period: 20, color: "#f472b6" },
  { period: 50, color: "#38bdf8" },
  { period: 200, color: "#c084fc" },
];

function toggleClass(active: boolean): string {
  return `rounded-full border border-border px-3 py-1 ${
    active ? "bg-panel-hover text-foreground" : "text-muted hover:text-foreground"
  }`;
}

export function PriceChart({
  bars,
  high52,
  initialOverlays = [],
}: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [showBands, setShowBands] = useState(initialOverlays.includes("bands"));
  const [showHigh, setShowHigh] = useState(initialOverlays.includes("high"));
  const [showDma, setShowDma] = useState(initialOverlays.includes("dma"));

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
    const lineLook = {
      lineWidth: 1 as const,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    };

    if (showBands) {
      const bands = bollingerBands(dates, closes);
      const edge = { ...lineLook, color: "#60a5fa" };
      chart.addSeries(LineSeries, edge).setData(bands.upper);
      chart.addSeries(LineSeries, edge).setData(bands.lower);
      chart
        .addSeries(LineSeries, { ...edge, lineStyle: LineStyle.Dotted })
        .setData(bands.middle);
    }

    if (showDma) {
      for (const line of DMA_LINES) {
        chart
          .addSeries(LineSeries, { ...lineLook, color: line.color })
          .setData(sma(dates, closes, line.period));
      }
    }

    if (showHigh) {
      const points =
        high52 && dates.length > 1
          ? [
              { time: dates[0], value: high52 },
              { time: dates[dates.length - 1], value: high52 },
            ]
          : rollingHigh(dates, closes);
      chart
        .addSeries(LineSeries, {
          ...lineLook,
          color: "#f59e0b",
          lineStyle: LineStyle.Dashed,
        })
        .setData(points);
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
    };
  }, [bars, high52, showBands, showHigh, showDma]);

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
          onClick={() => setShowDma((value) => !value)}
          className={toggleClass(showDma)}
          title="20, 50 and 200-day moving averages, the lines the DMA signal compares."
        >
          Moving averages
        </button>
        <button
          onClick={() => setShowHigh((value) => !value)}
          className={toggleClass(showHigh)}
          title="Highest close of the past year."
        >
          52-week high
        </button>
      </div>
      {showDma && (
        <p className="mb-2 text-xs text-muted">
          Pink: 20-day. Blue: 50-day. Purple: 200-day.
        </p>
      )}
      <div ref={containerRef} className="h-56 w-full" />
    </div>
  );
}