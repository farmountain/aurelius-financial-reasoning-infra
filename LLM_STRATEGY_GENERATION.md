# LLM-Assisted Strategy Generation

## Overview

AURELIUS now supports **LLM-assisted strategy generation** using OpenAI (GPT-4) or Anthropic (Claude) with automatic fallback to template-based generation.

## Features

- ✅ **Dual-mode operation**: LLM when available, templates as fallback
- ✅ **Multiple providers**: OpenAI GPT-4, Anthropic Claude
- ✅ **Zero-cost fallback**: Works without API keys
- ✅ **Robust error handling**: Graceful degradation on failures
- ✅ **Transparent operation**: Shows which mode is active

## Quick Start

### Without LLM (Template-Based)

```python
from aureus.orchestrator import Orchestrator

# Default: No LLM, uses templates
orchestrator = Orchestrator()

result = orchestrator.run_goal(
    goal="design a trend strategy under DD<10%",
    data_path="data.parquet"
)
# Output: 📋 Using template-based strategy generation...
```

### With OpenAI

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4"  # Optional, defaults to gpt-4
```

```python
from aureus.orchestrator import Orchestrator

orchestrator = Orchestrator(llm_provider="openai")

result = orchestrator.run_goal(
    goal="design an adaptive momentum strategy that reduces exposure during high volatility",
    data_path="data.parquet"
)
# Output: 🤖 Using OPENAI for strategy generation...
# LLM Reasoning: This strategy adapts position sizing based on realized volatility...
```

### With Anthropic Claude

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"  # Optional
```

```python
from aureus.orchestrator import Orchestrator

orchestrator = Orchestrator(llm_provider="anthropic")

result = orchestrator.run_goal(
    goal="create a mean reversion strategy for choppy markets with tight risk controls",
    data_path="data.parquet"
)
# Output: 🤖 Using ANTHROPIC for strategy generation...
```

## Advanced Configuration

### Custom LLM Config

```python
from aureus.orchestrator import Orchestrator
from aureus.llm_strategy_generator import LLMConfig

config = LLMConfig(
    provider="openai",
    api_key="sk-...",
    model="gpt-4-turbo",
    temperature=0.5,  # Lower = more deterministic
    max_tokens=1500,
    timeout=45,
)

orchestrator = Orchestrator(llm_config=config)
```

### Force Template Mode

```python
# Even with API key set, use templates only
orchestrator = Orchestrator(llm_provider="none")
```

## How It Works

### LLM Generation Flow

```
1. Parse goal → Extract constraints
2. Format prompt with goal + constraints
3. Call LLM API (OpenAI or Anthropic)
4. Parse JSON response
5. Validate strategy parameters
6. Return StrategyConfig
```

### Fallback Scenarios

LLM → Template fallback happens when:
- ❌ No API key configured
- ❌ LLM library not installed (`openai` or `anthropic`)
- ❌ API call fails (timeout, rate limit, etc.)
- ❌ Invalid JSON response from LLM
- ❌ User explicitly disables LLM (`use_llm=False`)

### Example Prompt

```
You are an expert quantitative trading strategist. Generate a trading strategy based on the following goal:

Goal: design a trend strategy under DD<10%

Available strategy types:
1. ts_momentum - Time-series momentum with volatility targeting
2. mean_reversion - Mean reversion using Bollinger bands
3. breakout - Volatility breakout strategy

Constraints detected: {"max_drawdown": 0.10, "strategy_type": "momentum"}

Return ONLY a JSON object with this exact structure:
{
    "type": "ts_momentum" | "mean_reversion" | "breakout",
    "symbol": "AAPL",
    "reasoning": "Brief explanation of why this strategy fits the goal",
    "parameters": { ... }
}
```

## Benefits of LLM Mode

| Feature | Template-Based | LLM-Assisted |
|---------|---------------|--------------|
| **Speed** | <1ms | 500-2000ms |
| **Cost** | $0 | ~$0.01-0.10/generation |
| **Flexibility** | Fixed patterns | Natural language |
| **Creativity** | Low | High |
| **Complexity** | Simple goals | Complex multi-criteria |
| **Reliability** | 100% | ~95% (with fallback) |

### When to Use LLM

✅ **Complex goals**: "adaptive strategy that switches between momentum and mean reversion based on market regime"  
✅ **Research mode**: Exploring novel strategy ideas  
✅ **Natural language**: Users who don't know strategy terminology  
✅ **Parameter tuning**: LLM can suggest optimal parameter ranges  

### When to Use Templates

✅ **Production**: Deterministic, zero-latency generation  
✅ **Known patterns**: Standard momentum/mean-reversion/breakout  
✅ **Cost-sensitive**: High-frequency strategy generation  
✅ **Offline**: No internet connectivity  

## Installation

### For OpenAI

```bash
pip install openai
```

### For Anthropic

```bash
pip install anthropic
```

### Both Optional

If neither is installed, system automatically uses template-based generation with no errors.

## Testing

```bash
# Test template-based generation (no API key needed)
pytest tests/test_llm_strategy_generator.py::TestLLMStrategyGenerator::test_template_fallback_with_no_llm

# Test with mocked LLM (no API key needed)
pytest tests/test_llm_strategy_generator.py::TestLLMStrategyGenerator::test_openai_generation_success

# Test live OpenAI (requires API key)
OPENAI_API_KEY=sk-... pytest tests/test_llm_strategy_generator.py -k openai --live

# Run all LLM tests
pytest tests/test_llm_strategy_generator.py -v
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | None |
| `OPENAI_MODEL` | Model to use | `gpt-4` |
| `OPENAI_TEMPERATURE` | Sampling temperature | `0.7` |
| `ANTHROPIC_API_KEY` | Anthropic API key | None |
| `ANTHROPIC_MODEL` | Model to use | `claude-3-5-sonnet-20241022` |
| `ANTHROPIC_TEMPERATURE` | Sampling temperature | `0.7` |

## Error Handling

```python
orchestrator = Orchestrator(llm_provider="openai")

# If OpenAI fails, automatically falls back to templates
result = orchestrator.run_goal(
    goal="design a complex strategy",
    data_path="data.parquet"
)

# Console output:
# 🤖 Using OPENAI for strategy generation...
# Warning: LLM generation failed: API Error
# Falling back to template-based generation
# 📋 Using template-based strategy generation...
```

## Cost Estimation

### OpenAI GPT-4
- **Input**: ~500 tokens (prompt)
- **Output**: ~200 tokens (strategy JSON)
- **Cost**: ~$0.015-0.035 per generation

### Anthropic Claude
- **Input**: ~500 tokens (prompt)
- **Output**: ~200 tokens (strategy JSON)
- **Cost**: ~$0.004-0.015 per generation

### Template-Based
- **Cost**: $0

## Examples

### Simple Goal (Template Works)

```python
goal = "trend strategy under DD<10%"
# Template: Perfect, generates instantly
```

### Complex Goal (LLM Shines)

```python
goal = """
design an adaptive strategy that:
- uses momentum during trending markets
- switches to mean reversion during choppy periods
- reduces exposure during volatility spikes
- maintains DD<15% across all regimes
"""
# LLM: Can understand and generate appropriate parameters
# Template: Would only detect "momentum" keyword
```

## Future Enhancements

- 🔄 **Strategy evolution**: LLM iteratively improves strategies
- 🎯 **Multi-objective optimization**: LLM balances competing goals
- 📊 **Regime detection**: LLM generates regime-switching logic
- 🧪 **Hypothesis generation**: LLM suggests novel strategy ideas
- 📚 **Learning from feedback**: Fine-tune on successful strategies

## Summary

LLM-assisted generation is **optional, transparent, and robust**:
- ✅ Works out-of-the-box with no configuration (template mode)
- ✅ Automatically uses LLM when API key is present
- ✅ Gracefully degrades on any failure
- ✅ Clear indication of which mode is active
- ✅ Comprehensive test coverage

**Result**: Best of both worlds - intelligent generation when available, reliable fallback always.
