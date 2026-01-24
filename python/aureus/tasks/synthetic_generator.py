"""Synthetic market regime generator for benchmarking."""

from enum import Enum
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pydantic import BaseModel, Field


class RegimeType(str, Enum):
    """Types of market regimes."""
    
    TREND = "trend"
    CHOP = "chop"
    VOL_SPIKE = "vol_spike"


class RegimeConfig(BaseModel):
    """Configuration for a market regime."""
    
    regime_type: RegimeType = Field(..., description="Type of market regime")
    num_days: int = Field(252, ge=1, description="Number of trading days")
    initial_price: float = Field(100.0, gt=0, description="Initial price")
    seed: int = Field(42, description="Random seed for determinism")
    
    # Trend parameters
    drift: float = Field(0.0005, description="Daily drift (trend)")
    volatility: float = Field(0.02, gt=0, description="Daily volatility")
    
    # Chop parameters
    mean_reversion_strength: float = Field(0.1, ge=0, le=1, description="Mean reversion strength")
    
    # Vol spike parameters
    spike_frequency: float = Field(0.05, ge=0, le=1, description="Probability of vol spike")
    spike_multiplier: float = Field(3.0, ge=1, description="Volatility multiplier during spike")


class SyntheticRegimeGenerator:
    """Generate synthetic market data for different regimes."""
    
    def __init__(self, config: RegimeConfig):
        """Initialize generator with configuration.
        
        Args:
            config: Regime configuration
        """
        self.config = config
        self.rng = np.random.RandomState(config.seed)
    
    def generate(self) -> pd.DataFrame:
        """Generate OHLCV data based on regime type.
        
        Returns:
            DataFrame with columns: timestamp, symbol, open, high, low, close, volume
        """
        if self.config.regime_type == RegimeType.TREND:
            return self._generate_trend()
        elif self.config.regime_type == RegimeType.CHOP:
            return self._generate_chop()
        elif self.config.regime_type == RegimeType.VOL_SPIKE:
            return self._generate_vol_spike()
        else:
            raise ValueError(f"Unknown regime type: {self.config.regime_type}")
    
    def _generate_trend(self) -> pd.DataFrame:
        """Generate trending market data with drift."""
        prices = []
        price = self.config.initial_price
        start_date = datetime(2023, 1, 1)
        
        for i in range(self.config.num_days):
            timestamp = int((start_date + timedelta(days=i)).timestamp())
            
            # Random walk with drift
            daily_return = self.rng.normal(self.config.drift, self.config.volatility)
            price = price * (1 + daily_return)
            
            # Generate OHLCV
            open_price = price * (1 + self.rng.normal(0, 0.005))
            close = price
            high = max(open_price, close) * (1 + abs(self.rng.normal(0, 0.01)))
            low = min(open_price, close) * (1 - abs(self.rng.normal(0, 0.01)))
            volume = self.rng.uniform(1000000, 5000000)
            
            prices.append({
                'timestamp': timestamp,
                'symbol': 'SYN',
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        return pd.DataFrame(prices)
    
    def _generate_chop(self) -> pd.DataFrame:
        """Generate choppy/range-bound market data."""
        prices = []
        price = self.config.initial_price
        mean_price = self.config.initial_price
        start_date = datetime(2023, 1, 1)
        
        for i in range(self.config.num_days):
            timestamp = int((start_date + timedelta(days=i)).timestamp())
            
            # Mean reversion
            deviation = price - mean_price
            mean_reversion = -self.config.mean_reversion_strength * deviation / mean_price
            random_shock = self.rng.normal(0, self.config.volatility)
            daily_return = mean_reversion + random_shock
            
            price = price * (1 + daily_return)
            
            # Generate OHLCV
            open_price = price * (1 + self.rng.normal(0, 0.005))
            close = price
            high = max(open_price, close) * (1 + abs(self.rng.normal(0, 0.01)))
            low = min(open_price, close) * (1 - abs(self.rng.normal(0, 0.01)))
            volume = self.rng.uniform(1000000, 5000000)
            
            prices.append({
                'timestamp': timestamp,
                'symbol': 'SYN',
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        return pd.DataFrame(prices)
    
    def _generate_vol_spike(self) -> pd.DataFrame:
        """Generate market data with volatility spikes."""
        prices = []
        price = self.config.initial_price
        start_date = datetime(2023, 1, 1)
        
        for i in range(self.config.num_days):
            timestamp = int((start_date + timedelta(days=i)).timestamp())
            
            # Random volatility spike
            vol = self.config.volatility
            if self.rng.random() < self.config.spike_frequency:
                vol *= self.config.spike_multiplier
            
            # Random walk with occasional vol spikes
            daily_return = self.rng.normal(0, vol)
            price = price * (1 + daily_return)
            
            # Generate OHLCV
            open_price = price * (1 + self.rng.normal(0, 0.005))
            close = price
            high = max(open_price, close) * (1 + abs(self.rng.normal(0, 0.01)))
            low = min(open_price, close) * (1 - abs(self.rng.normal(0, 0.01)))
            volume = self.rng.uniform(1000000, 5000000)
            
            prices.append({
                'timestamp': timestamp,
                'symbol': 'SYN',
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        return pd.DataFrame(prices)


def generate_regime_data(
    regime_type: RegimeType,
    num_days: int = 252,
    seed: int = 42,
    **kwargs
) -> pd.DataFrame:
    """Convenience function to generate regime data.
    
    Args:
        regime_type: Type of market regime
        num_days: Number of trading days
        seed: Random seed for determinism
        **kwargs: Additional parameters for RegimeConfig
    
    Returns:
        DataFrame with OHLCV data
    """
    config = RegimeConfig(
        regime_type=regime_type,
        num_days=num_days,
        seed=seed,
        **kwargs
    )
    generator = SyntheticRegimeGenerator(config)
    return generator.generate()
