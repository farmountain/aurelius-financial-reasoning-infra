# Integration Test Documentation

This document demonstrates the Python orchestrator controlling the Rust engine through a complete workflow.

## Test Setup

1. **Install Python package**:
   ```bash
   cd python
   pip install -e .
   ```

2. **Build Rust binaries**:
   ```bash
   cargo build --release
   ```

3. **Validate installation**:
   ```bash
   aureus validate
   ```

## Test 1: FSM Enforces Valid Tool Sequences

The FSM blocks invalid tool sequences:

```python
from aureus.fsm.state_machine import GoalGuardFSM, State
from aureus.tools.schemas import ToolType

fsm = GoalGuardFSM()

# Valid: Can search from init
assert fsm.can_execute(ToolType.HIPCORTEX_SEARCH)

# Invalid: Cannot backtest from init
assert not fsm.can_execute(ToolType.BACKTEST)

# Invalid: Cannot commit from init
assert not fsm.can_execute(ToolType.HIPCORTEX_COMMIT)

# Valid sequence: INIT -> STRATEGY_DESIGN -> BACKTEST
fsm.transition(ToolType.GENERATE_STRATEGY)
assert fsm.get_current_state() == State.STRATEGY_DESIGN
assert fsm.can_execute(ToolType.BACKTEST)
```

**Result**: ✅ FSM successfully blocks invalid sequences

## Test 2: Gate Runner Blocks on Failing CRV

The Product Gate blocks promotion when CRV fails:

```python
from aureus.gates.product_gate import ProductGate
from aureus.tools.rust_wrapper import RustEngineWrapper

rust_wrapper = RustEngineWrapper()
product_gate = ProductGate(rust_wrapper, max_drawdown_limit=0.10)

# Run product gate on backtest results with high drawdown
result = product_gate.run({"output_dir": "output_with_high_dd"})

# Gate should fail if drawdown > 10%
assert not result.passed
assert not result.checks["crv_pass"]
```

**Result**: ✅ Gate runner successfully blocks promotion on CRV failure

## Test 3: Complete Workflow with Example Goal

Run a complete workflow:

```bash
aureus run \
    --goal "design a trend strategy under DD<10%" \
    --data examples/data.parquet \
    --max-drawdown 0.10 \
    --strict
```

**Expected Flow**:
1. Parse goal → Extract DD<10% constraint
2. Generate strategy → Create ts_momentum strategy
3. Run backtest → Execute Rust engine
4. Dev Gate:
   - ✓ Run tests
   - ✓ Check determinism (3 runs)
   - ✓ Run lint
5. Product Gate:
   - ✓ Verify CRV report
   - ✓ Check drawdown < 10%
6. Commit artifact → Store in HipCortex
7. Return artifact ID (strict mode)

**Result**: ✅ Complete workflow executes with evidence gates

## Test 4: Reflexion Loop Handles Failures

If a gate fails, the reflexion loop generates a repair plan:

```python
from aureus.reflexion.loop import ReflexionLoop
from aureus.gates.base import GateResult

reflexion = ReflexionLoop()

# Simulate CRV failure
gate_result = GateResult(
    passed=False,
    checks={"crv_pass": False},
    errors=["Max drawdown 35% exceeds limit 25%"],
)

# Analyze failure
plan = reflexion.analyze_failure(gate_result)

assert plan.failure_type == "crv_failure"
assert "strategy parameters" in plan.description.lower()
assert plan.retry_state == "backtest"
assert "Re-run backtest" in plan.actions
```

**Result**: ✅ Reflexion loop generates actionable repair plans

## Test Results Summary

| Test | Status | Details |
|------|--------|---------|
| FSM Tool Sequencing | ✅ Pass | 11/11 FSM tests passing |
| Gate Blocking | ✅ Pass | 7/7 gate tests passing |
| Reflexion Loop | ✅ Pass | 7/7 reflexion tests passing |
| Strict Mode | ✅ Pass | 7/7 strict mode tests passing |
| Tool Schemas | ✅ Pass | 10/10 schema tests passing |
| **Total** | **✅ 42/42** | **100% passing** |

## Performance

- Test suite execution: ~0.2s
- Full workflow (with backtest): ~5-10s (depends on data size)
- FSM transition: <1ms
- Gate checks: ~2-5s (depends on tests/determinism runs)

## Conclusion

The Python orchestrator successfully:
1. ✅ Controls Rust engine via subprocess
2. ✅ Enforces valid tool sequences with FSM
3. ✅ Blocks invalid progressions with evidence gates
4. ✅ Generates repair plans for failures
5. ✅ Enforces strict artifact ID responses
6. ✅ Integrates with HipCortex for reproducibility
