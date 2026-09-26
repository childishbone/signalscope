"""One-off diagnostic: print Yahoo's raw exchange codes for our 7 markets.

Not part of the app. Run once to inform the exchange registry in Phase 4B,
then this script can be deleted or kept for future reference.
"""

import time

import yfinance as yf

# One equity per market, using the tickers we already verified in Phase 0.
TICKERS = {
    "US": "AAPL",
    "Singapore": "D05.SI",
    "Hong Kong": "0700.HK",
    "China (Shanghai)": "600519.SS",
    "China (Shenzhen)": "000001.SZ",
    "Japan": "7203.T",
    "Korea": "005930.KS",
    "Taiwan": "2330.TW",
}

SEARCH_QUERIES = ["Toyota", "Tencent", "Samsung Electronics", "DBS", "Apple"]


def show_ticker_metadata() -> None:
    print("=== Per-ticker exchange metadata (from history_metadata) ===")
    for market, symbol in TICKERS.items():
        meta = yf.Ticker(symbol).history_metadata or {}
        print(
            f"{market:<20} {symbol:<12} "
            f"exchangeName={meta.get('exchangeName')!r:<10} "
            f"fullExchangeName={meta.get('fullExchangeName')!r:<30} "
            f"currency={meta.get('currency')!r}"
        )
        time.sleep(1.2)


def show_search_exchange_fields() -> None:
    print("\n=== Search result fields (raw dict, all keys) ===")
    for query in SEARCH_QUERIES:
        print(f"\n--- '{query}' ---")
        quotes = yf.Search(query, max_results=6).quotes
        for q in quotes:
            print(
                f"  symbol={q.get('symbol')!r:<12} "
                f"exchange={q.get('exchange')!r:<8} "
                f"exchDisp={q.get('exchDisp')!r:<25} "
                f"quoteType={q.get('quoteType')!r}"
            )
        time.sleep(1.2)


if __name__ == "__main__":
    show_ticker_metadata()
    show_search_exchange_fields()
