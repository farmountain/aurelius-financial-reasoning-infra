#!/usr/bin/env python3
"""Generate sample OHLCV data for testing."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set seed for reproducibility
np.random.seed(42)

# Generate 252 days of data (1 trading year)
num_days = 252
start_date = datetime(2023, 1, 1)

timestamps = []
prices = []
initial_price = 150.0
price = initial_price

for i in range(num_days):
    timestamp = int((start_date + timedelta(days=i)).timestamp())
    
    # Random walk with drift
    daily_return = np.random.normal(0.0005, 0.02)
    price = price * (1 + daily_return)
    
    # Generate OHLCV
    high = price * (1 + abs(np.random.normal(0, 0.01)))
    low = price * (1 - abs(np.random.normal(0, 0.01)))
    open_price = price * (1 + np.random.normal(0, 0.005))
    close = price
    volume = np.random.uniform(1000000, 5000000)
    
    timestamps.append(timestamp)
    prices.append({
        'timestamp': timestamp,
        'symbol': 'AAPL',
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })

df = pd.DataFrame(prices)
print(f"Generated {len(df)} bars")
print(df.head())
print(f"\nPrice range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")

# Save to parquet
df.to_parquet('examples/data.parquet', index=False)
print("\nSaved to examples/data.parquet")
