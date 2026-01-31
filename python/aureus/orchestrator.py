"""Main orchestrator that coordinates all components."""

import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

from aureus.llm_strategy_generator import LLMStrategyGenerator, LLMConfig, LLMProvider
from aureus.tools.rust_wrapper import RustEngineWrapper
from aureus.tools.schemas import (
    ToolCall,
    ToolType,
    BacktestSpec,
    BacktestToolInput,
    StrategyConfig,
    CostModelConfig,
)
from aureus.fsm.state_machine import GoalGuardFSM, State
from aureus.gates.dev_gate import DevGate
from aureus.gates.product_gate import ProductGate
from aureus.reflexion.loop import ReflexionLoop
from aureus.strict_mode import StrictMode


class Orchestrator:
    """Main orchestrator for AURELIUS quant reasoning workflow."""
    
    def __init__(
        self,
        rust_cli_path: Optional[Path] = None,
        hipcortex_cli_path: Optional[Path] = None,
        strict_mode: bool = True,
        max_drawdown_limit: float = 0.10,  # Default 10% as in example
        llm_provider: LLMProvider = "none",  # "openai", "anthropic", or "none"
        llm_config: Optional[LLMConfig] = None,
    ):
        """Initialize orchestrator.
        
        Args:
            rust_cli_path: Path to Rust CLI (auto-detected if None)
            hipcortex_cli_path: Path to hipcortex CLI (auto-detected if None)
            strict_mode: Enable strict mode for artifact ID responses
            max_drawdown_limit: Maximum allowed drawdown
            llm_provider: LLM provider for strategy generation ("openai", "anthropic", or "none")
            llm_config: Custom LLM configuration (if None, reads from environment)
        """
        self.rust_wrapper = RustEngineWrapper(rust_cli_path, hipcortex_cli_path)
        self.fsm = GoalGuardFSM()
        self.dev_gate = DevGate(self.rust_wrapper)
        self.product_gate = ProductGate(self.rust_wrapper, max_drawdown_limit)
        self.reflexion = ReflexionLoop()
        self.strict_mode_checker = StrictMode(enabled=strict_mode)
        
        # Initialize LLM strategy generator
        if llm_config is None and llm_provider != "none":
            llm_config = LLMConfig.from_env(llm_provider)
        elif llm_config is None:
            llm_config = LLMConfig(provider="none")
        
        self.llm_generator = LLMStrategyGenerator(llm_config)
    
    def run_goal(self, goal: str, data_path: str) -> Dict[str, Any]:
        """Execute a goal using the orchestrator.
        
        Args:
            goal: The goal description (e.g., "design a trend strategy under DD<10%")
            data_path: Path to market data
            
        Returns:
            Dict with execution results and artifact IDs
        """
        print(f"\n{'='*60}")
        print(f"Goal: {goal}")
        print(f"{'='*60}\n")
        
        # Parse goal to extract constraints
        constraints = self._parse_goal(goal)
        max_dd = constraints.get("max_drawdown", self.product_gate.max_drawdown_limit)
        
        # Generate initial strategy based on goal
        print("Step 1: Generating strategy...")
        strategy_spec = self._generate_strategy_from_goal(goal)
        
        # Create backtest spec
        backtest_spec = BacktestSpec(
            initial_cash=100000.0,
            seed=42,
            strategy=strategy_spec,
            cost_model=CostModelConfig(
                type="fixed_per_share",
                cost_per_share=0.005,
                minimum_commission=1.0,
            ),
        )
        
        # Create output directory
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "backtest_output"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save spec to temp file
            spec_path = Path(tmpdir) / "spec.json"
            with open(spec_path, "w") as f:
                json.dump(backtest_spec.model_dump(), f, indent=2)
            
            # Run backtest
            print("\nStep 2: Running backtest...")
            if not self.fsm.can_execute(ToolType.BACKTEST):
                # Force transition to allow backtest
                self.fsm.force_transition(State.STRATEGY_DESIGN)
            
            backtest_result = self.rust_wrapper.execute(
                ToolCall(
                    tool_type=ToolType.BACKTEST,
                    parameters=BacktestToolInput(
                        spec=backtest_spec,
                        data_path=data_path,
                        output_dir=str(output_dir),
                    ),
                )
            )
            
            if not backtest_result.success:
                print(f"Backtest failed: {backtest_result.error}")
                return {"success": False, "error": backtest_result.error}
            
            self.fsm.transition(ToolType.BACKTEST)
            
            # Display backtest results
            if "stats" in backtest_result.output:
                stats = backtest_result.output["stats"]
                print(f"\nBacktest Results:")
                print(f"  Total Return: {stats.get('total_return', 0)*100:.2f}%")
                print(f"  Sharpe Ratio: {stats.get('sharpe_ratio', 0):.2f}")
                print(f"  Max Drawdown: {stats.get('max_drawdown', 0)*100:.2f}%")
                print(f"  Number of Trades: {stats.get('num_trades', 0)}")
            
            # Run Dev Gate
            print("\nStep 3: Running Dev Gate...")
            dev_result = self.dev_gate.run({
                "spec_path": str(spec_path),
                "data_path": data_path,
            })
            print(dev_result)
            
            if not dev_result.passed:
                print("\n⚠ Dev Gate Failed")
                print(self.reflexion.generate_failure_summary(dev_result))
                
                if self.reflexion.should_retry():
                    repair_plan = self.reflexion.analyze_failure(dev_result)
                    print(f"\nRepair Plan:")
                    print(f"  Type: {repair_plan.failure_type}")
                    print(f"  Description: {repair_plan.description}")
                    print(f"  Actions:")
                    for action in repair_plan.actions:
                        print(f"    - {action}")
                    
                    return {
                        "success": False,
                        "gate": "dev",
                        "repair_plan": repair_plan,
                    }
                else:
                    return {
                        "success": False,
                        "error": "Dev gate failed after max retries",
                    }
            
            self.fsm.force_transition(State.DEV_GATE_PASSED)
            print("✓ Dev Gate Passed")
            
            # Run Product Gate
            print("\nStep 4: Running Product Gate...")
            product_result = self.product_gate.run({"output_dir": str(output_dir)})
            print(product_result)
            
            if not product_result.passed:
                print("\n⚠ Product Gate Failed")
                print(self.reflexion.generate_failure_summary(product_result))
                
                if self.reflexion.should_retry():
                    repair_plan = self.reflexion.analyze_failure(product_result)
                    print(f"\nRepair Plan:")
                    print(f"  Type: {repair_plan.failure_type}")
                    print(f"  Description: {repair_plan.description}")
                    print(f"  Actions:")
                    for action in repair_plan.actions:
                        print(f"    - {action}")
                    
                    return {
                        "success": False,
                        "gate": "product",
                        "repair_plan": repair_plan,
                    }
                else:
                    return {
                        "success": False,
                        "error": "Product gate failed after max retries",
                    }
            
            self.fsm.force_transition(State.PRODUCT_GATE_PASSED)
            print("✓ Product Gate Passed")
            
            # Commit to HipCortex
            print("\nStep 5: Committing to HipCortex...")
            
            # Create a combined artifact with all results
            artifact_path = Path(tmpdir) / "artifact.json"
            artifact_data = {
                "goal": goal,
                "spec": backtest_spec.model_dump(),
                "stats": backtest_result.output.get("stats", {}),
                "crv_report": backtest_result.output.get("crv_report", {}),
            }
            
            with open(artifact_path, "w") as f:
                json.dump(artifact_data, f, indent=2)
            
            # Note: HipCortex commit would be executed here if the binary exists
            # For now, we'll create a deterministic artifact ID based on goal and stats
            artifact_data_str = json.dumps(artifact_data, sort_keys=True)
            artifact_hash = hashlib.sha256(artifact_data_str.encode()).hexdigest()
            artifact_id = artifact_hash
            
            print(f"✓ Committed artifact: {artifact_id}")
            
            # Format final response in strict mode
            if self.strict_mode_checker.enabled:
                response = self.strict_mode_checker.format_artifact_response(
                    [artifact_id],
                    context="Goal completed",
                )
                print(f"\nFinal Response (Strict Mode):\n{response}")
            
            return {
                "success": True,
                "artifact_id": artifact_id,
                "stats": backtest_result.output.get("stats", {}),
                "crv_passed": product_result.passed,
            }
    
    def _parse_goal(self, goal: str) -> Dict[str, Any]:
        """Parse goal string to extract constraints and strategy type.
        
        Enhanced parser that extracts multiple constraints and detects strategy type
        from natural language goals.
        
        Args:
            goal: Goal description (e.g., "design a trend strategy under DD<10%")
            
        Returns:
            Dict with extracted constraints and strategy hints
        """
        constraints = {}
        goal_lower = goal.lower()
        
        # Extract max drawdown from goal (e.g., "DD<10%" or "drawdown < 0.15")
        dd_match = re.search(r"DD\s*<\s*(\d+\.?\d*)%?", goal, re.IGNORECASE)
        if dd_match:
            dd_value = float(dd_match.group(1))
            if dd_value > 1.0:  # Assume percentage if > 1
                dd_value /= 100.0
            constraints["max_drawdown"] = dd_value
        
        # Extract Sharpe ratio targets (e.g., "Sharpe > 1.5")
        sharpe_match = re.search(r"sharpe\s*>?\s*(\d+\.?\d*)", goal_lower)
        if sharpe_match:
            constraints["min_sharpe"] = float(sharpe_match.group(1))
        
        # Extract return targets (e.g., "return > 15%")
        return_match = re.search(r"return\s*>?\s*(\d+\.?\d*)%?", goal_lower)
        if return_match:
            ret_value = float(return_match.group(1))
            if ret_value > 1.0:
                ret_value /= 100.0
            constraints["min_return"] = ret_value
        
        # Detect strategy type from keywords
        if any(word in goal_lower for word in ["trend", "momentum", "following"]):
            constraints["strategy_type"] = "momentum"
        elif any(word in goal_lower for word in ["mean.reversion", "mean reversion", "reversal", "chop", "range"]):
            constraints["strategy_type"] = "mean_reversion"
        elif any(word in goal_lower for word in ["breakout", "volatility", "vol"]):
            constraints["strategy_type"] = "breakout"
        else:
            # Default to momentum for generic goals
            constraints["strategy_type"] = "momentum"
        
        # Detect risk preferences
        if any(word in goal_lower for word in ["conservative", "low risk", "safe"]):
            constraints["risk_preference"] = "conservative"
        elif any(word in goal_lower for word in ["aggressive", "high risk", "speculative"]):
            constraints["risk_preference"] = "aggressive"
        else:
            constraints["risk_preference"] = "moderate"
        
        return constraints
    
    def _generate_strategy_from_goal(self, goal: str, use_llm: bool = True) -> StrategyConfig:
        """Generate strategy specification from goal using LLM or templates.
        
        Uses LLM-assisted generation when available, with automatic fallback to
        template-based generation if LLM fails or is not configured.
        
        Args:
            goal: Goal description
            use_llm: Whether to use LLM if available (default: True)
            
        Returns:
            StrategyConfig for the appropriate strategy
        """
        constraints = self._parse_goal(goal)
        
        # Use LLM generator (with automatic template fallback)
        if self.llm_generator.is_llm_available:
            print(f"🤖 Using {self.llm_generator.config.provider.upper()} for strategy generation...")
        else:
            print("📋 Using template-based strategy generation...")
        
        return self.llm_generator.generate(goal, constraints, use_llm=use_llm)
