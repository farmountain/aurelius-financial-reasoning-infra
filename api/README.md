# AURELIUS REST API

Comprehensive REST API for quantitative strategy generation, backtesting, validation, and production gate checking.

## Features

- **Strategy Generation**: Generate trading strategies from natural language goals
- **Backtesting**: Run backtests with detailed performance metrics
- **Deterministic Run Controls**: Optional `seed` and `data_source` inputs for reproducible runs
- **Walk-Forward Validation**: Validate strategy stability across historical periods
- **Gate Verification**: Run dev gate, CRV gate, and product gate checks
- **Reflexion**: Persisted strategy improvement iteration history and run execution
- **Orchestrator**: Persisted end-to-end pipeline runs with stage transitions
- **PostgreSQL Persistence**: Workflow artifacts are persisted in PostgreSQL-backed models
- **JWT Auth**: Backtest, validation, gate, reflexion, and orchestrator workflow routes are protected
- **Async Processing**: Background task execution for long-running operations
- **OpenAPI Documentation**: Auto-generated interactive API documentation

## Installation

```bash
cd api
pip install -r requirements.txt
```

## Running the Server

```bash
cd api
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Or use the main.py entry point:

```bash
cd api
python main.py
```

The API will be available at `http://localhost:8000`.

## API Documentation

### Interactive Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Core Endpoints

### Strategies

#### Generate Strategies
```
POST /api/v1/strategies/generate
```

Generate trading strategies from a natural language goal.

**Request:**
```json
{
  "goal": "Find arbitrage opportunities in paired stocks",
  "risk_preference": "moderate",
  "max_strategies": 5
}
```

**Response:**
```json
{
  "request_id": "uuid",
  "strategies": [
    {
      "id": "uuid",
      "strategy_type": "pairs_trading",
      "name": "Pairs Trading Strategy",
      "description": "...",
      "parameters": {
        "lookback": 20,
        "vol_target": 0.15,
        "position_size": 1.0,
        "stop_loss": 2.0,
        "take_profit": 5.0
      },
      "confidence": 0.9

      Use the returned strategy `id` value as `strategy_id` when invoking backtest, validation, gate, reflexion, and orchestrator routes.

      ---

      ## Authentication and Persistence Policy

      - JWT authentication is required for user-scoped workflow routes.
      - Core workflow artifacts (strategies, backtests, validations, gate results, reflexion, orchestrator runs) are persisted in PostgreSQL tables.
      - Include `Authorization: Bearer <token>` for protected endpoints.

      Example:

      ```bash
      curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/backtests/123/status
      ```
    }
  ],
  "generation_time_ms": 125.5
}
```

#### List Strategies
```
GET /api/v1/strategies?skip=0&limit=10
```

Get paginated list of all generated strategies.

#### Get Strategy Details
```
GET /api/v1/strategies/{strategy_id}
```

Get complete details for a specific strategy.

#### Validate Strategy
```
POST /api/v1/strategies/{strategy_id}/validate
```

Run quick validation checks on strategy parameters.

---

### Backtests

#### Run Backtest
```
POST /api/v1/backtests/run
```

Start a backtest in the background.

**Request:**
```json
{
  "strategy_id": "uuid",
  "start_date": "2023-01-01",
  "end_date": "2024-01-01",
  "initial_capital": 100000,
  "instruments": ["SPY", "QQQ"],
  "seed": 42,
  "data_source": "default"
}
```

**Response:**
```json
{
  "backtest_id": "uuid",
  "status": "running",
  "message": "Backtest started",
  "created_at": "2024-01-15T10:30:00.000Z"
}
```

#### Check Backtest Status
```
GET /api/v1/backtests/{backtest_id}/status
```

Check the status of a running backtest.

#### Get Backtest Results
```
GET /api/v1/backtests/{backtest_id}
```

Get completed backtest results with performance metrics.

**Response:**
```json
{
  "backtest": {
    "backtest_id": "uuid",
    "strategy_id": "uuid",
    "status": "completed",
    "metrics": {
      "total_return": 18.5,
      "sharpe_ratio": 1.75,
      "sortino_ratio": 2.1,
      "max_drawdown": -12.5,
      "win_rate": 55.0,
      "profit_factor": 1.8,
      "total_trades": 125,
      "avg_trade": 0.148,
      "calmar_ratio": 0.14
    },
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "completed_at": "2024-01-15T10:35:00.000Z",
    "duration_seconds": 45.2
  }
}
```

#### List Backtests
```
GET /api/v1/backtests?strategy_id=uuid&skip=0&limit=10
```

Get paginated list of backtests, optionally filtered by strategy.

---

### Validation (Walk-Forward)

#### Run Validation
```
POST /api/v1/validation/run
```

Start walk-forward validation in the background.

**Request:**
```json
{
  "strategy_id": "uuid",
  "start_date": "2023-01-01",
  "end_date": "2024-01-01",
  "window_size_days": 90,
  "train_size_days": 180,
  "initial_capital": 100000
}
```

**Response:**
```json
{
  "validation_id": "uuid",
  "status": "running",
  "message": "Validation started",
  "created_at": "2024-01-15T10:30:00.000Z"
}
```

#### Check Validation Status
```
GET /api/v1/validation/{validation_id}/status
```

Check validation progress.

#### Get Validation Results
```
GET /api/v1/validation/{validation_id}
```

Get completed validation with stability scores.

**Response:**
```json
{
  "validation_id": "uuid",
  "strategy_id": "uuid",
  "status": "completed",
  "windows": [
    {
      "window_id": 0,
      "train_start": "2023-01-01",
      "train_end": "2023-06-30",
      "test_start": "2023-06-30",
      "test_end": "2023-09-28",
      "train_sharpe": 2.0,
      "test_sharpe": 1.7,
      "train_return": 15.5,
      "test_return": 12.3,
      "train_drawdown": -10.0,
      "test_drawdown": -14.5,
      "degradation": 15.0
    }
  ],
  "metrics": {
    "num_windows": 3,
    "avg_train_sharpe": 2.0,
    "avg_test_sharpe": 1.7,
    "avg_degradation": 15.0,
    "stability_score": 85.0,
    "passed": true
  },
  "start_date": "2023-01-01",
  "end_date": "2024-01-01",
  "completed_at": "2024-01-15T11:00:00.000Z",
  "duration_seconds": 1800.5
}
```

#### List Validations
```
GET /api/v1/validation?strategy_id=uuid&skip=0&limit=10
```

Get paginated list of validations.

---

### Gates

#### Run Dev Gate
```
POST /api/v1/gates/dev-gate
```

Run development gate checks (type checking, linting, unit tests, determinism).

**Request:**
```json
{
  "strategy_id": "uuid"
}
```

**Response:**
```json
{
  "strategy_id": "uuid",
  "gate_status": "passed",
  "passed": true,
  "checks": [
    {
      "check_name": "Type Checking",
      "passed": true,
      "description": "Mypy type checking passes",
      "message": "No type errors found"
    },
    {
      "check_name": "Linting",
      "passed": true,
      "description": "Pylint linting passes",
      "message": "Code style compliant"
    }
  ],
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

#### Run CRV Gate
```
POST /api/v1/gates/crv-gate
```

Run CRV (Cumulative Risk/Reward) gate checks.

**Response:**
```json
{
  "strategy_id": "uuid",
  "gate_status": "passed",
  "passed": true,
  "min_sharpe_threshold": 0.8,
  "max_drawdown_threshold": -25.0,
  "min_return_threshold": 5.0,
  "actual_sharpe": 1.75,
  "actual_drawdown": -12.5,
  "actual_return": 18.5,
  "sharpe_pass": true,
  "drawdown_pass": true,
  "return_pass": true,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

#### Run Product Gate
```
POST /api/v1/gates/product-gate
```

Run full production gate (combines dev gate, CRV gate, validation).

**Response:**
```json
{
  "strategy_id": "uuid",
  "production_ready": true,
  "dev_gate": { ... },
  "crv_gate": { ... },
  "validation_passed": true,
  "recommendation": "✅ Ready for production deployment",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

#### Get Gate Status
```
GET /api/v1/gates/{strategy_id}/status
```

Get current gate status summary for a strategy.

---

### Reflexion

#### Run Reflexion Iteration
```
POST /api/v1/reflexion/{strategy_id}/run
```

#### Get Reflexion History
```
GET /api/v1/reflexion/{strategy_id}/history
```

---

### Orchestrator

#### Create End-to-End Run
```
POST /api/v1/orchestrator/runs
```

#### List Runs
```
GET /api/v1/orchestrator/runs
```

#### Get Run Status
```
GET /api/v1/orchestrator/runs/{run_id}
```

---

### WebSocket Contract

- Canonical envelope shape:
  - `event`
  - `timestamp`
  - `version`
  - `payload`
- Event taxonomy reference: [../docs/WEBSOCKET_CONTRACT.md](../docs/WEBSOCKET_CONTRACT.md)

---

## Risk Preferences

Risk preferences automatically adjust strategy parameters:

### Conservative
- Lookback: 40 days
- Volatility Target: 0.1 (10%)
- Position Size: 0.5x

### Moderate (Default)
- Lookback: 20 days
- Volatility Target: 0.15 (15%)
- Position Size: 1.0x

### Aggressive
- Lookback: 10 days
- Volatility Target: 0.25 (25%)
- Position Size: 2.0x

## Strategy Types

The API supports 8 strategy types:

1. **ts_momentum** - Time series momentum trading
2. **pairs_trading** - Statistical arbitrage between paired instruments
3. **stat_arb** - Statistical arbitrage strategies
4. **ml_classifier** - Machine learning based classification
5. **volatility_trading** - Volatility-based trading
6. **mean_reversion** - Mean reversion strategies
7. **trend_following** - Trend following strategies
8. **market_neutral** - Market-neutral long/short strategies

## Example Workflow

### 1. Generate Strategies

```bash
curl -X POST "http://localhost:8000/api/v1/strategies/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Capture momentum in growth stocks",
    "risk_preference": "moderate",
    "max_strategies": 5
  }'
```

### 2. Run Backtest

```bash
curl -X POST "http://localhost:8000/api/v1/backtests/run" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "strategy-uuid",
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "initial_capital": 100000
  }'
```

### 3. Run Validation

```bash
curl -X POST "http://localhost:8000/api/v1/validation/run" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "strategy-uuid",
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "window_size_days": 90,
    "train_size_days": 180
  }'
```

### 4. Run Production Gate

```bash
curl -X POST "http://localhost:8000/api/v1/gates/product-gate" \
  -H "Content-Type: application/json" \
  -d '{"strategy_id": "strategy-uuid"}'
```

## Python Client Example

```python
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        # Generate strategies
        response = await client.post(
            "http://localhost:8000/api/v1/strategies/generate",
            json={
                "goal": "Find profitable momentum patterns",
                "risk_preference": "moderate",
                "max_strategies": 5,
            }
        )
        strategies = response.json()
        strategy_id = strategies["strategies"][0]["strategy_type"]
        
        # Run backtest
        backtest_resp = await client.post(
            "http://localhost:8000/api/v1/backtests/run",
            json={
                "strategy_id": strategy_id,
                "start_date": "2023-01-01",
                "end_date": "2024-01-01",
            }
        )
        backtest = backtest_resp.json()
        
        # Check result
        result = await client.get(
            f"http://localhost:8000/api/v1/backtests/{backtest['backtest_id']}"
        )
        print(result.json())

asyncio.run(main())
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Strategy not found",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

HTTP Status Codes:
- `200`: Success
- `400`: Bad request (validation error)
- `404`: Resource not found
- `500`: Internal server error

## Environment Variables

Configure via environment or `.env` file:

```env
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True
LOG_LEVEL=info
```

## Performance Considerations

- **Strategy Generation**: ~100-200ms per request
- **Backtest**: 30-300s depending on date range
- **Validation**: 5-30 minutes depending on window configuration
- **Gates**: <1s for gate checks

## Production Deployment

For production, consider:

1. **Database**: Replace in-memory storage with PostgreSQL
2. **Task Queue**: Use Celery/RQ for background jobs
3. **Caching**: Add Redis caching for strategy results
4. **Authentication**: Add JWT/OAuth2 authentication
5. **Rate Limiting**: Implement rate limiting per client
6. **Monitoring**: Add Prometheus metrics and ELK logging
7. **Load Balancing**: Deploy multiple API instances behind a load balancer

## Contributing

To extend the API:

1. Add new schema in `api/schemas/`
2. Create router in `api/routers/`
3. Include router in `api/main.py`
4. Document in API docs
5. Add tests

## License

See root LICENSE file.
