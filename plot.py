"""
plot_sol_basis_backpack.py
Python ≥3.10   |   pip install requests pandas matplotlib
"""
import requests, time, datetime as dt
import pandas as pd
import matplotlib.pyplot as plt

BASE_URL = "https://api.backpack.exchange/api/v1/klines"
INTERVAL  = "1m"            # Backpack supports 1m .. 1d
LOOKBACK  = dt.timedelta(hours=24)

# --- helper ---------------------------------------------------------------
def to_seconds(ts: dt.datetime) -> int:
    return int(ts.replace(tzinfo=dt.timezone.utc).timestamp())

def get_klines(symbol: str,
               interval: str = INTERVAL,
               start: dt.datetime | None = None,
               end:   dt.datetime | None = None) -> pd.DataFrame:
    """
    Returns a DataFrame indexed by the candle start time (UTC) with
    open, high, low, close, volume, quoteVolume, trades
    """
    if end is None:
        end = dt.datetime.now(dt.timezone.utc)  # Fixed deprecation warning
    if start is None:
        start = end - LOOKBACK
    
    params = {
        "symbol":    symbol,
        "interval":  interval,
        "startTime": to_seconds(start),
        "endTime":   to_seconds(end)
    }
    
    r = requests.get(BASE_URL, params=params, timeout=10)
    r.raise_for_status()
    raw = r.json()
    
    df = pd.DataFrame(raw)
    
    # Fixed: Remove unit="s" since API returns datetime strings, not timestamps
    df["start"] = pd.to_datetime(df["start"], utc=True)
    
    numeric_cols = ["open", "high", "low", "close",
                    "volume", "quoteVolume", "trades"]
    df[numeric_cols] = df[numeric_cols].astype(float)
    df = df.set_index("start").sort_index()
    return df

# --- pull data ------------------------------------------------------------
end_time   = dt.datetime.now(dt.timezone.utc)  # Fixed deprecation warning
start_time = end_time - LOOKBACK

spot_df = get_klines("SOL_USDC",      start=start_time, end=end_time)
perp_df = get_klines("SOL_USDC_PERP", start=start_time, end=end_time)

# --- align & compute spread ----------------------------------------------
common_idx = spot_df.index.intersection(perp_df.index)
spot_close = spot_df.loc[common_idx, "close"]
perp_close = perp_df.loc[common_idx, "close"]
basis      = spot_close - perp_close       # positive => spot premium

# --- save raw + spread ----------------------------------------------------
spot_df.to_csv("sol_spot_backpack.csv")
perp_df.to_csv("sol_perp_backpack.csv")
basis.to_csv("sol_basis_backpack.csv", header=["basis"])

# --- plot -----------------------------------------------------------------
plt.figure(figsize=(10,5))
plt.plot(basis.index, basis.values)
plt.title("SOL Basis (Spot – Perp) — Backpack Exchange")
plt.xlabel("UTC time")
plt.ylabel("Price difference (USDC)")
plt.tight_layout()
plt.show()
