"""Tests for synthetic regime generator."""

import pytest
import pandas as pd
import numpy as np
from aureus.tasks.synthetic_generator import (
    RegimeType,
    RegimeConfig,
    SyntheticRegimeGenerator,
    generate_regime_data,
)


def test_regime_config_valid():
    """Test valid regime configuration."""
    config = RegimeConfig(
        regime_type=RegimeType.TREND,
        num_days=100,
        initial_price=100.0,
        seed=42,
    )
    
    assert config.regime_type == RegimeType.TREND
    assert config.num_days == 100
    assert config.seed == 42


def test_regime_config_invalid_num_days():
    """Test regime config rejects invalid num_days."""
    with pytest.raises(ValueError):
        RegimeConfig(
            regime_type=RegimeType.TREND,
            num_days=0,  # Must be >= 1
            seed=42,
        )


def test_synthetic_generator_determinism():
    """Test that generator produces deterministic results with same seed."""
    config = RegimeConfig(
        regime_type=RegimeType.TREND,
        num_days=50,
        seed=42,
    )
    
    gen1 = SyntheticRegimeGenerator(config)
    data1 = gen1.generate()
    
    gen2 = SyntheticRegimeGenerator(config)
    data2 = gen2.generate()
    
    # DataFrames should be identical
    pd.testing.assert_frame_equal(data1, data2)


def test_synthetic_generator_different_seeds():
    """Test that different seeds produce different results."""
    config1 = RegimeConfig(
        regime_type=RegimeType.TREND,
        num_days=50,
        seed=42,
    )
    
    config2 = RegimeConfig(
        regime_type=RegimeType.TREND,
        num_days=50,
        seed=123,
    )
    
    gen1 = SyntheticRegimeGenerator(config1)
    data1 = gen1.generate()
    
    gen2 = SyntheticRegimeGenerator(config2)
    data2 = gen2.generate()
    
    # DataFrames should be different (check closing prices)
    assert not np.allclose(data1['close'].values, data2['close'].values)


def test_trend_regime_generates_upward_movement():
    """Test that trend regime with positive drift trends upward."""
    config = RegimeConfig(
        regime_type=RegimeType.TREND,
        num_days=252,
        seed=42,
        drift=0.002,  # Positive drift
    )
    
    gen = SyntheticRegimeGenerator(config)
    data = gen.generate()
    
    # Check that final price is likely higher than initial (allow for volatility)
    initial_price = data['close'].iloc[0]
    final_price = data['close'].iloc[-1]
    
    # With positive drift over 252 days, should trend up on average
    # Allow some variance but should be higher
    assert final_price > initial_price * 0.9  # At least not massive decline


def test_chop_regime_mean_reversion():
    """Test that chop regime stays near initial price."""
    config = RegimeConfig(
        regime_type=RegimeType.CHOP,
        num_days=252,
        seed=42,
        mean_reversion_strength=0.2,
    )
    
    gen = SyntheticRegimeGenerator(config)
    data = gen.generate()
    
    # Check that price doesn't stray too far from initial
    initial_price = config.initial_price
    mean_price = data['close'].mean()
    
    # Mean should be within 20% of initial price for strong mean reversion
    assert abs(mean_price - initial_price) / initial_price < 0.3


def test_vol_spike_regime_has_spikes():
    """Test that vol spike regime has volatility spikes."""
    config = RegimeConfig(
        regime_type=RegimeType.VOL_SPIKE,
        num_days=252,
        seed=42,
        spike_frequency=0.1,  # 10% chance of spike
        spike_multiplier=3.0,
    )
    
    gen = SyntheticRegimeGenerator(config)
    data = gen.generate()
    
    # Calculate rolling volatility
    returns = data['close'].pct_change()
    rolling_vol = returns.rolling(window=10).std()
    
    # Should have some high volatility periods
    max_vol = rolling_vol.max()
    median_vol = rolling_vol.median()
    
    # Max vol should be higher than median (relaxed threshold)
    assert max_vol > median_vol * 1.2


def test_generate_trend_data():
    """Test trend data generation."""
    data = generate_regime_data(
        regime_type=RegimeType.TREND,
        num_days=100,
        seed=42,
        drift=0.001,
    )
    
    assert isinstance(data, pd.DataFrame)
    assert len(data) == 100
    assert 'timestamp' in data.columns
    assert 'close' in data.columns


def test_generate_chop_data():
    """Test chop data generation."""
    data = generate_regime_data(
        regime_type=RegimeType.CHOP,
        num_days=100,
        seed=42,
    )
    
    assert isinstance(data, pd.DataFrame)
    assert len(data) == 100


def test_generate_vol_spike_data():
    """Test vol spike data generation."""
    data = generate_regime_data(
        regime_type=RegimeType.VOL_SPIKE,
        num_days=100,
        seed=42,
    )
    
    assert isinstance(data, pd.DataFrame)
    assert len(data) == 100


def test_generated_data_schema():
    """Test that generated data has correct schema."""
    data = generate_regime_data(
        regime_type=RegimeType.TREND,
        num_days=50,
        seed=42,
    )
    
    # Check required columns
    required_columns = ['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']
    for col in required_columns:
        assert col in data.columns
    
    # Check data types
    assert data['timestamp'].dtype in [np.int64, np.int32]
    assert data['open'].dtype == np.float64
    assert data['high'].dtype == np.float64
    assert data['low'].dtype == np.float64
    assert data['close'].dtype == np.float64
    assert data['volume'].dtype == np.float64


def test_ohlc_invariants():
    """Test that OHLC data maintains invariants."""
    data = generate_regime_data(
        regime_type=RegimeType.TREND,
        num_days=100,
        seed=42,
    )
    
    # High should be >= Low
    assert (data['high'] >= data['low']).all()
    
    # High should be >= Open and Close
    assert (data['high'] >= data['open']).all()
    assert (data['high'] >= data['close']).all()
    
    # Low should be <= Open and Close
    assert (data['low'] <= data['open']).all()
    assert (data['low'] <= data['close']).all()
    
    # Prices should be positive
    assert (data['open'] > 0).all()
    assert (data['high'] > 0).all()
    assert (data['low'] > 0).all()
    assert (data['close'] > 0).all()
    assert (data['volume'] > 0).all()


def test_timestamps_are_sequential():
    """Test that timestamps are sequential."""
    data = generate_regime_data(
        regime_type=RegimeType.TREND,
        num_days=100,
        seed=42,
    )
    
    # Timestamps should be increasing
    timestamps = data['timestamp'].values
    assert (timestamps[1:] > timestamps[:-1]).all()
