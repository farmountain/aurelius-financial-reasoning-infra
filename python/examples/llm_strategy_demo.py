#!/usr/bin/env python3
"""
Example demonstrating LLM-assisted vs template-based strategy generation.

This script shows:
1. Template-based generation (no API key required)
2. LLM-assisted generation (requires OpenAI or Anthropic API key)
3. Fallback behavior when LLM fails
4. Comparison of results
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aureus.orchestrator import Orchestrator
from aureus.llm_strategy_generator import LLMConfig


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")


def demo_template_generation():
    """Demonstrate template-based strategy generation."""
    print_section("1. TEMPLATE-BASED GENERATION (No API Key Required)")
    
    orchestrator = Orchestrator(llm_provider="none")
    
    goals = [
        "design a trend strategy under DD<10%",
        "create a conservative mean reversion strategy",
        "aggressive breakout strategy with DD<20%",
    ]
    
    for goal in goals:
        print(f"\nGoal: {goal}")
        strategy = orchestrator._generate_strategy_from_goal(goal)
        
        print(f"  Type: {strategy.type}")
        print(f"  Symbol: {strategy.symbol}")
        if hasattr(strategy, 'lookback'):
            print(f"  Lookback: {strategy.lookback}")
        if hasattr(strategy, 'vol_target'):
            print(f"  Vol Target: {strategy.vol_target}")
        if hasattr(strategy, 'num_std'):
            print(f"  Num Std: {strategy.num_std}")
        if hasattr(strategy, 'breakout_threshold'):
            print(f"  Breakout Threshold: {strategy.breakout_threshold}")


def demo_llm_generation():
    """Demonstrate LLM-assisted strategy generation."""
    print_section("2. LLM-ASSISTED GENERATION (Requires API Key)")
    
    # Check if API key is available
    has_openai = os.getenv("OPENAI_API_KEY") is not None
    has_anthropic = os.getenv("ANTHROPIC_API_KEY") is not None
    
    if not has_openai and not has_anthropic:
        print("⚠️  No LLM API key found in environment variables.")
        print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY to test LLM mode.")
        print("   Skipping LLM demonstration.\n")
        return
    
    # Use whichever provider is available
    provider = "openai" if has_openai else "anthropic"
    print(f"Using provider: {provider.upper()}\n")
    
    orchestrator = Orchestrator(llm_provider=provider)
    
    if not orchestrator.llm_generator.is_llm_available:
        print("⚠️  LLM initialization failed. Check your API key and library installation.")
        print("   Install with: pip install openai  (or: pip install anthropic)")
        return
    
    # Test with complex goals that benefit from LLM
    complex_goals = [
        "design a momentum strategy that reduces exposure during high volatility periods under DD<12%",
        "create an adaptive strategy for choppy markets with tight risk controls",
        "build a volatility breakout strategy optimized for crypto markets",
    ]
    
    for goal in complex_goals:
        print(f"\nGoal: {goal}")
        try:
            strategy = orchestrator._generate_strategy_from_goal(goal)
            
            print(f"  ✓ Generated: {strategy.type}")
            print(f"  Symbol: {strategy.symbol}")
            if hasattr(strategy, 'lookback'):
                print(f"  Lookback: {strategy.lookback}")
            if hasattr(strategy, 'vol_target'):
                print(f"  Vol Target: {strategy.vol_target}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")


def demo_fallback_behavior():
    """Demonstrate graceful fallback from LLM to templates."""
    print_section("3. FALLBACK BEHAVIOR (LLM → Template)")
    
    print("Scenario: LLM configured but API call fails\n")
    
    # Create orchestrator with invalid API key (will fail and fallback)
    config = LLMConfig(
        provider="openai",
        api_key="sk-invalid-key-for-testing",
        model="gpt-4",
    )
    
    orchestrator = Orchestrator(llm_config=config)
    
    goal = "design a trend strategy under DD<10%"
    print(f"Goal: {goal}\n")
    
    print("Expected behavior:")
    print("  1. Try LLM generation")
    print("  2. LLM fails (invalid API key)")
    print("  3. Automatically fallback to template")
    print("  4. Return valid strategy\n")
    
    print("Actual execution:")
    try:
        strategy = orchestrator._generate_strategy_from_goal(goal)
        print(f"\n✓ Successfully generated strategy despite LLM failure")
        print(f"  Type: {strategy.type}")
        print(f"  This came from template fallback!")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


def demo_comparison():
    """Compare template vs LLM results for same goal."""
    print_section("4. COMPARISON: Template vs LLM")
    
    goal = "design a conservative momentum strategy under DD<8%"
    
    # Template version
    print(f"Goal: {goal}\n")
    print("Template-based result:")
    orchestrator_template = Orchestrator(llm_provider="none")
    strategy_template = orchestrator_template._generate_strategy_from_goal(goal)
    print(f"  Type: {strategy_template.type}")
    print(f"  Lookback: {strategy_template.lookback}")
    print(f"  Vol Target: {strategy_template.vol_target}")
    
    # LLM version (if available)
    if os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
        provider = "openai" if os.getenv("OPENAI_API_KEY") else "anthropic"
        print(f"\n{provider.upper()}-based result:")
        
        orchestrator_llm = Orchestrator(llm_provider=provider)
        if orchestrator_llm.llm_generator.is_llm_available:
            try:
                strategy_llm = orchestrator_llm._generate_strategy_from_goal(goal)
                print(f"  Type: {strategy_llm.type}")
                if hasattr(strategy_llm, 'lookback'):
                    print(f"  Lookback: {strategy_llm.lookback}")
                if hasattr(strategy_llm, 'vol_target'):
                    print(f"  Vol Target: {strategy_llm.vol_target}")
                
                print("\nDifferences:")
                print("  - Template uses fixed rules based on keywords")
                print("  - LLM can interpret nuance and context")
                print("  - LLM may suggest different parameters based on 'conservative' hint")
            except Exception as e:
                print(f"  (LLM call failed: {e})")
    else:
        print("\n(Set OPENAI_API_KEY or ANTHROPIC_API_KEY to see LLM comparison)")


def main():
    """Run all demonstrations."""
    print("\n" + "="*80)
    print("AURELIUS LLM-Assisted Strategy Generation Demo")
    print("="*80)
    
    # 1. Template-based (always works)
    demo_template_generation()
    
    # 2. LLM-assisted (if configured)
    demo_llm_generation()
    
    # 3. Fallback behavior
    demo_fallback_behavior()
    
    # 4. Comparison
    demo_comparison()
    
    # Summary
    print_section("SUMMARY")
    print("Key Takeaways:")
    print("  ✓ Template-based: Fast, reliable, zero-cost")
    print("  ✓ LLM-assisted: Flexible, intelligent, understands context")
    print("  ✓ Fallback: Automatic, graceful, no failures")
    print("  ✓ Optional: Works without API keys, enhanced with them\n")
    
    print("Next Steps:")
    print("  1. For basic use: No setup needed, templates work out-of-box")
    print("  2. For advanced use: Set OPENAI_API_KEY or ANTHROPIC_API_KEY")
    print("  3. Install LLM library: pip install openai (or anthropic)")
    print("  4. Test with complex goals to see LLM benefits\n")


if __name__ == "__main__":
    main()
