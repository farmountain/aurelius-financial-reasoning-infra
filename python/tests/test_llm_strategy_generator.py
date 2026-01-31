"""Tests for LLM-assisted strategy generation."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from aureus.llm_strategy_generator import (
    LLMStrategyGenerator,
    LLMConfig,
)
from aureus.tools.schemas import StrategyConfig


class TestLLMConfig:
    """Tests for LLM configuration."""
    
    def test_default_config(self):
        """Test default configuration has no LLM."""
        config = LLMConfig()
        assert config.provider == "none"
        assert config.api_key is None
    
    def test_openai_config_from_env(self):
        """Test OpenAI config from environment."""
        with patch.dict("os.environ", {
            "OPENAI_API_KEY": "sk-test-key",
            "OPENAI_MODEL": "gpt-4-turbo",
        }):
            config = LLMConfig.from_env("openai")
            assert config.provider == "openai"
            assert config.api_key == "sk-test-key"
            assert config.model == "gpt-4-turbo"
    
    def test_anthropic_config_from_env(self):
        """Test Anthropic config from environment."""
        with patch.dict("os.environ", {
            "ANTHROPIC_API_KEY": "sk-ant-test-key",
        }):
            config = LLMConfig.from_env("anthropic")
            assert config.provider == "anthropic"
            assert config.api_key == "sk-ant-test-key"
            assert "claude" in config.model


class TestLLMStrategyGenerator:
    """Tests for LLM strategy generator."""
    
    def test_template_fallback_with_no_llm(self):
        """Test that template generation works when no LLM configured."""
        generator = LLMStrategyGenerator()
        
        goal = "design a trend strategy under DD<10%"
        constraints = {"strategy_type": "momentum", "max_drawdown": 0.10}
        
        strategy = generator.generate(goal, constraints, use_llm=True)
        
        assert strategy.type == "ts_momentum"
        assert hasattr(strategy, "lookback")
        assert not generator.is_llm_available
    
    def test_extract_json_from_clean_response(self):
        """Test extracting JSON from clean LLM response."""
        generator = LLMStrategyGenerator()
        
        json_text = '{"type": "ts_momentum", "symbol": "AAPL"}'
        result = generator._extract_json(json_text)
        
        assert result is not None
        assert result["type"] == "ts_momentum"
        assert result["symbol"] == "AAPL"
    
    def test_extract_json_from_markdown(self):
        """Test extracting JSON from markdown code block."""
        generator = LLMStrategyGenerator()
        
        markdown_text = '''```json
{
    "type": "mean_reversion",
    "symbol": "AAPL",
    "parameters": {
        "lookback": 20
    }
}
```'''
        result = generator._extract_json(markdown_text)
        
        assert result is not None
        assert result["type"] == "mean_reversion"
    
    def test_extract_json_from_mixed_text(self):
        """Test extracting JSON from text with surrounding content."""
        generator = LLMStrategyGenerator()
        
        mixed_text = 'Here is the strategy: {"type": "breakout", "symbol": "AAPL"} as you requested.'
        result = generator._extract_json(mixed_text)
        
        assert result is not None
        assert result["type"] == "breakout"
    
    def test_json_to_strategy_config(self):
        """Test converting LLM JSON to StrategyConfig."""
        generator = LLMStrategyGenerator()
        
        strategy_json = {
            "type": "ts_momentum",
            "symbol": "AAPL",
            "reasoning": "Trend-following strategy for this goal",
            "parameters": {
                "lookback": 30,
                "vol_target": 0.12,
                "vol_lookback": 90,
            }
        }
        
        config = generator._json_to_strategy_config(strategy_json, "test goal")
        
        assert config.type == "ts_momentum"
        assert config.symbol == "AAPL"
        assert config.lookback == 30
        assert config.vol_target == 0.12
    
    def test_openai_generation_success(self):
        """Test successful OpenAI strategy generation (mock)."""
        try:
            import openai
        except ImportError:
            pytest.skip("openai not installed, skipping OpenAI-specific test")
        
        # Mock directly without patch since openai is dynamically imported
        mock_client = Mock()
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "type": "ts_momentum",
            "symbol": "AAPL",
            "reasoning": "Momentum strategy for trending markets",
            "parameters": {
                "lookback": 25,
                "vol_target": 0.15,
                "vol_lookback": 75,
            }
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create generator with OpenAI config
        config = LLMConfig(
            provider="openai",
            api_key="sk-test-key",
            model="gpt-4",
        )
        generator = LLMStrategyGenerator(config)
        generator._client = mock_client  # Inject mock
        
        # Generate strategy
        goal = "design a momentum strategy"
        constraints = {"strategy_type": "momentum"}
        strategy = generator._generate_with_llm(goal, constraints)
        
        assert strategy is not None
        assert strategy.type == "ts_momentum"
        assert strategy.lookback == 25
    
    def test_anthropic_generation_success(self):
        """Test successful Anthropic strategy generation (mock)."""
        try:
            import anthropic
        except ImportError:
            pytest.skip("anthropic not installed, skipping Anthropic-specific test")
        
        # Mock directly without patch since anthropic is dynamically imported
        mock_client = Mock()
        
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "type": "mean_reversion",
            "symbol": "AAPL",
            "reasoning": "Mean reversion for range-bound markets",
            "parameters": {
                "lookback": 20,
                "num_std": 2.0,
                "reversion_threshold": 0.5,
            }
        })
        mock_client.messages.create.return_value = mock_response
        
        # Create generator with Anthropic config
        config = LLMConfig(
            provider="anthropic",
            api_key="sk-ant-test-key",
            model="claude-3-5-sonnet-20241022",
        )
        generator = LLMStrategyGenerator(config)
        generator._client = mock_client  # Inject mock
        
        # Generate strategy
        goal = "design a mean reversion strategy"
        constraints = {"strategy_type": "mean_reversion"}
        strategy = generator._generate_with_llm(goal, constraints)
        
        assert strategy is not None
        assert strategy.type == "mean_reversion"
    
    def test_llm_failure_fallback_to_template(self):
        """Test that LLM failures gracefully fallback to templates."""
        # Create generator with broken client
        config = LLMConfig(
            provider="openai",
            api_key="sk-test-key",
            model="gpt-4",
        )
        generator = LLMStrategyGenerator(config)
        
        # Mock client that raises error
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        generator._client = mock_client
        
        # Generate should fallback to templates
        goal = "design a trend strategy"
        constraints = {"strategy_type": "momentum"}
        strategy = generator.generate(goal, constraints, use_llm=True)
        
        # Should get template-based strategy
        assert strategy.type == "ts_momentum"
        assert hasattr(strategy, "lookback")
    
    def test_invalid_json_fallback(self):
        """Test handling of invalid JSON from LLM."""
        generator = LLMStrategyGenerator()
        
        invalid_json = "This is not valid JSON at all"
        result = generator._extract_json(invalid_json)
        
        assert result is None
    
    def test_template_generation_momentum(self):
        """Test template-based momentum generation."""
        generator = LLMStrategyGenerator()
        
        constraints = {
            "strategy_type": "momentum",
            "risk_preference": "moderate",
        }
        strategy = generator._generate_with_templates("test", constraints)
        
        assert strategy.type == "ts_momentum"
        assert strategy.lookback == 20
        assert strategy.vol_target == 0.15
    
    def test_template_generation_mean_reversion(self):
        """Test template-based mean reversion generation."""
        generator = LLMStrategyGenerator()
        
        constraints = {
            "strategy_type": "mean_reversion",
            "risk_preference": "conservative",
        }
        strategy = generator._generate_with_templates("test", constraints)
        
        assert strategy.type == "mean_reversion"
        assert strategy.num_std == 2.5  # Conservative setting
    
    def test_template_generation_breakout(self):
        """Test template-based breakout generation."""
        generator = LLMStrategyGenerator()
        
        constraints = {
            "strategy_type": "breakout",
            "risk_preference": "aggressive",
        }
        strategy = generator._generate_with_templates("test", constraints)
        
        assert strategy.type == "breakout"
        assert strategy.lookback == 10  # Aggressive setting
        assert strategy.breakout_threshold == 1.5
