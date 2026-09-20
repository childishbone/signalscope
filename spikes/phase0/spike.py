"""Phase 0 feasibility spike: can Yahoo (via yfinance) serve all 7 markets?"""

import time

import yfinance as yf

# One equity + one ETF per market (China: one Shanghai, one Shenzhen listing).
TICKERS: dict[str, list[str]] = {
    "US": ["AAPL", "SPY"],
    "Singapore": ["D05.SI", "ES3.SI"],
    "Hong Kong": ["0700.HK", "2800.HK"],
    "China": ["600519.SS", "000001.SZ"],
    "Japan": ["7203.T", "1306.T"],
    "Korea": ["005930.KS", "069500.KS"],
    "Taiwan": ["2330.TW", "0050.TW"],
}

SEARCH_QUERIES = ["Toyota", "Tencent", "Samsung Electronics"]

# 200-DMA needs 200 bars; Ichimoku needs ~78. We want comfortable headroom.
MIN_BARS = 260


def check_ticker(symbol: str) -> dict[str, object]:
    """Fetch ~2y of daily candles and summarise what came back."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2y", interval="1d", auto_adjust=False)
        if df.empty:
            return {"symbol": symbol, "status": "EMPTY"}
        meta = ticker.history_metadata or {}
        return {
            "symbol": symbol,
            "status": "OK" if len(df) >= MIN_BARS else "SHORT",
            "bars": len(df),
            "last_date": df.index[-1].date().isoformat(),
            "last_close": round(float(df["Close"].iloc[-1]), 2),
            "volume": int(df["Volume"].iloc[-1]),
            "exchange": meta.get("exchangeName", "?"),
            "currency": meta.get("currency", "?"),
            "has_ohlc": all(c in df.columns for c in ("Open", "High", "Low", "Close")),
        }
    except Exception as exc:  # noqa: BLE001 - spike script, we want to see everything
        return {"symbol": symbol, "status": f"ERROR: {type(exc).__name__}: {exc}"}


def check_search(query: str) -> None:
    """Symbol search is how the Watchlist page will find securities."""
    try:
        quotes = yf.Search(query, max_results=5).quotes
        print(f"\nSearch '{query}': {len(quotes)} results")
        for q in quotes:
            print(
                f"  {q.get('symbol', '?'):<12} {q.get('shortname', '?'):<35} "
                f"{q.get('exchDisp', '?'):<22} {q.get('quoteType', '?')}"
            )
    except Exception as exc:  # noqa: BLE001
        print(f"\nSearch '{query}' FAILED: {type(exc).__name__}: {exc}")


def main() -> None:
    print(f"yfinance version: {yf.__version__}\n")
    print(
        f"{'Market':<11}{'Symbol':<11}{'Status':<8}{'Bars':<6}{'Last date':<12}"
        f"{'Close':<12}{'Volume':<14}{'Exchange':<10}{'Ccy'}"
    )
    print("-" * 95)

    failures = 0
    for market, symbols in TICKERS.items():
        for symbol in symbols:
            r = check_ticker(symbol)
            if r["status"] != "OK":
                failures += 1
            if "bars" in r:
                print(
                    f"{market:<11}{r['symbol']:<11}{r['status']:<8}{r['bars']:<6}"
                    f"{r['last_date']:<12}{r['last_close']:<12}{r['volume']:<14}"
                    f"{r['exchange']:<10}{r['currency']}"
                )
            else:
                print(f"{market:<11}{r['symbol']:<11}{r['status']}")
            time.sleep(1.5)  # be polite; avoids tripping Yahoo's rate limiter

    print(f"\nTickers not OK: {failures} of {sum(len(s) for s in TICKERS.values())}")

    for query in SEARCH_QUERIES:
        check_search(query)
        time.sleep(1.5)


if __name__ == "__main__":
    main()
