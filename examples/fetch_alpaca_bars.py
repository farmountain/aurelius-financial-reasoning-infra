#!/usr/bin/env python3
"""Fetch historical bars from Alpaca Data API and save as parquet for AURELIUS backtests."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd


BASE_URL = "https://data.alpaca.markets/v2/stocks"


def iso_to_epoch_seconds(ts: str) -> int:
    if ts.endswith("Z"):
        ts = ts.replace("Z", "+00:00")
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def fetch_bars(
    symbol: str,
    start: str,
    end: str,
    timeframe: str,
    feed: str,
    adjustment: str,
) -> list[dict]:
    api_key = os.getenv("APCA_API_KEY_ID")
    api_secret = os.getenv("APCA_API_SECRET_KEY")

    if not api_key or not api_secret:
        raise RuntimeError(
            "Missing Alpaca credentials. Set APCA_API_KEY_ID and APCA_API_SECRET_KEY."
        )

    params = {
        "start": start,
        "end": end,
        "timeframe": timeframe,
        "feed": feed,
        "adjustment": adjustment,
        "sort": "asc",
        "limit": 10000,
    }

    url = f"{BASE_URL}/{symbol}/bars?{urlencode(params)}"
    req = Request(
        url,
        headers={
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret,
            "Accept": "application/json",
        },
    )

    with urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    bars = payload.get("bars", [])
    return bars


def to_aurelius_dataframe(symbol: str, bars: list[dict]) -> pd.DataFrame:
    rows = []
    for b in bars:
        rows.append(
            {
                "timestamp": iso_to_epoch_seconds(b["t"]),
                "symbol": symbol,
                "open": float(b["o"]),
                "high": float(b["h"]),
                "low": float(b["l"]),
                "close": float(b["c"]),
                "volume": float(b.get("v", 0.0)),
            }
        )

    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="AAPL")
    parser.add_argument("--start", required=True, help="ISO timestamp, e.g. 2024-01-01T00:00:00Z")
    parser.add_argument("--end", required=True, help="ISO timestamp, e.g. 2024-06-30T00:00:00Z")
    parser.add_argument("--timeframe", default="1Day", help="Alpaca timeframe, e.g. 1Min, 5Min, 1Hour, 1Day")
    parser.add_argument("--feed", default="iex", choices=["iex", "sip"], help="Data feed")
    parser.add_argument("--adjustment", default="raw", choices=["raw", "split", "dividend", "all"])
    parser.add_argument("--out", default="examples/alpaca_data.parquet")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        bars = fetch_bars(
            symbol=args.symbol,
            start=args.start,
            end=args.end,
            timeframe=args.timeframe,
            feed=args.feed,
            adjustment=args.adjustment,
        )
    except Exception as e:
        print(f"ERROR fetching Alpaca bars: {e}")
        return 1

    if not bars:
        print("No bars returned from Alpaca.")
        return 1

    df = to_aurelius_dataframe(args.symbol, bars)
    df.to_parquet(args.out, index=False)

    print(f"Fetched {len(df)} bars for {args.symbol}")
    print(f"Saved: {args.out}")
    print(df.head(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
