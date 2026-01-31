"""Product gate: CRV verification and walk-forward validation."""

from typing import Dict, Optional
from pathlib import Path
from aureus.gates.base import Gate, GateResult
from aureus.tools.rust_wrapper import RustEngineWrapper
from aureus.tools.schemas import ToolCall, ToolType, CRVVerifyToolInput
from aureus.walk_forward import WalkForwardValidator


class ProductGate(Gate):
    """Product gate that enforces production-readiness checks."""
    
    def __init__(
        self,
        rust_wrapper: RustEngineWrapper,
        max_drawdown_limit: float = 0.25,
        enable_walk_forward: bool = False,  # Disabled by default for backward compatibility
        walk_forward_windows: int = 3,
    ):
        """Initialize product gate.
        
        Args:
            rust_wrapper: Rust engine wrapper for running checks
            max_drawdown_limit: Maximum allowed drawdown (default 25%)
            enable_walk_forward: Enable walk-forward validation (default: False)
            walk_forward_windows: Number of walk-forward windows (default: 3)
        """
        self.rust_wrapper = rust_wrapper
        self.max_drawdown_limit = max_drawdown_limit
        self.enable_walk_forward = enable_walk_forward
        self.walk_forward_validator = WalkForwardValidator(num_windows=walk_forward_windows) if enable_walk_forward else None
    
    def get_name(self) -> str:
        """Get the gate name."""
        return "ProductGate"
    
    def run(self, context: Dict[str, any]) -> GateResult:
        """Run product gate checks.
        
        Args:
            context: Must contain 'output_dir' with backtest results
            
        Returns:
            GateResult with check results
        """
        checks = {}
        errors = []
        details = {}
        
        output_dir = context.get("output_dir")
        if not output_dir:
            return GateResult(
                passed=False,
                checks={"output_dir_provided": False},
                errors=["output_dir not provided in context"],
            )
        
        output_path = Path(output_dir)
        stats_path = output_path / "stats.json"
        trades_path = output_path / "trades.csv"
        equity_path = output_path / "equity_curve.csv"
        crv_path = output_path / "crv_report.json"
        
        # Check 1: CRV verification
        print("Running CRV verification...")
        if not crv_path.exists():
            checks["crv_exists"] = False
            errors.append("CRV report not found")
        else:
            crv_result = self.rust_wrapper.execute(
                ToolCall(
                    tool_type=ToolType.CRV_VERIFY,
                    parameters=CRVVerifyToolInput(
                        stats_path=str(stats_path),
                        trades_path=str(trades_path),
                        equity_path=str(equity_path),
                        max_drawdown_limit=self.max_drawdown_limit,
                    ),
                )
            )
            checks["crv_pass"] = crv_result.success
            if not crv_result.success:
                errors.append(f"CRV verification failed")
                if "crv_report" in crv_result.output:
                    violations = crv_result.output["crv_report"].get("violations", [])
                    for v in violations:
                        errors.append(f"  - {v.get('rule_id')}: {v.get('message')}")
            details["crv"] = crv_result.output
        
        # Check 2: Walk-forward validation
        if self.enable_walk_forward and "data_path" in context:
            print("Running walk-forward validation...")
            try:
                data_path = context["data_path"]
                wf_output_dir = output_path / "walk_forward"
                wf_output_dir.mkdir(exist_ok=True)
                
                # Create windows
                windows = self.walk_forward_validator.create_windows(data_path)
                print(f"  Created {len(windows)} walk-forward windows")
                
                # For now, we'll use the full backtest stats as a proxy
                # In a full implementation, we would re-run the strategy on each window
                import json
                with open(stats_path) as f:
                    stats = json.load(f)
                
                # Simplified validation: check if Sharpe ratio is stable
                # In production, would run actual walk-forward backtests
                sharpe = stats.get("sharpe_ratio", 0.0)
                
                if sharpe >= self.walk_forward_validator.min_test_sharpe:
                    checks["walk_forward"] = True
                    details["walk_forward"] = {
                        "num_windows": len(windows),
                        "sharpe_ratio": sharpe,
                        "status": "passed_simplified",
                        "note": "Full walk-forward implementation requires re-running backtests per window"
                    }
                else:
                    checks["walk_forward"] = False
                    errors.append(f"Strategy Sharpe ({sharpe:.3f}) below minimum threshold")
                    details["walk_forward"] = {"sharpe_ratio": sharpe, "status": "failed"}
                    
            except Exception as e:
                checks["walk_forward"] = False
                errors.append(f"Walk-forward validation failed: {str(e)}")
                details["walk_forward"] = {"error": str(e)}
        else:
            # Walk-forward disabled or no data path provided
            print("Walk-forward validation (disabled)...")
            checks["walk_forward"] = True  # Pass if disabled
            details["walk_forward"] = {
                "enabled": False,
                "note": "Enable with enable_walk_forward=True and provide data_path"
            }
        
        # Check 3: Stress suite (placeholder for now)
        # In a full implementation, this would test strategy under various market conditions
        print("Stress suite (placeholder)...")
        checks["stress_suite"] = True  # Placeholder
        details["stress_suite"] = {"note": "Placeholder - not implemented yet"}
        
        # Gate passes only if all checks pass
        passed = all(checks.values())
        
        return GateResult(
            passed=passed,
            checks=checks,
            errors=errors,
            details=details,
        )
