"use client";

import {
  CandlestickSeries,
  createChart,
  LineSeries,
  LineStyle,
} from "lightweight-charts";
import { useEffect, useRef, useState } from "react";
import type { ApiBar } from "@/lib/api";
import {
  bollingerBands,
  ichimokuLines,
  rollingHigh,
  rsiSeries,
  sma,
} from "@/lib/indicators";

export type ChartOverlay = "bands" | "high" | "dma" | "ichimoku" | "rsi";

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

const RSI_PERIOD = 14;

const CHART_LOOK = {
  layout: {
    background: { color: "transparent" },
    textColor: "#9ca3af",
  },
  grid: {
    vertLines: { color: "#27272a" },
    horzLines: { color: "#27272a" },
  },
  timeScale: { borderColor: "#27272a" },
  rightPriceScale: { borderColor: "#27272a" },
};

const LINE_LOOK = {
  lineWidth: 1 as const,
  priceLineVisible: false,
  lastValueVisible: false,
  crosshairMarkerVisible: false,
};

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
  const rsiRef = useRef<HTMLDivElement>(null);
  const [showBands, setShowBands] = useState(initialOverlays.includes("bands"));
  const [showHigh, setShowHigh] = useState(initialOverlays.includes("high"));
  const [showDma, setShowDma] = useState(initialOverlays.includes("dma"));
  const [showIchimoku, setShowIchimoku] = useState(
    initialOverlays.includes("ichimoku"),
  );
  const [showRsi, setShowRsi] = useState(initialOverlays.includes("rsi"));

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      ...CHART_LOOK,
      width: container.clientWidth,
      height: 224,
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
    const highs = bars.map((bar) => Number(bar.high));
    const lows = bars.map((bar) => Number(bar.low));

    if (showBands) {
      const bands = bollingerBands(dates, closes);
      const edge = { ...LINE_LOOK, color: "#60a5fa" };
      chart.addSeries(LineSeries, edge).setData(bands.upper);
      chart.addSeries(LineSeries, edge).setData(bands.lower);
      chart
        .addSeries(LineSeries, { ...edge, lineStyle: LineStyle.Dotted })
        .setData(bands.middle);
    }

    if (showDma) {
      for (const line of DMA_LINES) {
        chart
          .addSeries(LineSeries, { ...LINE_LOOK, color: line.color })
          .setData(sma(dates, closes, line.period));
      }
    }

    if (showIchimoku) {
      const lines = ichimokuLines(dates, highs, lows);
      const drawn = [
        { points: lines.tenkan, color: "#22d3ee" },
        { points: lines.kijun, color: "#fb923c" },
        { points: lines.senkouA, color: "#86efac" },
        { points: lines.senkouB, color: "#fca5a5" },
      ];
      for (const line of drawn) {
        chart
          .addSeries(LineSeries, { ...LINE_LOOK, color: line.color })
          .setData(line.points);
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
          ...LINE_LOOK,
          color: "#f59e0b",
          lineStyle: LineStyle.Dashed,
        })
        .setData(points);
    }

    chart.timeScale().fitContent();

    // The RSI strip sits under the price chart and uses the same dates, so
    // the two line up.
    const rsiContainer = showRsi ? rsiRef.current : null;
    const rsiChart = rsiContainer
      ? createChart(rsiContainer, {
          ...CHART_LOOK,
          width: rsiContainer.clientWidth,
          height: 112,
        })
      : null;

    if (rsiChart) {
      const rsiLine = rsiChart.addSeries(LineSeries, {
        ...LINE_LOOK,
        color: "#a78bfa",
        autoscaleInfoProvider: () => ({
          priceRange: { minValue: 0, maxValue: 100 },
        }),
      });
      rsiLine.setData([
        ...dates.slice(0, RSI_PERIOD).map((time) => ({ time })),
        ...rsiSeries(dates, closes, RSI_PERIOD),
      ]);
      for (const level of [30, 50, 70]) {
        rsiLine.createPriceLine({
          price: level,
          color: level === 50 ? "#52525b" : "#71717a",
          lineWidth: 1,
          lineStyle: LineStyle.Dashed,
          axisLabelVisible: true,
          title: "",
        });
      }
      rsiChart.timeScale().fitContent();
    }

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
      if (rsiChart && rsiRef.current) {
        rsiChart.applyOptions({ width: rsiRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      rsiChart?.remove();
    };
  }, [bars, high52, showBands, showHigh, showDma, showIchimoku, showRsi]);

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
          onClick={() => setShowIchimoku((value) => !value)}
          className={toggleClass(showIchimoku)}
          title="The Ichimoku lines the signal reads: Tenkan, Kijun and the two cloud edges."
        >
          Ichimoku
        </button>
        <button
          onClick={() => setShowHigh((value) => !value)}
          className={toggleClass(showHigh)}
          title="Highest close of the past year."
        >
          52-week high
        </button>
        <button
          onClick={() => setShowRsi((value) => !value)}
          className={toggleClass(showRsi)}
          title="14-day RSI in a strip under the chart. Above 70 is stretched up, below 30 is stretched down."
        >
          RSI
        </button>
      </div>
      {showDma && (
        <p className="mb-2 text-xs text-muted">
          Pink: 20-day. Blue: 50-day. Purple: 200-day.
        </p>
      )}
      {showIchimoku && (
        <p className="mb-2 text-xs text-muted">
          Cyan: Tenkan (9-day). Orange: Kijun (26-day). Light green and light
          red: the two edges of the cloud (Senkou A and B). Price above both
          edges is bullish; below both is bearish.
        </p>
      )}
      <div ref={containerRef} className="h-56 w-full" />
      {showRsi && (
        <>
          <p className="mb-1 mt-3 text-xs text-muted">
            RSI (14-day). Dashed lines at 30, 50 and 70.
          </p>
          <div ref={rsiRef} className="h-28 w-full" />
        </>
      )}
    </div>
  );
}