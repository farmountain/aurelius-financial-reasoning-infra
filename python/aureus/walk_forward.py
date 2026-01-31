"""Walk-forward validation module for out-of-sample testing."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd


@dataclass
class WalkForwardWindow:
    """Single window in walk-forward analysis."""
    
    train_start: int  # Timestamp
    train_end: int
    test_start: int
    test_end: int
    window_id: int


@dataclass
class WalkForwardResult:
    """Results from a single walk-forward window."""
    
    window_id: int
    train_period: tuple[int, int]  # (start, end) timestamps
    test_period: tuple[int, int]
    train_stats: Dict[str, float]
    test_stats: Dict[str, float]
    performance_degradation: float  # (test_sharpe - train_sharpe) / train_sharpe
    is_overfitting: bool


@dataclass
class WalkForwardAnalysis:
    """Complete walk-forward analysis results."""
    
    windows: List[WalkForwardResult]
    avg_train_sharpe: float
    avg_test_sharpe: float
    avg_degradation: float
    stability_score: float  # 1.0 = perfect, 0.0 = complete overfit
    passed: bool
    failure_reasons: List[str]


class WalkForwardValidator:
    """Implements walk-forward validation for strategy robustness testing."""
    
    def __init__(
        self,
        train_ratio: float = 0.7,
        test_ratio: float = 0.3,
        num_windows: int = 3,
        max_degradation: float = 0.3,  # 30% performance drop is acceptable
        min_test_sharpe: float = 0.5,
    ):
        """Initialize walk-forward validator.
        
        Args:
            train_ratio: Fraction of data for training (default: 70%)
            test_ratio: Fraction of data for testing (default: 30%)
            num_windows: Number of walk-forward windows (default: 3)
            max_degradation: Maximum acceptable performance degradation (default: 30%)
            min_test_sharpe: Minimum acceptable Sharpe ratio in test set (default: 0.5)
        """
        self.train_ratio = train_ratio
        self.test_ratio = test_ratio
        self.num_windows = num_windows
        self.max_degradation = max_degradation
        self.min_test_sharpe = min_test_sharpe
    
    def create_windows(self, data_path: str) -> List[WalkForwardWindow]:
        """Create walk-forward windows from data.
        
        Args:
            data_path: Path to data file (CSV or Parquet)
            
        Returns:
            List of WalkForwardWindow objects
        """
        # Load data to get timestamps
        if data_path.endswith('.parquet'):
            df = pd.read_parquet(data_path)
        else:
            df = pd.read_csv(data_path)
        
        timestamps = sorted(df['timestamp'].unique())
        total_length = len(timestamps)
        
        # Calculate window size
        window_size = total_length // self.num_windows
        train_size = int(window_size * self.train_ratio)
        test_size = int(window_size * self.test_ratio)
        
        windows = []
        for i in range(self.num_windows):
            start_idx = i * window_size
            train_end_idx = start_idx + train_size
            test_end_idx = min(train_end_idx + test_size, total_length)
            
            if train_end_idx >= total_length or test_end_idx > total_length:
                break
            
            windows.append(WalkForwardWindow(
                train_start=timestamps[start_idx],
                train_end=timestamps[train_end_idx - 1],
                test_start=timestamps[train_end_idx],
                test_end=timestamps[test_end_idx - 1],
                window_id=i + 1,
            ))
        
        return windows
    
    def split_data_by_window(
        self,
        data_path: str,
        window: WalkForwardWindow,
        output_dir: Path,
    ) -> tuple[Path, Path]:
        """Split data into train and test sets for a window.
        
        Args:
            data_path: Path to original data file
            window: Walk-forward window specification
            output_dir: Directory to save split data
            
        Returns:
            Tuple of (train_path, test_path)
        """
        # Load data
        if data_path.endswith('.parquet'):
            df = pd.read_parquet(data_path)
        else:
            df = pd.read_csv(data_path)
        
        # Split by timestamp
        train_df = df[
            (df['timestamp'] >= window.train_start) &
            (df['timestamp'] <= window.train_end)
        ]
        test_df = df[
            (df['timestamp'] >= window.test_start) &
            (df['timestamp'] <= window.test_end)
        ]
        
        # Save splits
        train_path = output_dir / f"train_window_{window.window_id}.parquet"
        test_path = output_dir / f"test_window_{window.window_id}.parquet"
        
        train_df.to_parquet(train_path, index=False)
        test_df.to_parquet(test_path, index=False)
        
        return train_path, test_path
    
    def analyze_window_results(
        self,
        window: WalkForwardWindow,
        train_stats: Dict[str, float],
        test_stats: Dict[str, float],
    ) -> WalkForwardResult:
        """Analyze results from a single walk-forward window.
        
        Args:
            window: Walk-forward window
            train_stats: Statistics from training period
            test_stats: Statistics from test period
            
        Returns:
            WalkForwardResult with analysis
        """
        train_sharpe = train_stats.get('sharpe_ratio', 0.0)
        test_sharpe = test_stats.get('sharpe_ratio', 0.0)
        
        # Calculate performance degradation
        if train_sharpe != 0:
            degradation = (test_sharpe - train_sharpe) / abs(train_sharpe)
        else:
            degradation = -1.0  # Complete failure if train Sharpe is 0
        
        # Check for overfitting
        is_overfitting = (
            degradation < -self.max_degradation or
            test_sharpe < self.min_test_sharpe
        )
        
        return WalkForwardResult(
            window_id=window.window_id,
            train_period=(window.train_start, window.train_end),
            test_period=(window.test_start, window.test_end),
            train_stats=train_stats,
            test_stats=test_stats,
            performance_degradation=degradation,
            is_overfitting=is_overfitting,
        )
    
    def validate(
        self,
        windows: List[WalkForwardWindow],
        results: List[WalkForwardResult],
    ) -> WalkForwardAnalysis:
        """Validate walk-forward results.
        
        Args:
            windows: List of walk-forward windows
            results: List of results for each window
            
        Returns:
            WalkForwardAnalysis with overall validation
        """
        if not results:
            return WalkForwardAnalysis(
                windows=[],
                avg_train_sharpe=0.0,
                avg_test_sharpe=0.0,
                avg_degradation=0.0,
                stability_score=0.0,
                passed=False,
                failure_reasons=["No walk-forward results to validate"],
            )
        
        # Calculate averages
        avg_train_sharpe = sum(r.train_stats['sharpe_ratio'] for r in results) / len(results)
        avg_test_sharpe = sum(r.test_stats['sharpe_ratio'] for r in results) / len(results)
        avg_degradation = sum(r.performance_degradation for r in results) / len(results)
        
        # Calculate stability score (1.0 = no degradation, 0.0 = 100% degradation)
        stability_score = max(0.0, 1.0 + avg_degradation)
        
        # Check for failures
        failure_reasons = []
        overfitting_count = sum(1 for r in results if r.is_overfitting)
        
        if overfitting_count > 0:
            failure_reasons.append(
                f"Overfitting detected in {overfitting_count}/{len(results)} windows"
            )
        
        if avg_test_sharpe < self.min_test_sharpe:
            failure_reasons.append(
                f"Average test Sharpe ({avg_test_sharpe:.3f}) below minimum ({self.min_test_sharpe})"
            )
        
        if avg_degradation < -self.max_degradation:
            failure_reasons.append(
                f"Average degradation ({avg_degradation:.1%}) exceeds maximum ({self.max_degradation:.1%})"
            )
        
        passed = len(failure_reasons) == 0
        
        return WalkForwardAnalysis(
            windows=results,
            avg_train_sharpe=avg_train_sharpe,
            avg_test_sharpe=avg_test_sharpe,
            avg_degradation=avg_degradation,
            stability_score=stability_score,
            passed=passed,
            failure_reasons=failure_reasons,
        )
    
    def save_analysis(
        self,
        analysis: WalkForwardAnalysis,
        output_path: Path,
    ) -> None:
        """Save walk-forward analysis to JSON file.
        
        Args:
            analysis: Walk-forward analysis results
            output_path: Path to save JSON file
        """
        data = {
            "passed": analysis.passed,
            "avg_train_sharpe": analysis.avg_train_sharpe,
            "avg_test_sharpe": analysis.avg_test_sharpe,
            "avg_degradation": analysis.avg_degradation,
            "stability_score": analysis.stability_score,
            "failure_reasons": analysis.failure_reasons,
            "windows": [
                {
                    "window_id": w.window_id,
                    "train_period": list(w.train_period),
                    "test_period": list(w.test_period),
                    "train_sharpe": w.train_stats["sharpe_ratio"],
                    "test_sharpe": w.test_stats["sharpe_ratio"],
                    "degradation": w.performance_degradation,
                    "is_overfitting": w.is_overfitting,
                }
                for w in analysis.windows
            ],
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
