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
        "date": [d.strftime("%Y-%m-%d") for d in dates],
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
            train_start=datetime(2020, 1, 1),
            train_end=datetime(2020, 6, 30),
            test_start=datetime(2020, 7, 1),
            test_end=datetime(2020, 9, 30)
        )
        
        assert window.window_id == 1
        assert window.train_start == datetime(2020, 1, 1)
        assert window.test_end == datetime(2020, 9, 30)
    
    def test_window_to_dict(self):
        """Test converting window to dictionary."""
        window = WalkForwardWindow(
            window_id=1,
            train_start=datetime(2020, 1, 1),
            train_end=datetime(2020, 6, 30),
            test_start=datetime(2020, 7, 1),
            test_end=datetime(2020, 9, 30)
        )
        
        d = window.to_dict()
        assert d["window_id"] == 1
        assert d["train_start"] == "2020-01-01"
        assert d["test_end"] == "2020-09-30"


class TestWalkForwardValidator:
    """Test WalkForwardValidator class."""
    
    def test_validator_creation(self):
        """Test creating a validator."""
        validator = WalkForwardValidator(num_windows=3)
        
        assert validator.num_windows == 3
        assert validator.min_test_sharpe == 0.5
        assert validator.max_sharpe_degradation == 0.3
    
    def test_validator_custom_params(self):
        """Test creating validator with custom parameters."""
        validator = WalkForwardValidator(
            num_windows=5,
            min_test_sharpe=1.0,
            max_sharpe_degradation=0.2
        )
        
        assert validator.num_windows == 5
        assert validator.min_test_sharpe == 1.0
        assert validator.max_sharpe_degradation == 0.2
    
    def test_create_windows(self, tmp_path):
        """Test creating walk-forward windows from data."""
        # Create mock data file with 365 days
        data_path = create_mock_data_file(tmp_path, num_days=365)
        
        validator = WalkForwardValidator(num_windows=3)
        windows = validator.create_windows(str(data_path))
        
        # Should create 3 windows
        assert len(windows) == 3
        
        # Check window IDs
        assert windows[0].window_id == 0
        assert windows[1].window_id == 1
        assert windows[2].window_id == 2
        
        # Check that train/test periods don't overlap
        for window in windows:
            assert window.train_start < window.train_end
            assert window.test_start < window.test_end
            assert window.train_end <= window.test_start
    
    def test_create_windows_insufficient_data(self, tmp_path):
        """Test that insufficient data raises an error."""
        # Create mock data file with only 100 days (not enough)
        data_path = create_mock_data_file(tmp_path, num_days=100)
        
        validator = WalkForwardValidator(num_windows=3)
        
        with pytest.raises(ValueError, match="Insufficient data"):
            validator.create_windows(str(data_path))
    
    def test_validate_passing_strategy(self, tmp_path):
        """Test validating a strategy that passes all criteria."""
        # Create mock data and results
        data_path = create_mock_data_file(tmp_path, num_days=365)
        
        # Create mock backtest results with good Sharpe ratios
        train_results = []
        test_results = []
        
        for i in range(3):
            train_result = create_mock_backtest_result(
                tmp_path / f"train_{i}",
                sharpe=2.0,  # Good train Sharpe
                total_return=0.25
            )
            test_result = create_mock_backtest_result(
                tmp_path / f"test_{i}",
                sharpe=1.8,  # Good test Sharpe (slight degradation)
                total_return=0.22
            )
            
            train_results.append(str(train_result))
            test_results.append(str(test_result))
        
        validator = WalkForwardValidator(num_windows=3)
        analysis = validator.validate(
            data_path=str(data_path),
            train_results=train_results,
            test_results=test_results
        )
        
        assert analysis.passed is True
        assert len(analysis.window_results) == 3
        assert "All validation checks passed" in analysis.summary
    
    def test_validate_failing_low_sharpe(self, tmp_path):
        """Test validating a strategy that fails due to low test Sharpe."""
        data_path = create_mock_data_file(tmp_path, num_days=365)
        
        # Create mock backtest results with poor test Sharpe
        train_results = []
        test_results = []
        
        for i in range(3):
            train_result = create_mock_backtest_result(
                tmp_path / f"train_{i}",
                sharpe=2.0,
                total_return=0.25
            )
            test_result = create_mock_backtest_result(
                tmp_path / f"test_{i}",
                sharpe=0.3,  # Low test Sharpe (below threshold)
                total_return=0.05
            )
            
            train_results.append(str(train_result))
            test_results.append(str(test_result))
        
        validator = WalkForwardValidator(
            num_windows=3,
            min_test_sharpe=0.5
        )
        analysis = validator.validate(
            data_path=str(data_path),
            train_results=train_results,
            test_results=test_results
        )
        
        assert analysis.passed is False
        assert "Failed" in analysis.summary
    
    def test_validate_failing_excessive_degradation(self, tmp_path):
        """Test validating a strategy that fails due to excessive degradation."""
        data_path = create_mock_data_file(tmp_path, num_days=365)
        
        # Create mock backtest results with excessive degradation
        train_results = []
        test_results = []
        
        for i in range(3):
            train_result = create_mock_backtest_result(
                tmp_path / f"train_{i}",
                sharpe=2.0,  # Good train Sharpe
                total_return=0.25
            )
            test_result = create_mock_backtest_result(
                tmp_path / f"test_{i}",
                sharpe=1.0,  # Test Sharpe drops too much (50% degradation)
                total_return=0.12
            )
            
            train_results.append(str(train_result))
            test_results.append(str(test_result))
        
        validator = WalkForwardValidator(
            num_windows=3,
            max_sharpe_degradation=0.3  # Max 30% degradation allowed
        )
        analysis = validator.validate(
            data_path=str(data_path),
            train_results=train_results,
            test_results=test_results
        )
        
        assert analysis.passed is False
        assert "excessive degradation" in analysis.summary.lower()
    
    def test_validate_save_results(self, tmp_path):
        """Test that validation results can be saved to file."""
        data_path = create_mock_data_file(tmp_path, num_days=365)
        
        train_results = []
        test_results = []
        
        for i in range(3):
            train_result = create_mock_backtest_result(
                tmp_path / f"train_{i}",
                sharpe=2.0,
                total_return=0.25
            )
            test_result = create_mock_backtest_result(
                tmp_path / f"test_{i}",
                sharpe=1.8,
                total_return=0.22
            )
            
            train_results.append(str(train_result))
            test_results.append(str(test_result))
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        validator = WalkForwardValidator(num_windows=3)
        analysis = validator.validate(
            data_path=str(data_path),
            train_results=train_results,
            test_results=test_results,
            output_dir=str(output_dir)
        )
        
        # Check that output files were created
        assert (output_dir / "walk_forward_analysis.json").exists()
        assert (output_dir / "walk_forward_summary.txt").exists()
        
        # Verify JSON content
        with open(output_dir / "walk_forward_analysis.json") as f:
            saved_analysis = json.load(f)
        
        assert saved_analysis["passed"] is True
        assert len(saved_analysis["window_results"]) == 3


class TestWalkForwardResult:
    """Test WalkForwardResult dataclass."""
    
    def test_result_creation(self):
        """Test creating a walk-forward result."""
        result = WalkForwardResult(
            window_id=1,
            train_sharpe=2.0,
            test_sharpe=1.8,
            degradation=0.1,
            train_return=0.25,
            test_return=0.22
        )
        
        assert result.window_id == 1
        assert result.train_sharpe == 2.0
        assert result.test_sharpe == 1.8
        assert result.degradation == 0.1
    
    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = WalkForwardResult(
            window_id=1,
            train_sharpe=2.0,
            test_sharpe=1.8,
            degradation=0.1,
            train_return=0.25,
            test_return=0.22
        )
        
        d = result.to_dict()
        assert d["window_id"] == 1
        assert d["train_sharpe"] == 2.0
        assert d["test_sharpe"] == 1.8


class TestWalkForwardAnalysis:
    """Test WalkForwardAnalysis dataclass."""
    
    def test_analysis_creation(self):
        """Test creating a walk-forward analysis."""
        results = [
            WalkForwardResult(0, 2.0, 1.8, 0.1, 0.25, 0.22),
            WalkForwardResult(1, 2.1, 1.9, 0.095, 0.26, 0.23),
        ]
        
        analysis = WalkForwardAnalysis(
            passed=True,
            window_results=results,
            avg_degradation=0.0975,
            stability_score=0.95,
            summary="All checks passed"
        )
        
        assert analysis.passed is True
        assert len(analysis.window_results) == 2
        assert analysis.avg_degradation == 0.0975
        assert analysis.stability_score == 0.95
    
    def test_analysis_to_dict(self):
        """Test converting analysis to dictionary."""
        results = [
            WalkForwardResult(0, 2.0, 1.8, 0.1, 0.25, 0.22),
        ]
        
        analysis = WalkForwardAnalysis(
            passed=True,
            window_results=results,
            avg_degradation=0.1,
            stability_score=0.95,
            summary="Passed"
        )
        
        d = analysis.to_dict()
        assert d["passed"] is True
        assert len(d["window_results"]) == 1
        assert d["avg_degradation"] == 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
