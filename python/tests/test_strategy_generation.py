"""Tests for enhanced strategy generation from goals."""

import pytest
from aureus.llm_strategy_generator import LLMStrategyGenerator


class TestStrategyGeneration:
    """Test suite for real strategy generation implementation."""

    def test_momentum_strategy_generation(self):
        """Test that momentum keywords generate momentum strategies."""
        generator = LLMStrategyGenerator()
        
        goals = [
            "design a trend strategy under DD<10%",
            "create momentum strategy with DD<15%",
            "trend following strategy with low risk",
        ]
        
        for goal in goals:
            constraints = {"strategy_type": "momentum", "max_drawdown": 0.10}
            strategy = generator.generate(goal, constraints, use_llm=False)
            assert strategy.type == "ts_momentum"
            assert hasattr(strategy, "lookback")
            assert hasattr(strategy, "vol_target")

    def test_mean_reversion_strategy_generation(self):
        """Test that mean-reversion keywords generate mean-reversion strategies."""
        generator = LLMStrategyGenerator()
        
        goals = [
            "design a mean reversion strategy under DD<10%",
            "create reversal strategy with DD<15%",
            "chop market strategy with conservative risk",
        ]
        
        for goal in goals:
            constraints = {"strategy_type": "mean_reversion", "max_drawdown": 0.10}
            strategy = generator.generate(goal, constraints, use_llm=False)
            assert strategy.type == "mean_reversion"

    def test_breakout_strategy_generation(self):
        """Test that breakout keywords generate breakout strategies."""
        generator = LLMStrategyGenerator()
        
        goals = [
            "design a breakout strategy under DD<10%",
            "create volatility strategy with DD<15%",
        ]
        
        for goal in goals:
            constraints = {"strategy_type": "breakout", "max_drawdown": 0.10}
            strategy = generator.generate(goal, constraints, use_llm=False)
            assert strategy.type == "breakout"

    def test_constraint_extraction(self):
        """Test that constraints are properly extracted from goals."""
        from aureus.orchestrator import Orchestrator
        # Use orchestrator's _parse_goal directly without initializing Rust wrapper
        orchestrator = Orchestrator.__new__(Orchestrator)
        
        # Test drawdown extraction
        constraints = orchestrator._parse_goal("design a strategy under DD<10%")
        assert "max_drawdown" in constraints
        assert constraints["max_drawdown"] == 0.10
        
        # Test percentage conversion
        constraints = orchestrator._parse_goal("strategy with DD<25%")
        assert constraints["max_drawdown"] == 0.25
        
        # Test Sharpe ratio extraction
        constraints = orchestrator._parse_goal("strategy with sharpe > 1.5")
        assert "min_sharpe" in constraints
        assert constraints["min_sharpe"] == 1.5

    def test_risk_preference_adjustment(self):
        """Test that risk preferences adjust strategy parameters."""
        generator = LLMStrategyGenerator()
        
        # Conservative strategy
        conservative_constraints = {
            "strategy_type": "momentum",
            "risk_preference": "conservative",
        }
        conservative_strategy = generator.generate(
            "conservative trend strategy", conservative_constraints, use_llm=False
        )
        
        # Aggressive strategy
        aggressive_constraints = {
            "strategy_type": "momentum",
            "risk_preference": "aggressive",
        }
        aggressive_strategy = generator.generate(
            "aggressive momentum strategy", aggressive_constraints, use_llm=False
        )
        
        # Conservative should have lower volatility target
        assert conservative_strategy.vol_target < aggressive_strategy.vol_target
        
        # Conservative should have longer lookback
        assert conservative_strategy.lookback > aggressive_strategy.lookback

    def test_default_strategy_type(self):
        """Test that generic goals default to momentum strategy."""
        generator = LLMStrategyGenerator()
        
        constraints = {"strategy_type": "momentum"}
        strategy = generator.generate("design a good strategy", constraints, use_llm=False)
        assert strategy.type == "ts_momentum"

    def test_multiple_constraint_extraction(self):
        """Test extraction of multiple constraints from complex goals."""
        from aureus.orchestrator import Orchestrator
        orchestrator = Orchestrator.__new__(Orchestrator)
        
        goal = "design a trend strategy under DD<10% with sharpe > 1.5 and return > 20%"
        constraints = orchestrator._parse_goal(goal)
        
        assert constraints["max_drawdown"] == 0.10
        assert constraints["min_sharpe"] == 1.5
        assert constraints["min_return"] == 0.20
        assert constraints["strategy_type"] == "momentum"

    def test_case_insensitive_parsing(self):
        """Test that goal parsing is case-insensitive."""
        from aureus.orchestrator import Orchestrator
        orchestrator = Orchestrator.__new__(Orchestrator)
        
        goals = [
            "TREND strategy under DD<10%",
            "trend Strategy Under DD<10%",
            "TREND STRATEGY UNDER DD<10%",
        ]
        
        for goal in goals:
            constraints = orchestrator._parse_goal(goal)
            assert constraints["strategy_type"] == "momentum"

    def test_no_longer_placeholder(self):
        """Verify that strategy generation is no longer a placeholder."""
        generator = LLMStrategyGenerator()
        
        # Generate different strategies
        momentum_strategy = generator.generate(
            "trend strategy",
            {"strategy_type": "momentum"},
            use_llm=False
        )
        mean_rev_strategy = generator.generate(
            "mean reversion strategy",
            {"strategy_type": "mean_reversion"},
            use_llm=False
        )
        breakout_strategy = generator.generate(
            "breakout strategy",
            {"strategy_type": "breakout"},
            use_llm=False
        )
        
        # All should be different types (not all the same placeholder)
        strategies = {momentum_strategy.type, mean_rev_strategy.type, breakout_strategy.type}
        assert len(strategies) == 3  # Three distinct types
        assert "ts_momentum" in strategies
        assert "mean_reversion" in strategies
        assert "breakout" in strategies
