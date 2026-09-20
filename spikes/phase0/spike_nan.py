import time

import pandas as pd
import yfinance as yf

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

SUSPECTS = ["ES3.SI", "2800.HK", "0050.TW"]
CONTROL = ["D05.SI"]  # a stock that came back fine

for symbol in SUSPECTS + CONTROL:
    df = yf.Ticker(symbol).history(period="2y", interval="1d", auto_adjust=False)
    bad = df[["Open", "High", "Low", "Close"]].isna().any(axis=1)
    print(f"\n=== {symbol}: {len(df)} bars, {int(bad.sum())} with NaN in OHLC ===")
    print(df[["Open", "High", "Low", "Close", "Volume"]].tail(6))
    if bad.any():
        print("NaN dates:", [d.date().isoformat() for d in df.index[bad]][:10])
    time.sleep(1.5)
