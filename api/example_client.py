"""Example API client demonstrating the full workflow."""
import httpx
import asyncio
import json
from datetime import datetime, timedelta


async def main():
    """Run example API workflow."""
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("AURELIUS REST API - Example Workflow")
        print("=" * 60)
        
        # 1. Health Check
        print("\n[1] Health Check")
        print("-" * 60)
        try:
            response = await client.get(f"{base_url}/health")
            print(f"✅ API is {response.json()['status']}")
        except Exception as e:
            print(f"❌ API not running: {e}")
            print("\nPlease start the API server:")
            print("  cd api && python main.py")
            return
        
        # 2. Generate Strategies
        print("\n[2] Generate Strategies")
        print("-" * 60)
        gen_response = await client.post(
            f"{base_url}/api/v1/strategies/generate",
            json={
                "goal": "Find profitable momentum patterns in growth stocks",
                "risk_preference": "moderate",
                "max_strategies": 5,
            }
        )
        gen_data = gen_response.json()
        print(f"Generated {len(gen_data['strategies'])} strategies:")
        
        strategy_id = None
        for i, strategy in enumerate(gen_data['strategies'], 1):
            print(f"  {i}. {strategy['name']}")
            print(f"     Type: {strategy['strategy_type']}")
            print(f"     Confidence: {strategy['confidence']:.1%}")
            print(f"     Lookback: {strategy['parameters']['lookback']} days")
            if i == 1:
                strategy_id = strategy['strategy_type']
        
        # 3. Run Backtest
        print("\n[3] Run Backtest")
        print("-" * 60)
        backtest_response = await client.post(
            f"{base_url}/api/v1/backtests/run",
            json={
                "strategy_id": strategy_id,
                "start_date": "2023-01-01",
                "end_date": "2024-01-01",
                "initial_capital": 100000,
                "instruments": ["SPY"],
            }
        )
        backtest_data = backtest_response.json()
        backtest_id = backtest_data['backtest_id']
        print(f"Backtest started: {backtest_id}")
        
        # Wait a moment and check status
        await asyncio.sleep(1)
        status_response = await client.get(
            f"{base_url}/api/v1/backtests/{backtest_id}/status"
        )
        status_data = status_response.json()
        print(f"Status: {status_data['status']}")
        
        if status_data['status'] == 'completed':
            bt_result = status_data['result']
            print(f"✅ Backtest completed!")
            print(f"   Total Return: {bt_result['metrics']['total_return']:.2f}%")
            print(f"   Sharpe Ratio: {bt_result['metrics']['sharpe_ratio']:.2f}")
            print(f"   Max Drawdown: {bt_result['metrics']['max_drawdown']:.2f}%")
            print(f"   Win Rate: {bt_result['metrics']['win_rate']:.1f}%")
        
        # 4. Run Validation
        print("\n[4] Run Walk-Forward Validation")
        print("-" * 60)
        val_response = await client.post(
            f"{base_url}/api/v1/validation/run",
            json={
                "strategy_id": strategy_id,
                "start_date": "2023-01-01",
                "end_date": "2024-01-01",
                "window_size_days": 90,
                "train_size_days": 180,
            }
        )
        val_data = val_response.json()
        validation_id = val_data['validation_id']
        print(f"Validation started: {validation_id}")
        
        # Wait and check status
        await asyncio.sleep(2)
        val_status_response = await client.get(
            f"{base_url}/api/v1/validation/{validation_id}/status"
        )
        val_status = val_status_response.json()
        
        if val_status['status'] == 'completed':
            val_result = val_status['result']
            print(f"✅ Validation completed!")
            print(f"   Windows: {val_result['metrics']['num_windows']}")
            print(f"   Avg Train Sharpe: {val_result['metrics']['avg_train_sharpe']:.2f}")
            print(f"   Avg Test Sharpe: {val_result['metrics']['avg_test_sharpe']:.2f}")
            print(f"   Stability Score: {val_result['metrics']['stability_score']:.1f}%")
            print(f"   Passed: {val_result['metrics']['passed']}")
        
        # 5. Run Dev Gate
        print("\n[5] Development Gate")
        print("-" * 60)
        dev_response = await client.post(
            f"{base_url}/api/v1/gates/dev-gate",
            json={"strategy_id": strategy_id}
        )
        dev_data = dev_response.json()
        print(f"Gate Status: {dev_data['gate_status']}")
        for check in dev_data['checks']:
            status_symbol = "✅" if check['passed'] else "❌"
            print(f"  {status_symbol} {check['check_name']}: {check['message']}")
        
        # 6. Run CRV Gate
        print("\n[6] CRV Gate (Risk/Reward)")
        print("-" * 60)
        crv_response = await client.post(
            f"{base_url}/api/v1/gates/crv-gate",
            json={"strategy_id": strategy_id}
        )
        crv_data = crv_response.json()
        print(f"Gate Status: {crv_data['gate_status']}")
        print(f"  Sharpe Check: {crv_data['actual_sharpe']:.2f} >= {crv_data['min_sharpe_threshold']} {'✅' if crv_data['sharpe_pass'] else '❌'}")
        print(f"  Drawdown Check: {crv_data['actual_drawdown']:.2f}% >= {crv_data['max_drawdown_threshold']}% {'✅' if crv_data['drawdown_pass'] else '❌'}")
        print(f"  Return Check: {crv_data['actual_return']:.2f}% >= {crv_data['min_return_threshold']}% {'✅' if crv_data['return_pass'] else '❌'}")
        
        # 7. Run Product Gate
        print("\n[7] Product Gate (Full Check)")
        print("-" * 60)
        product_response = await client.post(
            f"{base_url}/api/v1/gates/product-gate",
            json={"strategy_id": strategy_id}
        )
        product_data = product_response.json()
        print(f"Production Ready: {product_data['production_ready']}")
        print(f"Recommendation: {product_data['recommendation']}")
        
        # 8. List All Strategies
        print("\n[8] List All Strategies")
        print("-" * 60)
        list_response = await client.get(f"{base_url}/api/v1/strategies?limit=5")
        list_data = list_response.json()
        print(f"Total strategies: {list_data['total']}")
        print(f"Showing {len(list_data['strategies'])} (limit 5)")
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ API WORKFLOW COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nNext Steps:")
        print("1. Access interactive docs: http://localhost:8000/docs")
        print("2. Review ReDoc: http://localhost:8000/redoc")
        print("3. Check API status: http://localhost:8000/api/v1/status")
        print("4. Integrate with web dashboard or external clients")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
