"""
Unit tests for determinism primitive endpoint and scoring service.

Tests cover:
- Perfect determinism (score = 100)
- Slight variance (score 95-99)
- High variance (score < 95)
- Edge cases (2 runs, many runs, extreme values)
- Validation errors (single run, negative values, invalid threshold)
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from main import app
from services.determinism_scoring import (
    DeterminismScoringService,
    DeterminismScoreRequest,
    BacktestRun
)


client = TestClient(app)


# Test Data Fixtures
@pytest.fixture
def perfect_deterministic_runs():
    """Two identical backtest runs (perfect determinism)."""
    return [
        BacktestRun(
            run_id="run-1",
            timestamp=datetime.fromisoformat("2026-02-16T10:00:00"),
            total_return=0.15,
            sharpe_ratio=1.8,
            max_drawdown=0.12,
            trade_count=42,
            final_portfolio_value=115000.0,
            execution_time_ms=1250
        ),
        BacktestRun(
            run_id="run-2",
            timestamp=datetime.fromisoformat("2026-02-16T10:05:00"),
            total_return=0.15,
            sharpe_ratio=1.8,
            max_drawdown=0.12,
            trade_count=42,
            final_portfolio_value=115000.0,
            execution_time_ms=1230
        )
    ]


@pytest.fixture
def slight_variance_runs():
    """Runs with slight variance (score 95-99)."""
    return [
        BacktestRun(
            run_id="run-1",
            timestamp=datetime.fromisoformat("2026-02-16T10:00:00"),
            total_return=0.150,
            sharpe_ratio=1.80,
            max_drawdown=0.120,
            trade_count=42,
            final_portfolio_value=115000.0,
            execution_time_ms=1250
        ),
        BacktestRun(
            run_id="run-2",
            timestamp=datetime.fromisoformat("2026-02-16T10:05:00"),
            total_return=0.151,
            sharpe_ratio=1.81,
            max_drawdown=0.121,
            trade_count=42,
            final_portfolio_value=115050.0,
            execution_time_ms=1230
        )
    ]


@pytest.fixture
def high_variance_runs():
    """Runs with high variance (score < 95)."""
    return [
        BacktestRun(
            run_id="run-1",
            timestamp=datetime.fromisoformat("2026-02-16T10:00:00"),
            total_return=0.15,
            sharpe_ratio=1.8,
            max_drawdown=0.12,
            trade_count=42,
            final_portfolio_value=115000.0,
            execution_time_ms=1250
        ),
        BacktestRun(
            run_id="run-2",
            timestamp=datetime.fromisoformat("2026-02-16T10:05:00"),
            total_return=0.22,
            sharpe_ratio=2.1,
            max_drawdown=0.18,
            trade_count=38,
            final_portfolio_value=122000.0,
            execution_time_ms=1100
        )
    ]


@pytest.fixture
def varying_trade_count_runs():
    """Runs with identical metrics but different trade counts."""
    return [
        BacktestRun(
            run_id="run-1",
            timestamp=datetime.fromisoformat("2026-02-16T10:00:00"),
            total_return=0.15,
            sharpe_ratio=1.8,
            max_drawdown=0.12,
            trade_count=42,
            final_portfolio_value=115000.0,
            execution_time_ms=1250
        ),
        BacktestRun(
            run_id="run-2",
            timestamp=datetime.fromisoformat("2026-02-16T10:05:00"),
            total_return=0.15,
            sharpe_ratio=1.8,
            max_drawdown=0.12,
            trade_count=45,
            final_portfolio_value=115000.0,
            execution_time_ms=1230
        )
    ]


class TestDeterminismScoringService:
    """Unit tests for DeterminismScoringService."""
    
    def test_perfect_determinism(self, perfect_deterministic_runs):
        """Test perfect determinism returns score of 100."""
        request = DeterminismScoreRequest(
            strategy_id="test-strat",
            runs=perfect_deterministic_runs,
            threshold=95.0
        )
        
        result = DeterminismScoringService.score_determinism(request)
        
        assert result.score == 100.0
        assert result.passed is True
        assert result.confidence_interval > 0.9
        assert len(result.issues) == 0
        assert result.variance_metrics["total_return"] < 1e-10
        assert result.variance_metrics["trade_count"] == 0.0
    
    def test_slight_variance(self, slight_variance_runs):
        """Test slight variance returns score between 95-99."""
        request = DeterminismScoreRequest(
            strategy_id="test-strat",
            runs=slight_variance_runs,
            threshold=95.0
        )
        
        result = DeterminismScoringService.score_determinism(request)
        
        assert 95.0 <= result.score < 100.0
        assert result.passed is True
        assert result.confidence_interval > 0.8
    
    def test_high_variance_fails(self, high_variance_runs):
        """Test high variance returns score below threshold."""
        request = DeterminismScoreRequest(
            strategy_id="test-strat",
            runs=high_variance_runs,
            threshold=95.0
        )
        
        result = DeterminismScoringService.score_determinism(request)
        
        assert result.score < 95.0
        assert result.passed is False
        assert len(result.issues) > 0
        assert any("high variance" in issue.lower() for issue in result.issues)
    
    def test_varying_trade_count_detected(self, varying_trade_count_runs):
        """Test detection of varying trade counts."""
        request = DeterminismScoreRequest(
            strategy_id="test-strat",
            runs=varying_trade_count_runs,
            threshold=95.0
        )
        
        result = DeterminismScoringService.score_determinism(request)
        
        assert result.variance_metrics["trade_count"] > 0
        assert any("trade count" in issue.lower() for issue in result.issues)
    
    def test_multiple_runs(self, perfect_deterministic_runs):
        """Test scoring with more than 2 runs."""
        # Add a third identical run
        third_run = BacktestRun(
            run_id="run-3",
            timestamp=datetime.fromisoformat("2026-02-16T10:10:00"),
            total_return=0.15,
            sharpe_ratio=1.8,
            max_drawdown=0.12,
            trade_count=42,
            final_portfolio_value=115000.0,
            execution_time_ms=1260
        )
        
        request = DeterminismScoreRequest(
            strategy_id="test-strat",
            runs=perfect_deterministic_runs + [third_run],
            threshold=95.0
        )
        
        result = DeterminismScoringService.score_determinism(request)
        
        assert result.score == 100.0
        assert result.passed is True
    
    def test_custom_threshold(self, slight_variance_runs):
        """Test custom threshold parameter."""
        request = DeterminismScoreRequest(
            strategy_id="test-strat",
            runs=slight_variance_runs,
            threshold=99.0
        )
        
        result = DeterminismScoringService.score_determinism(request)
        
        # Slight variance should fail stricter threshold
        if result.score < 99.0:
            assert result.passed is False
    
    def test_negative_returns(self):
        """Test handling of negative returns."""
        runs = [
            BacktestRun(
                run_id="run-1",
                timestamp=datetime.fromisoformat("2026-02-16T10:00:00"),
                total_return=-0.10,
                sharpe_ratio=-0.5,
                max_drawdown=0.25,
                trade_count=30,
                final_portfolio_value=90000.0,
                execution_time_ms=1200
            ),
            BacktestRun(
                run_id="run-2",
                timestamp=datetime.fromisoformat("2026-02-16T10:05:00"),
                total_return=-0.10,
                sharpe_ratio=-0.5,
                max_drawdown=0.25,
                trade_count=30,
                final_portfolio_value=90000.0,
                execution_time_ms=1210
            )
        ]
        
        request = DeterminismScoreRequest(
            strategy_id="test-strat",
            runs=runs,
            threshold=95.0
        )
        
        result = DeterminismScoringService.score_determinism(request)
        
        assert result.score == 100.0
        assert result.passed is True
    
    def test_extreme_variance(self):
        """Test extreme variance between runs."""
        runs = [
            BacktestRun(
                run_id="run-1",
                timestamp=datetime.fromisoformat("2026-02-16T10:00:00"),
                total_return=0.50,
                sharpe_ratio=3.0,
                max_drawdown=0.05,
                trade_count=100,
                final_portfolio_value=150000.0,
                execution_time_ms=2000
            ),
            BacktestRun(
                run_id="run-2",
                timestamp=datetime.fromisoformat("2026-02-16T10:05:00"),
                total_return=-0.30,
                sharpe_ratio=-1.5,
                max_drawdown=0.40,
                trade_count=20,
                final_portfolio_value=70000.0,
                execution_time_ms=800
            )
        ]
        
        request = DeterminismScoreRequest(
            strategy_id="test-strat",
            runs=runs,
            threshold=95.0
        )
        
        result = DeterminismScoringService.score_determinism(request)
        
        assert result.score < 50.0
        assert result.passed is False
        assert len(result.issues) > 2  # Should detect multiple issues
    
    def test_validation_min_runs(self):
        """Test validation requires at least 2 runs."""
        with pytest.raises(ValueError):
            DeterminismScoreRequest(
                strategy_id="test-strat",
                runs=[
                    BacktestRun(
                        run_id="run-1",
                        timestamp=datetime.fromisoformat("2026-02-16T10:00:00"),
                        total_return=0.15,
                        sharpe_ratio=1.8,
                        max_drawdown=0.12,
                        trade_count=42,
                        final_portfolio_value=115000.0,
                        execution_time_ms=1250
                    )
                ],
                threshold=95.0
            )
    
    def test_validation_threshold_range(self):
        """Test validation of threshold range (0-100)."""
        with pytest.raises(ValueError):
            DeterminismScoreRequest(
                strategy_id="test-strat",
                runs=[],
                threshold=150.0  # Invalid: > 100
            )
        
        with pytest.raises(ValueError):
            DeterminismScoreRequest(
                strategy_id="test-strat",
                runs=[],
                threshold=-10.0  # Invalid: < 0
            )


class TestDeterminismEndpoint:
    """Integration tests for /api/primitives/v1/determinism/score endpoint."""
    
    def test_endpoint_requires_authentication(self):
        """Test endpoint requires authentication."""
        response = client.post(
            "/api/primitives/v1/determinism/score",
            json={
                "strategy_id": "test-strat",
                "runs": [],
                "threshold": 95.0
            }
        )
        
        assert response.status_code == 401
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/api/primitives/v1/determinism/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
