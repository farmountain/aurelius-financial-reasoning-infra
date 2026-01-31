"""
Tests for advanced strategy templates.
"""

import pytest
from aureus.llm_strategy_generator import LLMStrategyGenerator, LLMConfig
from aureus.tools.schemas import StrategyConfig


class TestAdvancedStrategyTemplates:
    """Test advanced strategy template generation."""
    
    def test_pairs_trading_template(self):
        """Test pairs trading strategy generation."""
        generator = LLMStrategyGenerator(LLMConfig(provider="none"))
        
        goal = "Create a pairs trading strategy between AAPL and MSFT"
        constraints = {
            "strategy_type": "pairs_trading",
            "risk_preference": "moderate"
        }
        
        strategy = generator.generate(goal, constraints, use_llm=False)
        
        assert strategy.type == "pairs_trading"
        assert strategy.symbol == "AAPL"
        assert hasattr(strategy, "secondary_symbol")
        assert strategy.secondary_symbol == "MSFT"
        assert hasattr(strategy, "entry_zscore")
        assert hasattr(strategy, "exit_zscore")
        assert hasattr(strategy, "hedge_ratio_method")
        assert strategy.hedge_ratio_method == "ols"
    
    def test_pairs_trading_from_goal_text(self):
        """Test pairs trading detection from goal text."""
        generator = LLMStrategyGenerator(LLMConfig(provider="none"))
        
        goal = "I want to trade pairs between tech stocks"
        constraints = {"risk_preference": "conservative"}
        
        strategy = generator.generate(goal, constraints, use_llm=False)
        
        assert strategy.type == "pairs_trading"
        assert hasattr(strategy, "entry_zscore")
        # Conservative risk should have higher entry zscore
        assert strategy.entry_zscore >= 1.4  # 2.0 * 0.7
    
    def test_stat_arb_template(self):
        """Test statistical arbitrage strategy generation."""
        generator = LLMStrategyGenerator(LLMConfig(provider="none"))
        
        goal = "Design a statistical arbitrage strategy"
        constraints = {
            "strategy_type": "stat_arb",
            "risk_preference": "moderate"
        }
        
        strategy = generator.generate(goal, constraints, use_llm=False)
        
        assert strategy.type == "stat_arb"
        assert strategy.symbol == "SPY"
        assert hasattr(strategy, "basket")
        assert isinstance(strategy.basket, list)
        assert len(strategy.basket) == 3
        assert hasattr(strategy, "cointegration_test")
        assert strategy.cointegration_test == "adf"
        assert hasattr(strategy, "hedge_ratio_method")
        assert strategy.hedge_ratio_method == "johansen"
    
    def test_stat_arb_from_goal_text(self):
        """Test stat arb detection from goal text."""
        generator = LLMStrategyGenerator(LLMConfig(provider="none"))
        
        goal = "Build an arbitrage strategy using statistical methods"
        constraints = {"risk_preference": "aggressive"}
        
        strategy = generator.generate(goal, constraints, use_llm=False)
        
        assert strategy.type == "stat_arb"
        assert hasattr(strategy, "entry_threshold")
        # Aggressive should have higher threshold (1.5x multiplier)
        assert strategy.entry_threshold >= 3.0  # 2.0 * 1.5
    
    def test_ml_classifier_template(self):
        """Test ML classifier strategy generation."""
        generator = LLMStrategyGenerator(LLMConfig(provider="none"))
        
        goal = "Create a machine learning classifier for trading"
        constraints = {
            "strategy_type": "ml_classifier",
            "risk_preference": "moderate"
        }
        
        strategy = generator.generate(goal, constraints, use_llm=False)
        
        assert strategy.type == "ml_classifier"
        assert hasattr(strategy, "num_features")
        assert strategy.num_features == 15  # 15 * 1.0
        assert hasattr(strategy, "model_type")
        assert strategy.model_type == "random_forest"
        assert hasattr(strategy, "retrain_frequency")
        assert strategy.retrain_frequency == 20
        assert hasattr(strategy, "feature_set")
        assert strategy.feature_set == "technical"
        assert hasattr(strategy, "target_variable")
        assert strategy.target_variable == "forward_return"
    
    def test_ml_from_goal_text(self):
        """Test ML detection from goal text."""
        generator = LLMStrategyGenerator(LLMConfig(provider="none"))
        
        goal = "I want to use ML to predict returns"
        constraints = {"risk_preference": "conservative"}
        
        strategy = generator.generate(goal, constraints, use_llm=False)
        
        assert strategy.type == "ml_classifier"
        assert hasattr(strategy, "num_features")
        # Conservative should have fewer features
        assert strategy.num_features <= 11  # 15 * 0.7
    
    def test_carry_trade_template(self):
        """Test carry trade strategy generation."""
        generator = LLMStrategyGenerator(LLMConfig(provider="none"))
        
        goal = "Design a carry trade strategy"
        constraints = {
            "strategy_type": "carry_trade",
            "risk_preference": "moderate"
        }
        
        strategy = generator.generate(goal, constraints, use_llm=False)
        
        assert strategy.type == "carry_trade"
        assert strategy.symbol == "FX_EURUSD"
        assert hasattr(strategy, "min_carry")
        assert strategy.min_carry == 0.02
        assert hasattr(strategy, "vol_target")
        assert strategy.vol_target == 0.15
        assert hasattr(strategy, "rebalance_frequency")
        assert strategy.rebalance_frequency == 5
    
    def test_carry_from_goal_text(self):
        """Test carry trade detection from goal text."""
        generator = LLMStrategyGenerator(LLMConfig(provider="none"))
        
        goal = "Trade interest rate differentials in FX markets"
        constraints = {"risk_preference": "aggressive"}
        
        strategy = generator.generate(goal, constraints, use_llm=False)
        
        assert strategy.type == "carry_trade"
        assert hasattr(strategy, "vol_target")
        # Aggressive should have higher vol target
        assert strategy.vol_target >= 0.25
    
    def test_volatility_trading_template(self):
        """Test volatility trading strategy generation."""
        generator = LLMStrategyGenerator(LLMConfig(provider="none"))
        
        goal = "Create a volatility trading strategy"
        constraints = {
            "strategy_type": "volatility_trading",
            "risk_preference": "moderate"
        }
        
        strategy = generator.generate(goal, constraints, use_llm=False)
        
        assert strategy.type == "volatility_trading"
        assert strategy.symbol == "SPY"
        assert hasattr(strategy, "options_chain")
        assert strategy.options_chain == "SPY_OPTIONS"
        assert hasattr(strategy, "target_delta")
        assert strategy.target_delta == 0.25  # 0.25 * 1.0
        assert hasattr(strategy, "vol_forecast_method")
        assert strategy.vol_forecast_method == "ewma"
        assert hasattr(strategy, "hedge_type")
        assert strategy.hedge_type == "delta"
    
    def test_vol_from_goal_text(self):
        """Test volatility trading detection from goal text."""
        generator = LLMStrategyGenerator(LLMConfig(provider="none"))
        
        goal = "I want to trade vol on SPY using options"
        constraints = {"risk_preference": "conservative"}
        
        strategy = generator.generate(goal, constraints, use_llm=False)
        
        assert strategy.type == "volatility_trading"
        assert hasattr(strategy, "target_delta")
        # Conservative should have lower delta
        assert strategy.target_delta <= 0.175  # 0.25 * 0.7
    
    def test_risk_preference_adjustments(self):
        """Test that risk preferences adjust parameters correctly."""
        generator = LLMStrategyGenerator(LLMConfig(provider="none"))
        
        # Conservative
        conservative = generator.generate(
            "momentum strategy",
            {"strategy_type": "momentum", "risk_preference": "conservative"},
            use_llm=False
        )
        
        # Moderate
        moderate = generator.generate(
            "momentum strategy",
            {"strategy_type": "momentum", "risk_preference": "moderate"},
            use_llm=False
        )
        
        # Aggressive
        aggressive = generator.generate(
            "momentum strategy",
            {"strategy_type": "momentum", "risk_preference": "aggressive"},
            use_llm=False
        )
        
        # Conservative should have:
        # - Lower vol target
        # - Longer lookback
        assert conservative.vol_target < moderate.vol_target < aggressive.vol_target
        assert conservative.lookback > moderate.lookback > aggressive.lookback
    
    def test_default_strategy_fallback(self):
        """Test that unknown strategy types fall back to momentum."""
        generator = LLMStrategyGenerator(LLMConfig(provider="none"))
        
        strategy = generator.generate(
            "unknown strategy type",
            {"strategy_type": "unknown_type"},
            use_llm=False
        )
        
        # Should fall back to momentum
        assert strategy.type == "ts_momentum"
        assert hasattr(strategy, "lookback")
        assert hasattr(strategy, "vol_target")


class TestStrategyConfigFlexibility:
    """Test that StrategyConfig can handle all new strategy types."""
    
    def test_pairs_trading_config(self):
        """Test creating pairs trading config directly."""
        config = StrategyConfig(
            type="pairs_trading",
            symbol="AAPL",
            secondary_symbol="MSFT",
            entry_zscore=2.0,
            exit_zscore=0.5,
            hedge_ratio_method="ols"
        )
        
        assert config.type == "pairs_trading"
        assert config.secondary_symbol == "MSFT"
    
    def test_stat_arb_config(self):
        """Test creating stat arb config directly."""
        config = StrategyConfig(
            type="stat_arb",
            symbol="SPY",
            basket=["QQQ", "IWM", "DIA"],
            cointegration_test="adf"
        )
        
        assert config.type == "stat_arb"
        assert len(config.basket) == 3
    
    def test_ml_classifier_config(self):
        """Test creating ML classifier config directly."""
        config = StrategyConfig(
            type="ml_classifier",
            symbol="AAPL",
            model_type="random_forest",
            num_features=15,
            feature_set="technical"
        )
        
        assert config.type == "ml_classifier"
        assert config.model_type == "random_forest"
    
    def test_carry_trade_config(self):
        """Test creating carry trade config directly."""
        config = StrategyConfig(
            type="carry_trade",
            symbol="FX_EURUSD",
            min_carry=0.02,
            rebalance_frequency=5
        )
        
        assert config.type == "carry_trade"
        assert config.min_carry == 0.02
    
    def test_volatility_trading_config(self):
        """Test creating volatility trading config directly."""
        config = StrategyConfig(
            type="volatility_trading",
            symbol="SPY",
            options_chain="SPY_OPTIONS",
            target_delta=0.25,
            hedge_type="delta"
        )
        
        assert config.type == "volatility_trading"
        assert config.hedge_type == "delta"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
