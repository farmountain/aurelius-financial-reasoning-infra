"""LLM-assisted strategy generation module."""

import json
import os
from typing import Optional, Dict, Any, Literal
from dataclasses import dataclass

from aureus.tools.schemas import StrategyConfig


LLMProvider = Literal["openai", "anthropic", "none"]


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    
    provider: LLMProvider = "none"
    api_key: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30
    
    @classmethod
    def from_env(cls, provider: LLMProvider = "openai") -> "LLMConfig":
        """Create LLM config from environment variables.
        
        Args:
            provider: LLM provider to use
            
        Returns:
            LLMConfig instance
        """
        if provider == "openai":
            return cls(
                provider="openai",
                api_key=os.getenv("OPENAI_API_KEY"),
                model=os.getenv("OPENAI_MODEL", "gpt-4"),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            )
        elif provider == "anthropic":
            return cls(
                provider="anthropic",
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
                temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7")),
            )
        else:
            return cls(provider="none")


class LLMStrategyGenerator:
    """LLM-assisted strategy generation with fallback to templates."""
    
    STRATEGY_GENERATION_PROMPT = """You are an expert quantitative trading strategist. Generate a trading strategy based on the following goal:

Goal: {goal}

Available strategy types:
1. ts_momentum - Time-series momentum with volatility targeting
   Parameters: lookback (int), vol_target (float), vol_lookback (int)
   
2. mean_reversion - Mean reversion using Bollinger bands
   Parameters: lookback (int), num_std (float), reversion_threshold (float)
   
3. breakout - Volatility breakout strategy
   Parameters: lookback (int), breakout_threshold (float), atr_period (int)

Constraints detected: {constraints}

Return ONLY a JSON object with this exact structure:
{{
    "type": "ts_momentum" | "mean_reversion" | "breakout",
    "symbol": "AAPL",
    "reasoning": "Brief explanation of why this strategy fits the goal",
    "parameters": {{
        // Strategy-specific parameters
    }}
}}

Focus on generating strategies that:
- Respect the specified constraints (drawdown limits, Sharpe ratios)
- Match the detected market regime or goal intent
- Use reasonable parameter values based on quantitative research
- Are implementable with the available strategy types

Return only the JSON, no additional text."""

    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize LLM strategy generator.
        
        Args:
            config: LLM configuration (None = no LLM, use templates only)
        """
        self.config = config or LLMConfig(provider="none")
        self._client = None
        
        if self.config.provider != "none" and self.config.api_key:
            self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize LLM client based on provider."""
        try:
            if self.config.provider == "openai":
                import openai
                self._client = openai.OpenAI(
                    api_key=self.config.api_key,
                    timeout=self.config.timeout,
                )
            elif self.config.provider == "anthropic":
                import anthropic
                self._client = anthropic.Anthropic(
                    api_key=self.config.api_key,
                    timeout=self.config.timeout,
                )
        except ImportError as e:
            print(f"Warning: Failed to import LLM library: {e}")
            print("Falling back to template-based generation")
            self.config.provider = "none"
            self._client = None
        except Exception as e:
            print(f"Warning: Failed to initialize LLM client: {e}")
            print("Falling back to template-based generation")
            self.config.provider = "none"
            self._client = None
    
    def generate(
        self,
        goal: str,
        constraints: Dict[str, Any],
        use_llm: bool = True,
    ) -> StrategyConfig:
        """Generate strategy from goal using LLM or templates.
        
        Args:
            goal: Natural language goal description
            constraints: Extracted constraints from goal
            use_llm: Whether to use LLM (if available)
            
        Returns:
            StrategyConfig for the generated strategy
        """
        # Try LLM generation if enabled and available
        if use_llm and self.config.provider != "none" and self._client:
            try:
                strategy = self._generate_with_llm(goal, constraints)
                if strategy:
                    return strategy
            except Exception as e:
                print(f"Warning: LLM generation failed: {e}")
                print("Falling back to template-based generation")
        
        # Fallback to template-based generation
        return self._generate_with_templates(goal, constraints)
    
    def _generate_with_llm(
        self,
        goal: str,
        constraints: Dict[str, Any],
    ) -> Optional[StrategyConfig]:
        """Generate strategy using LLM.
        
        Args:
            goal: Goal description
            constraints: Extracted constraints
            
        Returns:
            StrategyConfig or None if generation fails
        """
        prompt = self.STRATEGY_GENERATION_PROMPT.format(
            goal=goal,
            constraints=json.dumps(constraints, indent=2),
        )
        
        try:
            if self.config.provider == "openai":
                response = self._client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert quantitative trading strategist. "
                                     "Always respond with valid JSON only."
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
                content = response.choices[0].message.content
                
            elif self.config.provider == "anthropic":
                response = self._client.messages.create(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    messages=[
                        {"role": "user", "content": prompt},
                    ],
                )
                content = response.content[0].text
            else:
                return None
            
            # Parse LLM response
            strategy_json = self._extract_json(content)
            if not strategy_json:
                return None
            
            # Convert to StrategyConfig
            return self._json_to_strategy_config(strategy_json, goal)
            
        except Exception as e:
            print(f"LLM API error: {e}")
            return None
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response.
        
        Args:
            text: LLM response text
            
        Returns:
            Parsed JSON dict or None
        """
        # Try to find JSON in response
        text = text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object in text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            return None
    
    def _json_to_strategy_config(
        self,
        strategy_json: Dict[str, Any],
        goal: str,
    ) -> StrategyConfig:
        """Convert LLM JSON response to StrategyConfig.
        
        Args:
            strategy_json: Parsed JSON from LLM
            goal: Original goal (for context)
            
        Returns:
            StrategyConfig instance
        """
        strategy_type = strategy_json.get("type", "ts_momentum")
        symbol = strategy_json.get("symbol", "AAPL")
        params = strategy_json.get("parameters", {})
        reasoning = strategy_json.get("reasoning", "")
        
        # Create StrategyConfig with LLM parameters
        config = StrategyConfig(
            type=strategy_type,
            symbol=symbol,
            **params
        )
        
        # Store reasoning as metadata if available
        if reasoning:
            print(f"LLM Reasoning: {reasoning}")
        
        return config
    
    def _generate_with_templates(
        self,
        goal: str,
        constraints: Dict[str, Any],
    ) -> StrategyConfig:
        """Generate strategy using template-based approach.
        
        This is the fallback method when LLM is not available or fails.
        
        Args:
            goal: Goal description
            constraints: Extracted constraints
            
        Returns:
            StrategyConfig from templates
        """
        strategy_type = constraints.get("strategy_type", "momentum")
        risk_preference = constraints.get("risk_preference", "moderate")
        
        # Adjust parameters based on risk preference
        if risk_preference == "conservative":
            vol_target = 0.10
            lookback = 40
        elif risk_preference == "aggressive":
            vol_target = 0.25
            lookback = 10
        else:
            vol_target = 0.15
            lookback = 20
        
        # Generate based on strategy type
        if strategy_type == "momentum":
            return StrategyConfig(
                type="ts_momentum",
                symbol="AAPL",
                lookback=lookback,
                vol_target=vol_target,
                vol_lookback=min(60, lookback * 3),
            )
        elif strategy_type == "mean_reversion":
            return StrategyConfig(
                type="mean_reversion",
                symbol="AAPL",
                lookback=lookback,
                num_std=2.5 if risk_preference == "conservative" else 2.0,
                reversion_threshold=0.5,
            )
        elif strategy_type == "breakout":
            return StrategyConfig(
                type="breakout",
                symbol="AAPL",
                lookback=lookback,
                breakout_threshold=2.0 if risk_preference == "conservative" else 1.5,
                atr_period=14,
            )
        else:
            return StrategyConfig(
                type="ts_momentum",
                symbol="AAPL",
                lookback=lookback,
                vol_target=vol_target,
                vol_lookback=min(60, lookback * 3),
            )
    
    @property
    def is_llm_available(self) -> bool:
        """Check if LLM is available for use."""
        return (
            self.config.provider != "none" 
            and self._client is not None 
            and self.config.api_key is not None
        )
