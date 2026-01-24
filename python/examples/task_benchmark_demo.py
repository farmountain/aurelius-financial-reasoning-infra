#!/usr/bin/env python3
"""Example script demonstrating task generator and benchmark suite usage."""

import json
from pathlib import Path

from aureus.tasks import (
    TaskGenerator,
    BenchmarkRunner,
    HipCortexStorage,
    RegimeType,
    generate_regime_data,
    GoldTrajectory,
)


def main():
    """Run task generation and benchmark demo."""
    print("=" * 80)
    print("AURELIUS Task Generator and Benchmark Suite Demo")
    print("=" * 80)
    
    # 1. Generate synthetic data for different regimes
    print("\n1. Generating synthetic market data...")
    trend_data = generate_regime_data(RegimeType.TREND, num_days=100, seed=42)
    chop_data = generate_regime_data(RegimeType.CHOP, num_days=100, seed=42)
    vol_spike_data = generate_regime_data(RegimeType.VOL_SPIKE, num_days=100, seed=42)
    
    print(f"   - Trend regime: {len(trend_data)} bars")
    print(f"   - Chop regime: {len(chop_data)} bars")
    print(f"   - Vol spike regime: {len(vol_spike_data)} bars")
    
    # 2. Generate tasks
    print("\n2. Generating benchmark tasks...")
    generator = TaskGenerator(seed=42)
    
    # Generate a variety of tasks
    tasks = []
    
    # Design tasks
    tasks.append(generator.generate_design_task(
        RegimeType.TREND, 
        max_drawdown=0.25, 
        num_days=100
    ))
    tasks.append(generator.generate_design_task(
        RegimeType.CHOP, 
        max_drawdown=0.15, 
        min_sharpe=1.0,
        num_days=100
    ))
    
    # Debug tasks
    tasks.append(generator.generate_debug_task(
        RegimeType.VOL_SPIKE,
        issue="excessive drawdown during volatility spikes",
        num_days=100
    ))
    
    # Repair tasks
    tasks.append(generator.generate_repair_task(
        RegimeType.TREND,
        violation="max_drawdown_constraint",
        target_metric={"max_drawdown": 0.20},
        num_days=100
    ))
    
    # Optimize tasks
    tasks.append(generator.generate_optimize_task(
        RegimeType.CHOP,
        objective="sharpe_ratio",
        target_value=1.5,
        num_days=100
    ))
    
    print(f"   Generated {len(tasks)} tasks")
    for task in tasks:
        print(f"   - {task.task_id}: {task.goal}")
    
    # 3. Store tasks in HipCortex
    print("\n3. Storing tasks in HipCortex...")
    storage = HipCortexStorage(".hipcortex_demo")
    
    for task in tasks:
        task_hash = storage.store_task(task, metadata={
            "created_by": "demo_script",
            "version": "1.0"
        })
        print(f"   - Stored {task.task_id} → {task_hash[:12]}...")
    
    # 4. Store gold trajectories (expected solutions)
    print("\n4. Storing gold trajectories...")
    
    # Example gold trajectory for first task
    gold_trajectory = GoldTrajectory(
        task_id=tasks[0].task_id,
        strategy_spec={
            "type": "ts_momentum",
            "lookback": 20,
            "vol_target": 0.15,
        },
        expected_metrics={
            "sharpe_ratio": 1.2,
            "max_drawdown": 0.18,
            "total_return": 0.15,
        },
        crv_report={
            "passed": True,
            "violations": []
        }
    )
    
    traj_hash = storage.store_gold_trajectory(gold_trajectory)
    print(f"   - Stored gold trajectory for {tasks[0].task_id} → {traj_hash[:12]}...")
    
    # 5. Run benchmark suite
    print("\n5. Running benchmark suite...")
    runner = BenchmarkRunner(output_dir="./benchmark_demo_output")
    results = runner.run_suite(tasks)
    
    print(f"\n   Benchmark Results:")
    print(f"   - Total tasks: {results.total_tasks}")
    print(f"   - Passed: {results.passed_tasks}")
    print(f"   - CRV passed: {results.crv_passed_tasks}")
    print(f"   - Pass rate: {results.pass_rate:.1%}")
    print(f"   - CRV pass rate: {results.crv_pass_rate:.1%}")
    print(f"   - Robustness score: {results.robustness_score:.1%}")
    
    # Show individual task results
    print(f"\n   Individual Task Results:")
    for task_result in results.task_results:
        status = "✓" if task_result.passed else "✗"
        crv_status = "✓" if task_result.crv_passed else "✗"
        print(f"   {status} {task_result.task_id}")
        print(f"      Pass: {task_result.passed}, CRV: {task_result.crv_passed}")
        if task_result.metrics:
            print(f"      Metrics: {json.dumps(task_result.metrics, indent=10)}")
        if task_result.error:
            print(f"      Error: {task_result.error}")
    
    # 6. List stored artifacts
    print("\n6. Listing stored artifacts...")
    stored_tasks = storage.list_tasks()
    stored_trajectories = storage.list_trajectories()
    
    print(f"   - {len(stored_tasks)} tasks stored")
    print(f"   - {len(stored_trajectories)} gold trajectories stored")
    
    # 7. Retrieve and verify a task
    print("\n7. Verifying storage integrity...")
    retrieved_task = storage.retrieve_task(tasks[0].task_id)
    
    if retrieved_task:
        print(f"   ✓ Successfully retrieved task: {retrieved_task.task_id}")
        print(f"     Goal: {retrieved_task.goal}")
        print(f"     Regime: {retrieved_task.regime}")
        print(f"     Constraints: {retrieved_task.constraints}")
    
    print("\n" + "=" * 80)
    print("Demo completed successfully!")
    print(f"Benchmark results saved to: ./benchmark_demo_output/benchmark_results.json")
    print(f"Artifacts stored in: .hipcortex_demo/")
    print("=" * 80)


if __name__ == "__main__":
    main()
