"""Signal-efficacy backtest: when an indicator says Bullish or Bearish, what
did price actually do afterwards?

Standalone and read-only -- it pulls price history straight from the market
data provider, never touches the database, and prints a results table.

How it works (walk-forward, so there is no lookahead bias):
  for each trading day T in a security's history, every indicator is scored
  using ONLY bars up to and including T -- exactly what the live app would
  have seen that day. We then look at what the price did over the next
  5 / 20 / 60 trading days.

Two views are printed for each indicator and state:
  * ENTRIES -- only the day the indicator *flips into* that state. This is
    the equivalent of a signal event, and is what a live alert would be.
  * ALL DAYS -- every day the indicator is in that state (bigger sample, but
    consecutive days overlap, so treat the hit rate as a rough guide).
Both are compared with a BASELINE: the same statistics over every day, with
no signal at all. A signal only means something if it beats the baseline.

Further views:
  * SCORE -- returns grouped by each indicator's raw score, not just its
    three-way label, plus a rank correlation (does a higher score go with a
    higher forward return?).
  * RISK -- the worst dip over the next 20 days by state (trend indicators
    often predict risk better than direction).
  * STABILITY -- bullish-minus-bearish before vs after a split date, to see
    whether any edge holds in both halves of the period.
  * VERDICT -- fixed pass/fail tests (decided before looking at results):
    a RETURN test (bullish beats bearish at 20d and 60d in both halves) and
    a RISK test (bullish states dip less than bearish in both halves).
    A pass makes an indicator a candidate, not a proven signal.

Research candidates (52-week high, momentum, volatility) live in
candidate_signals.py. Use --indicators to test only some, e.g.
    --indicators High52,Momentum,Volatility,Bollinger

Usage (from the `api` folder, with the virtual environment active):
    python scripts/backtest_signals.py AAPL MSFT D05.SI 0700.HK
    python scripts/backtest_signals.py --period 5y AAPL MSFT
    python scripts/backtest_signals.py --tickers-file my_tickers.txt
"""

from __future__ import annotations

import argparse
import json
import statistics
import tempfile
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from candidate_signals import (  # noqa: I001
    HIGH52_MINIMUM,
    MOMENTUM_MINIMUM,
    VOLATILITY_MINIMUM,
    score_high52,
    score_momentum,
    score_volatility,
)

from signalscope.signals.bollinger import MINIMUM_CLOSES_REQUIRED as BOLLINGER_MIN
from signalscope.signals.bollinger import score_bollinger
from signalscope.signals.dma import MINIMUM_CLOSES_REQUIRED as DMA_MIN
from signalscope.signals.dma import score_dma
from signalscope.signals.ichimoku import MINIMUM_BARS_REQUIRED as ICHIMOKU_MIN
from signalscope.signals.ichimoku import score_ichimoku
from signalscope.signals.macd import MINIMUM_CLOSES_REQUIRED as MACD_MIN
from signalscope.signals.macd import score_macd
from signalscope.signals.rsi import MINIMUM_CLOSES_REQUIRED as RSI_MIN
from signalscope.signals.rsi import score_rsi
from signalscope.signals.types import IndicatorResult
from signalscope.signals.volume import MINIMUM_BARS_REQUIRED as VOLUME_MIN
from signalscope.signals.volume import score_volume

HORIZONS = (5, 20, 60)
CACHE_DIR = Path(tempfile.gettempdir()) / "signalscope_backtest_cache"
STATES = ("bullish", "bearish")
DIP_WINDOW = 20
DIP_THRESHOLD = -10.0


@dataclass(frozen=True)
class PriceSeries:
    """Plain parallel lists, oldest first. `adj_closes` is used for forward
    returns so splits and dividends don't create fake jumps."""

    dates: list[str]
    highs: list[float]
    lows: list[float]
    closes: list[float]
    adj_closes: list[float]
    volumes: list[float]


# ---------------------------------------------------------------- data


def fetch_series(symbol: str, period: str) -> PriceSeries | None:
    """Download (or load from the local cache) daily bars for one ticker."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f"{symbol.replace('/', '_')}_{period}_v2.json"

    if cache_file.exists():
        rows = json.loads(cache_file.read_text())
    else:
        # Imported here so the scoring/stat code above can be tested
        # without the network library installed.
        from signalscope.market_data.yahoo import YahooProvider

        provider = YahooProvider()
        bars = None
        for attempt in range(1, 4):
            try:
                bars = provider.get_historical_bars(symbol, period=period)
                break
            except Exception as exc:  # network / rate limit
                print(f"  {symbol}: attempt {attempt} failed ({exc!r}); retrying")
                time.sleep(2 * attempt)
        if not bars:
            return None
        rows = [
            {
                "d": bar.trade_date.isoformat(),
                "h": float(bar.high),
                "l": float(bar.low),
                "c": float(bar.close),
                "a": float(bar.adj_close if bar.adj_close is not None else bar.close),
                "v": float(bar.volume),
            }
            for bar in bars
        ]
        cache_file.write_text(json.dumps(rows))
        time.sleep(1.0)  # be polite to Yahoo

    return PriceSeries(
        dates=[r["d"] for r in rows],
        highs=[r["h"] for r in rows],
        lows=[r["l"] for r in rows],
        closes=[r["c"] for r in rows],
        adj_closes=[r["a"] for r in rows],
        volumes=[r["v"] for r in rows],
    )


# ------------------------------------------------------------ walk-forward


def _score_dma(s: PriceSeries, end: int) -> IndicatorResult:
    return score_dma(s.closes[:end])


def _score_rsi(s: PriceSeries, end: int) -> IndicatorResult:
    return score_rsi(s.closes[:end])


def _score_ichimoku(s: PriceSeries, end: int) -> IndicatorResult:
    return score_ichimoku(s.highs[:end], s.lows[:end], s.closes[:end])


def _score_macd(s: PriceSeries, end: int) -> IndicatorResult:
    return score_macd(s.closes[:end])


def _score_bollinger(s: PriceSeries, end: int) -> IndicatorResult:
    return score_bollinger(s.closes[:end])


def _score_volume(s: PriceSeries, end: int) -> IndicatorResult:
    return score_volume(s.closes[:end], s.volumes[:end])


def _score_high52(s: PriceSeries, end: int) -> IndicatorResult:
    return score_high52(s.closes[:end])


def _score_momentum(s: PriceSeries, end: int) -> IndicatorResult:
    return score_momentum(s.closes[:end])


def _score_volatility(s: PriceSeries, end: int) -> IndicatorResult:
    return score_volatility(s.closes[:end])


INDICATORS: dict[str, tuple[int, Callable[[PriceSeries, int], IndicatorResult]]] = {
    "DMA": (DMA_MIN, _score_dma),
    "RSI": (RSI_MIN, _score_rsi),
    "Ichimoku": (ICHIMOKU_MIN, _score_ichimoku),
    "MACD": (MACD_MIN, _score_macd),
    "Bollinger": (BOLLINGER_MIN, _score_bollinger),
    "Volume": (VOLUME_MIN, _score_volume),
    "High52": (HIGH52_MINIMUM, _score_high52),
    "Momentum": (MOMENTUM_MINIMUM, _score_momentum),
    "Volatility": (VOLATILITY_MINIMUM, _score_volatility),
}

# Every indicator is judged on exactly the same days: from the day the
# slowest indicator has enough history. Fixed here, before any --indicators
# filtering, so results do not shift depending on which are selected.
COMMON_START = max(minimum for minimum, _ in INDICATORS.values())


def forward_returns(adj: list[float], t: int) -> dict[int, float | None]:
    """% return from day t's close to the close `h` trading days later."""
    return {h: (adj[t + h] / adj[t] - 1.0) * 100.0 if t + h < len(adj) else None for h in HORIZONS}


def worst_dip(adj: list[float], t: int) -> float | None:
    """Lowest close in the next DIP_WINDOW days, as a % change from day t."""
    if t + DIP_WINDOW >= len(adj):
        return None
    return (min(adj[t + k] for k in range(1, DIP_WINDOW + 1)) / adj[t] - 1.0) * 100.0


@dataclass
class Observation:
    date: str
    state: str
    score: float
    is_entry: bool  # True on the day the state flips into `state`
    fwd: dict[int, float | None]
    dip: float | None


def walk_forward(series: PriceSeries) -> dict[str, list[Observation]]:
    """Score every indicator on every day using only data up to that day."""
    results: dict[str, list[Observation]] = {}
    n = len(series.closes)
    for name, (_, scorer) in INDICATORS.items():
        observations: list[Observation] = []
        previous: str | None = None
        for t in range(COMMON_START - 1, n):
            result = scorer(series, t + 1)  # bars 0..t inclusive
            state = result.state.value
            observations.append(
                Observation(
                    date=series.dates[t],
                    state=state,
                    score=result.score,
                    is_entry=(previous is not None and state != previous),
                    fwd=forward_returns(series.adj_closes, t),
                    dip=worst_dip(series.adj_closes, t),
                )
            )
            previous = state
        results[name] = observations
    return results


def baseline(series: PriceSeries) -> list[Observation]:
    """Every day from the same warm-up point, regardless of any signal."""
    start = COMMON_START - 1
    return [
        Observation(
            date=series.dates[t],
            state="any",
            score=0.0,
            is_entry=False,
            fwd=forward_returns(series.adj_closes, t),
            dip=worst_dip(series.adj_closes, t),
        )
        for t in range(start, len(series.closes))
    ]


# ------------------------------------------------------------------- stats


def collect(observations: list[Observation], horizon: int) -> list[float]:
    values = (o.fwd[horizon] for o in observations)
    return [v for v in values if v is not None]


def row_stats(values: list[float], base_mean: float) -> tuple[int, float, float, float, float]:
    """(n, mean %, hit rate %, excess vs baseline %, t-stat vs baseline).

    The t-stat asks "is this mean different from the baseline mean by more
    than chance?" Rule of thumb: |t| above ~2 is worth a look. On the
    ALL DAYS rows it is too optimistic, because consecutive days overlap.
    """
    n = len(values)
    if n == 0:
        return 0, 0.0, 0.0, 0.0, 0.0
    mean = statistics.fmean(values)
    hit = 100.0 * sum(1 for v in values if v > 0) / n
    t_stat = 0.0
    if n >= 2:
        sd = statistics.stdev(values)
        if sd > 0:
            t_stat = (mean - base_mean) / (sd / n**0.5)
    return n, mean, hit, mean - base_mean, t_stat


def print_table(
    title: str,
    rows: list[tuple[str, list[Observation]]],
    base_means: dict[int, float],
) -> None:
    print(f"\n{title}")
    header = f"{'':<30}" + "".join(
        f"| {h:>2}d:    n   mean  excess      t  hit% " for h in HORIZONS
    )
    print(header)
    print("-" * len(header))
    for label, observations in rows:
        line = f"{label:<30}"
        for h in HORIZONS:
            n, mean, hit, excess, t_stat = row_stats(collect(observations, h), base_means[h])
            line += f"| {'':>4}{n:>5} {mean:>+6.2f} {excess:>+7.2f} {t_stat:>+6.1f} {hit:>5.1f} "
        print(line)


def mean_of(observations: list[Observation], horizon: int) -> float:
    values = collect(observations, horizon)
    return statistics.fmean(values) if values else 0.0


def _ranks(values: list[float]) -> list[float]:
    """1-based ranks, with tied values sharing their average rank."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        average = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = average
        i = j + 1
    return ranks


def rank_corr(xs: list[float], ys: list[float]) -> float:
    """Spearman rank correlation; 0.0 if it cannot be computed."""
    if len(xs) < 3:
        return 0.0
    try:
        return statistics.correlation(_ranks(xs), _ranks(ys))
    except statistics.StatisticsError:
        return 0.0


def print_score_view(
    name: str, observations: list[Observation], base_means: dict[int, float]
) -> None:
    scores = sorted({o.score for o in observations})
    rows = [
        (f"{name} score {score:+.0f}", [o for o in observations if o.score == score])
        for score in scores
    ]
    print_table(f"{name.upper()} BY RAW SCORE", rows, base_means)
    line = f"{'rank corr (score vs return)':<30}"
    for h in HORIZONS:
        pairs = [(o.score, o.fwd[h]) for o in observations if o.fwd[h] is not None]
        xs = [x for x, _ in pairs]
        ys = [y for _, y in pairs if y is not None]
        line += f"| {h:>2}d: {rank_corr(xs, ys):>+6.3f}   "
    print(line)


def print_risk_table(title: str, rows: list[tuple[str, list[Observation]]]) -> None:
    print(f"\n{title}")
    header = f"{'':<30}|      n   avg worst dip   share with dip <= {DIP_THRESHOLD:.0f}%"
    print(header)
    print("-" * len(header))
    for label, observations in rows:
        dips = [o.dip for o in observations if o.dip is not None]
        if not dips:
            print(f"{label:<30}|      0")
            continue
        share = 100.0 * sum(1 for d in dips if d <= DIP_THRESHOLD) / len(dips)
        print(f"{label:<30}| {len(dips):>6} {statistics.fmean(dips):>+12.2f}% {share:>20.1f}%")


def print_stability(
    pooled: dict[str, list[Observation]],
    pooled_baseline: list[Observation],
    split: str,
) -> None:
    print(f"\nSTABILITY: bullish minus bearish (all days), before vs after {split}")
    print("(a real edge should be positive in BOTH halves)")
    columns = [(20, True), (20, False), (60, True), (60, False)]
    header = f"{'':<30}" + "".join(
        f"| {h}d {'before' if before else 'after':<6} " for h, before in columns
    )
    print(header)
    print("-" * len(header))

    def half(observations: list[Observation], before: bool) -> list[Observation]:
        return [o for o in observations if (o.date < split) == before]

    line = f"{'baseline avg return':<30}"
    for h, before in columns:
        line += f"| {mean_of(half(pooled_baseline, before), h):>+10.2f} "
    print(line)
    for name in INDICATORS:
        line = f"{name:<30}"
        for h, before in columns:
            part = half(pooled[name], before)
            bull = [o for o in part if o.state == "bullish"]
            bear = [o for o in part if o.state == "bearish"]
            line += f"| {mean_of(bull, h) - mean_of(bear, h):>+10.2f} "
        print(line)


def mean_dip(observations: list[Observation]) -> float:
    dips = [o.dip for o in observations if o.dip is not None]
    return statistics.fmean(dips) if dips else 0.0


def print_risk_stability(
    pooled: dict[str, list[Observation]],
    pooled_baseline: list[Observation],
    split: str,
) -> None:
    print(f"\nRISK STABILITY: average worst 20-day dip, before vs after {split}")
    print("(gap = bullish dip minus bearish dip, in % points; positive = bullish")
    print(" states dipped LESS than bearish ones. It should be positive in BOTH halves)")
    header = (
        f"{'':<30}| gap before | gap after  | bull before | bull after | bear before | bear after"
    )
    print(header)
    print("-" * len(header))

    def half(observations: list[Observation], before: bool) -> list[Observation]:
        return [o for o in observations if (o.date < split) == before]

    base_before = mean_dip(half(pooled_baseline, True))
    base_after = mean_dip(half(pooled_baseline, False))
    print(
        f"{'baseline (all days)':<30}| {'':>10} | {'':>10} "
        f"| {base_before:>+11.2f} | {base_after:>+10.2f} "
        f"| {base_before:>+11.2f} | {base_after:>+10.2f}"
    )
    for name in INDICATORS:
        cells: list[float] = []
        for before in (True, False):
            part = half(pooled[name], before)
            cells.append(mean_dip([o for o in part if o.state == "bullish"]))
            cells.append(mean_dip([o for o in part if o.state == "bearish"]))
        bull_b, bear_b, bull_a, bear_a = cells
        print(
            f"{name:<30}| {bull_b - bear_b:>+10.2f} | {bull_a - bear_a:>+10.2f} "
            f"| {bull_b:>+11.2f} | {bull_a:>+10.2f} | {bear_b:>+11.2f} | {bear_a:>+10.2f}"
        )


MIN_SAMPLE = 300


def print_verdicts(pooled: dict[str, list[Observation]], split: str) -> None:
    """Fixed pass/fail tests, decided before looking at any results."""
    print("\nVERDICT (fixed rules, set before seeing results)")
    print(f"  RETURN test: bullish minus bearish > 0 at 20d AND 60d, before AND after {split}")
    print("  RISK test:   bullish states dip less than bearish, before AND after the split")
    print(f"  Each side needs at least {MIN_SAMPLE} days in each half, else INSUFFICIENT.")
    print("  A PASS only makes an indicator a CANDIDATE. With several indicators tested,")
    print("  one can pass by luck, so a pass still needs a sanity check before shipping.")
    header = f"{'':<30}| RETURN test    | RISK test"
    print(header)
    print("-" * len(header))

    for name in INDICATORS:
        enough = True
        return_ok = True
        risk_ok = True
        for before in (True, False):
            part = [o for o in pooled[name] if (o.date < split) == before]
            bull = [o for o in part if o.state == "bullish"]
            bear = [o for o in part if o.state == "bearish"]
            if len(bull) < MIN_SAMPLE or len(bear) < MIN_SAMPLE:
                enough = False
            for h in (20, 60):
                if mean_of(bull, h) - mean_of(bear, h) <= 0:
                    return_ok = False
            if mean_dip(bull) - mean_dip(bear) <= 0:
                risk_ok = False
        if not enough:
            print(f"{name:<30}| INSUFFICIENT   | INSUFFICIENT")
        else:
            print(
                f"{name:<30}| {'PASS' if return_ok else 'fail':<14} "
                f"| {'PASS' if risk_ok else 'fail'}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Signal-efficacy backtest")
    parser.add_argument("tickers", nargs="*", help="Yahoo tickers, e.g. AAPL D05.SI 0700.HK")
    parser.add_argument("--tickers-file", help="text file with one ticker per line")
    parser.add_argument("--period", default="5y", help="history to pull (default 5y)")
    parser.add_argument(
        "--split-date", default="2024-01-01", help="date splitting the stability check"
    )
    parser.add_argument(
        "--indicators",
        help="comma-separated indicator names to test (default: all), "
        "e.g. High52,Momentum,Volatility,Bollinger",
    )
    args = parser.parse_args()

    if args.indicators:
        wanted = [name.strip() for name in args.indicators.split(",") if name.strip()]
        unknown = [name for name in wanted if name not in INDICATORS]
        if unknown:
            parser.error(
                f"unknown indicator(s): {', '.join(unknown)}; choose from {', '.join(INDICATORS)}"
            )
        for name in list(INDICATORS):
            if name not in wanted:
                del INDICATORS[name]

    tickers = list(args.tickers)
    if args.tickers_file:
        tickers += [
            line.strip()
            for line in Path(args.tickers_file).read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]
    if not tickers:
        parser.error("give at least one ticker (or --tickers-file)")

    pooled: dict[str, list[Observation]] = defaultdict(list)
    pooled_baseline: list[Observation] = []

    print(f"Backtesting {len(tickers)} ticker(s), period={args.period}")
    for symbol in tickers:
        series = fetch_series(symbol, args.period)
        if series is None:
            print(f"  {symbol}: no data returned -- skipped")
            continue
        usable = len(series.closes) - COMMON_START
        print(
            f"  {symbol}: {len(series.closes)} bars "
            f"({series.dates[0]} -> {series.dates[-1]}), {max(usable, 0)} scoreable days"
        )
        if usable < 100:
            print("    too little history for a meaningful backtest -- skipped")
            continue
        for name, observations in walk_forward(series).items():
            pooled[name].extend(observations)
        pooled_baseline.extend(baseline(series))

    if not pooled_baseline:
        print("\nNo usable data -- nothing to report.")
        return

    base_means = {h: mean_of(pooled_baseline, h) for h in HORIZONS}
    print_table("BASELINE (every day, no signal)", [("all days", pooled_baseline)], base_means)
    for name in INDICATORS:
        observations = pooled[name]
        entries = [
            (f"{name} -> {s} (entry)", [o for o in observations if o.state == s and o.is_entry])
            for s in STATES
        ]
        all_days = [
            (f"{name} = {s} (all days)", [o for o in observations if o.state == s]) for s in STATES
        ]
        print_table(f"{name.upper()}", entries + all_days, base_means)

    print("\nBULLISH minus BEARISH, mean forward return in % points")
    print("(a useful indicator should be clearly POSITIVE: bullish beats bearish)")
    header = f"{'':<30}" + "".join(f"| {h:>2}d      " for h in HORIZONS)
    print(header)
    print("-" * len(header))
    for name in INDICATORS:
        observations = pooled[name]
        for label, only_entries in (("entries", True), ("all days", False)):
            line = f"{name + ' (' + label + ')':<30}"
            keep = [o for o in observations if o.is_entry or not only_entries]
            bull = [o for o in keep if o.state == "bullish"]
            bear = [o for o in keep if o.state == "bearish"]
            for h in HORIZONS:
                line += f"| {mean_of(bull, h) - mean_of(bear, h):>+7.2f}  "
            print(line)

    for name in INDICATORS:
        print_score_view(name, pooled[name], base_means)

    risk_rows: list[tuple[str, list[Observation]]] = [("baseline (all days)", pooled_baseline)]
    for name in INDICATORS:
        for state in ("bullish", "neutral", "bearish"):
            risk_rows.append((f"{name} = {state}", [o for o in pooled[name] if o.state == state]))
    print_risk_table("RISK: worst dip over the next 20 days", risk_rows)

    print_stability(pooled, pooled_baseline, args.split_date)
    print_risk_stability(pooled, pooled_baseline, args.split_date)
    print_verdicts(pooled, args.split_date)

    print(
        "\nHow to read: 'excess' = mean minus the baseline mean; 't' = excess measured in "
        "standard errors (|t| < 2 is probably noise; all-days rows overstate t). "
        "Bullish rows want positive excess, bearish rows want negative. For RISK, a bearish "
        "state is useful if its dips are clearly WORSE than the baseline's."
    )


if __name__ == "__main__":
    main()
