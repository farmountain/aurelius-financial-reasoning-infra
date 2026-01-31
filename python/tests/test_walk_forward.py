"""
Tests for walk-forward validation module.
"""

import pytest
from pathlib import Path
import json
import tempfile
from datetime import datetime, timedelta
import pandas as pd

from aureus.walk_forward import (
    WalkForwardWindow,
    WalkForwardResult,
    WalkForwardAnalysis,
    WalkForwardValidator
)


def create_mock_data_file(tmp_path, num_days=365, start_date=None):
    """Create a mock data CSV file for testing."""
    if start_date is None:
        start_date = datetime(2020, 1, 1)
    
    dates = [start_date + timedelta(days=i) for i in range(num_days)]
    data = {
        "timestamp": [int(d.timestamp()) for d in dates],  # Use timestamp column
        "close": [100 + i * 0.1 for i in range(num_days)]
    }
    
    df = pd.DataFrame(data)
    data_path = tmp_path / "test_data.csv"
    df.to_csv(data_path, index=False)
    
    return data_path


def create_mock_backtest_result(tmp_path, sharpe=1.5, total_return=0.20):
    """Create a mock backtest result file."""
    result = {
        "sharpe_ratio": sharpe,
        "total_return": total_return,
        "max_drawdown": -0.15,
        "win_rate": 0.55
    }
    
    # Create directory if it doesn't exist
    tmp_path.mkdir(parents=True, exist_ok=True)
    
    result_path = tmp_path / "backtest_stats.json"
    with open(result_path, "w") as f:
        json.dump(result, f)
    
    return result_path


class TestWalkForwardWindow:
    """Test WalkForwardWindow dataclass."""
    
    def test_window_creation(self):
        """Test creating a walk-forward window."""
        window = WalkForwardWindow(
            window_id=1,
            train_start=1577836800,  # 2020-01-01 timestamp
            train_end=1593561600,     # 2020-06-30 timestamp
            test_start=1593648000,    # 2020-07-01 timestamp
            test_end=1601510400       # 2020-09-30 timestamp
        )
        
        assert window.window_id == 1
        assert window.train_start == 1577836800
        assert window.test_end == 1601510400


class TestWalkForwardValidator:
    """Test WalkForwardValidator class."""
    
    def test_validator_creation(self):
        """Test creating a validator."""
        validator = WalkForwardValidator(num_windows=3)
        
        assert validator.num_windows == 3
        assert validator.min_test_sharpe == 0.5
        assert validator.max_degradation == 0.3
    
    def test_validator_custom_params(self):
        """Test creating validator with custom parameters."""
        validator = WalkForwardValidator(
            num_windows=5,
            min_test_sharpe=1.0,
            max_degradation=0.2
        )
        
        assert validator.num_windows == 5
        assert validator.min_test_sharpe == 1.0
        assert validator.max_degradation == 0.2
    
    def test_create_windows(self, tmp_path):
        """Test creating walk-forward windows from data."""
        # Create mock data file with 365 days
        data_path = create_mock_data_file(tmp_path, num_days=365)
        
        validator = WalkForwardValidator(num_windows=3)
        windows = validator.create_windows(str(data_path))
        
        # Should create 3 windows
        assert len(windows) == 3
        
        # Check window IDs (starts at 1, not 0)
        assert windows[0].window_id == 1
        assert windows[1].window_id == 2
        assert windows[2].window_id == 3
        
        # Check that train/test periods don't overlap
        for window in windows:
            assert window.train_start < window.train_end
            assert window.test_start < window.test_end
            assert window.train_end <= window.test_start
    
    def test_create_windows_insufficient_data(self, tmp_path):
        """Test that insufficient data still creates windows but fewer than requested."""
        # Create mock data file with only 100 days (smaller dataset)
        data_path = create_mock_data_file(tmp_path, num_days=100)
        
        validator = WalkForwardValidator(num_windows=3)
        
        # Should create windows, but may be fewer than requested
        windows = validator.create_windows(str(data_path))
        
        # Should create at least 1 window
        assert len(windows) >= 1
        assert len(windows) <= 3
    
    def test_validate_passing_strategy(self, tmp_path):
        """Test validating a strategy that passes all criteria."""
        # Create mock windows
        windows = [
            WalkForwardWindow(0, 1577836800, 1593561600, 1593648000, 1601510400),
            WalkForwardWindow(1, 1593648000, 1609459200, 1609545600, 1617321600),
            WalkForwardWindow(2, 1609545600, 1625097600, 1625184000, 1632960000),
        ]
        
        # Create mock results with good Sharpe ratios
        results = [
            WalkForwardResult(
                window_id=0,
                train_period=(1577836800, 1593561600),
                test_period=(1593648000, 1601510400),
                train_stats={"sharpe_ratio": 2.0, "total_return": 0.25},
                test_stats={"sharpe_ratio": 1.8, "total_return": 0.22},
                performance_degradation=-0.1,  # 10% degradation
                is_overfitting=False
            ),
            WalkForwardResult(
                window_id=1,
                train_period=(1593648000, 1609459200),
                test_period=(1609545600, 1617321600),
                train_stats={"sharpe_ratio": 2.1, "total_return": 0.26},
                test_stats={"sharpe_ratio": 1.9, "total_return": 0.23},
                performance_degradation=-0.095,  # 9.5% degradation
                is_overfitting=False
            ),
            WalkForwardResult(
                window_id=2,
                train_period=(1609545600, 1625097600),
                test_period=(1625184000, 1632960000),
                train_stats={"sharpe_ratio": 2.0, "total_return": 0.25},
                test_stats={"sharpe_ratio": 1.85, "total_return": 0.23},
                performance_degradation=-0.075,  # 7.5% degradation
                is_overfitting=False
            ),
        ]
        
        validator = WalkForwardValidator(num_windows=3)
        analysis = validator.validate(windows=windows, results=results)
        
        assert analysis.passed is True
        assert len(analysis.windows) == 3
        assert len(analysis.failure_reasons) == 0
    
    def test_validate_failing_low_sharpe(self, tmp_path):
        """Test validating a strategy that fails due to low test Sharpe."""
        windows = [
            WalkForwardWindow(0, 1577836800, 1593561600, 1593648000, 1601510400),
        ]
        
        # Create mock results with poor test Sharpe
        results = [
            WalkForwardResult(
                window_id=0,
                train_period=(1577836800, 1593561600),
                test_period=(1593648000, 1601510400),
                train_stats={"sharpe_ratio": 2.0, "total_return": 0.25},
                test_stats={"sharpe_ratio": 0.3, "total_return": 0.05},  # Low test Sharpe
                performance_degradation=-0.85,
                is_overfitting=True
            ),
        ]
        
        validator = WalkForwardValidator(
            num_windows=1,
            min_test_sharpe=0.5
        )
        analysis = validator.validate(windows=windows, results=results)
        
        assert analysis.passed is False
        assert len(analysis.failure_reasons) > 0
    
    def test_validate_failing_excessive_degradation(self, tmp_path):
        """Test validating a strategy that fails due to excessive degradation."""
        windows = [
            WalkForwardWindow(0, 1577836800, 1593561600, 1593648000, 1601510400),
        ]
        
        # Create mock results with excessive degradation
        results = [
            WalkForwardResult(
                window_id=0,
                train_period=(1577836800, 1593561600),
                test_period=(1593648000, 1601510400),
                train_stats={"sharpe_ratio": 2.0, "total_return": 0.25},
                test_stats={"sharpe_ratio": 1.0, "total_return": 0.12},  # 50% degradation
                performance_degradation=-0.5,
                is_overfitting=True
            ),
        ]
        
        validator = WalkForwardValidator(
            num_windows=1,
            max_degradation=0.3  # Max 30% degradation allowed
        )
        analysis = validator.validate(windows=windows, results=results)
        
        assert analysis.passed is False
        assert len(analysis.failure_reasons) > 0
    
    def test_validate_save_results(self, tmp_path):
        """Test that validation results can be saved to file."""
        windows = [
            WalkForwardWindow(0, 1577836800, 1593561600, 1593648000, 1601510400),
        ]
        
        results = [
            WalkForwardResult(
                window_id=0,
                train_period=(1577836800, 1593561600),
                test_period=(1593648000, 1601510400),
                train_stats={"sharpe_ratio": 2.0, "total_return": 0.25},
                test_stats={"sharpe_ratio": 1.8, "total_return": 0.22},
                performance_degradation=-0.1,
                is_overfitting=False
            ),
        ]
        
        output_path = tmp_path / "walk_forward_analysis.json"
        
        validator = WalkForwardValidator(num_windows=1)
        analysis = validator.validate(windows=windows, results=results)
        validator.save_analysis(analysis, output_path)
        
        # Check that output file was created
        assert output_path.exists()
        
        # Verify JSON content
        with open(output_path) as f:
            saved_analysis = json.load(f)
        
        assert saved_analysis["passed"] is True
        assert len(saved_analysis["windows"]) == 1


class TestWalkForwardResult:
    """Test WalkForwardResult dataclass."""
    
    def test_result_creation(self):
        """Test creating a walk-forward result."""
        result = WalkForwardResult(
            window_id=1,
            train_period=(1577836800, 1593561600),
            test_period=(1593648000, 1601510400),
            train_stats={"sharpe_ratio": 2.0, "total_return": 0.25},
            test_stats={"sharpe_ratio": 1.8, "total_return": 0.22},
            performance_degradation=-0.1,
            is_overfitting=False
        )
        
        assert result.window_id == 1
        assert result.train_stats["sharpe_ratio"] == 2.0
        assert result.test_stats["sharpe_ratio"] == 1.8
        assert result.performance_degradation == -0.1


class TestWalkForwardAnalysis:
    """Test WalkForwardAnalysis dataclass."""
    
    def test_analysis_creation(self):
        """Test creating a walk-forward analysis."""
        results = [
            WalkForwardResult(
                window_id=0,
                train_period=(1577836800, 1593561600),
                test_period=(1593648000, 1601510400),
                train_stats={"sharpe_ratio": 2.0, "total_return": 0.25},
                test_stats={"sharpe_ratio": 1.8, "total_return": 0.22},
                performance_degradation=-0.1,
                is_overfitting=False
            ),
            WalkForwardResult(
                window_id=1,
                train_period=(1593648000, 1609459200),
                test_period=(1609545600, 1617321600),
                train_stats={"sharpe_ratio": 2.1, "total_return": 0.26},
                test_stats={"sharpe_ratio": 1.9, "total_return": 0.23},
                performance_degradation=-0.095,
                is_overfitting=False
            ),
        ]
        
        analysis = WalkForwardAnalysis(
            windows=results,
            avg_train_sharpe=2.05,
            avg_test_sharpe=1.85,
            avg_degradation=-0.0975,
            stability_score=0.90,
            passed=True,
            failure_reasons=[]
        )
        
        assert analysis.passed is True
        assert len(analysis.windows) == 2
        assert analysis.avg_degradation == -0.0975
        assert analysis.stability_score == 0.90


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
