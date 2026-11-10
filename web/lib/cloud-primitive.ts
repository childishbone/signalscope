import type {
  IPrimitivePaneRenderer,
  IPrimitivePaneView,
  ISeriesPrimitive,
  SeriesAttachedParameter,
  Time,
} from "lightweight-charts";

import type { LinePoint } from "@/lib/indicators";

export interface CloudPoint {
  time: string;
  a: number;
  b: number;
}

const GREEN = "rgba(34, 197, 94, 0.18)";
const RED = "rgba(239, 68, 68, 0.18)";

/** Pair up the two cloud edges by date; only dates that have both are kept. */
export function cloudPoints(
  senkouA: LinePoint[],
  senkouB: LinePoint[],
): CloudPoint[] {
  const bByTime = new Map(senkouB.map((point) => [point.time, point.value]));
  const points: CloudPoint[] = [];
  for (const point of senkouA) {
    const b = bByTime.get(point.time);
    if (b !== undefined) {
      points.push({ time: point.time, a: point.value, b });
    }
  }
  return points;
}

interface Segment {
  x1: number;
  x2: number;
  a1: number;
  a2: number;
  b1: number;
  b2: number;
  bullish: boolean;
}

type Attached = SeriesAttachedParameter<Time>;

class CloudRenderer implements IPrimitivePaneRenderer {
  private readonly owner: CloudPrimitive;

  constructor(owner: CloudPrimitive) {
    this.owner = owner;
  }

  draw(target: Parameters<IPrimitivePaneRenderer["draw"]>[0]): void {
    const segments = this.owner.segments();
    target.useBitmapCoordinateSpace((scope) => {
      const ctx = scope.context;
      const hr = scope.horizontalPixelRatio;
      const vr = scope.verticalPixelRatio;
      for (const seg of segments) {
        ctx.beginPath();
        ctx.moveTo(seg.x1 * hr, seg.a1 * vr);
        ctx.lineTo(seg.x2 * hr, seg.a2 * vr);
        ctx.lineTo(seg.x2 * hr, seg.b2 * vr);
        ctx.lineTo(seg.x1 * hr, seg.b1 * vr);
        ctx.closePath();
        ctx.fillStyle = seg.bullish ? GREEN : RED;
        ctx.fill();
      }
    });
  }
}

class CloudView implements IPrimitivePaneView {
  private readonly cloudRenderer: CloudRenderer;

  constructor(owner: CloudPrimitive) {
    this.cloudRenderer = new CloudRenderer(owner);
  }

  zOrder() {
    return "bottom" as const;
  }

  renderer(): IPrimitivePaneRenderer {
    return this.cloudRenderer;
  }
}

/** Shades the area between the two Ichimoku cloud edges (green when Senkou A
 * is above B, red when below). Attach it to the price series. */
export class CloudPrimitive implements ISeriesPrimitive<Time> {
  private param: Attached | null = null;
  private readonly points: CloudPoint[];
  private readonly view: CloudView;

  constructor(points: CloudPoint[]) {
    this.points = points;
    this.view = new CloudView(this);
  }

  attached(param: Attached): void {
    this.param = param;
  }

  detached(): void {
    this.param = null;
  }

  paneViews(): readonly IPrimitivePaneView[] {
    return [this.view];
  }

  segments(): Segment[] {
    const param = this.param;
    if (!param) return [];
    const timeScale = param.chart.timeScale();

    const placed = this.points.map((point) => ({
      x: timeScale.timeToCoordinate(point.time as Time),
      a: param.series.priceToCoordinate(point.a),
      b: param.series.priceToCoordinate(point.b),
      bullish: point.a >= point.b,
    }));

    const result: Segment[] = [];
    for (let i = 1; i < placed.length; i += 1) {
      const left = placed[i - 1];
      const right = placed[i];
      if (
        left.x === null ||
        right.x === null ||
        left.a === null ||
        right.a === null ||
        left.b === null ||
        right.b === null
      ) {
        continue;
      }
      result.push({
        x1: left.x,
        x2: right.x,
        a1: left.a,
        a2: right.a,
        b1: left.b,
        b2: right.b,
        bullish: right.bullish,
      });
    }
    return result;
  }
}