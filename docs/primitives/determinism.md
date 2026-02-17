# Determinism Primitive API

The Determinism Primitive analyzes variance in key metrics across multiple backtest runs to detect non-deterministic behavior that could indicate implementation bugs or data issues.

## Overview

**Endpoint:** `POST /api/primitives/v1/determinism/score`

**Authentication:** API Key (X-API-Key header) or JWT (Authorization: Bearer token)

**Rate Limits:**
- API key: 1,000 requests/hour
- JWT token: 5,000 requests/hour

**Use Cases:**
- Verify backtest engine determinism before production deployment
- Detect data feed inconsistencies causing non-reproducible results
- Validate strategy implementation correctness through reproducibility
- Continuous integration testing of backtesting infrastructure

---

## Request

### Request Body

```json
{
  "strategy_id": "strat-123",
  "runs": [
    {
      "run_id": "run-1",
      "timestamp": "2026-02-16T10:00:00Z",
      "total_return": 0.15,
      "sharpe_ratio": 1.8,
      "max_drawdown": 0.12,
      "trade_count": 42,
      "final_portfolio_value": 115000.0,
      "execution_time_ms": 1250
    },
    {
      "run_id": "run-2",
      "timestamp": "2026-02-16T10:05:00Z",
      "total_return": 0.15,
      "sharpe_ratio": 1.8,
      "max_drawdown": 0.12,
      "trade_count": 42,
      "final_portfolio_value": 115000.0,
      "execution_time_ms": 1230
    }
  ],
  "threshold": 95.0
}
```

### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_id` | string | Yes | Unique identifier for the strategy being tested |
| `runs` | array | Yes | At least 2 backtest runs with identical parameters (see BacktestRun schema) |
| `threshold` | number | No | Minimum score to pass (0-100). Default: 95.0 |

### BacktestRun Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | string | Yes | Unique identifier for this backtest run |
| `timestamp` | string (ISO 8601) | Yes | When the backtest was executed |
| `total_return` | number | Yes | Total return as decimal (0.15 = 15%) |
| `sharpe_ratio` | number | Yes | Sharpe ratio of the strategy |
| `max_drawdown` | number | Yes | Maximum drawdown as decimal (0.12 = 12%) |
| `trade_count` | integer | Yes | Total number of trades executed |
| `final_portfolio_value` | number | Yes | Final portfolio value in currency units |
| `execution_time_ms` | number | Yes | Backtest execution time in milliseconds |

---

## Response

### Response Body

```json
{
  "data": {
    "score": 98.5,
    "passed": true,
    "confidence_interval": 0.95,
    "p_value": 0.001,
    "variance_metrics": {
      "total_return": 0.0,
      "sharpe_ratio": 0.0,
      "max_drawdown": 0.0,
      "trade_count": 0.0
    },
    "issues": []
  },
  "meta": {
    "version": "v1",
    "timestamp": "2026-02-17T14:30:00Z",
    "request_id": "req-abc123"
  },
  "links": {
    "self": "/api/primitives/v1/determinism/score",
    "docs": "/api/primitives/openapi/v1.json"
  }
}
```

### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `data.score` | number | Determinism score from 0-100 (100 = perfect determinism) |
| `data.passed` | boolean | Whether score meets the specified threshold |
| `data.confidence_interval` | number | Statistical confidence level (0-1) |
| `data.p_value` | number | Statistical significance of variance |
| `data.variance_metrics` | object | Variance across runs for each metric (coefficient of variation) |
| `data.issues` | array | List of detected non-deterministic behaviors |
| `meta.version` | string | API version (v1) |
| `meta.timestamp` | string | Response timestamp (ISO 8601) |
| `meta.request_id` | string | Unique request identifier for debugging |
| `links` | object | HATEOAS links to related resources |

### Score Interpretation

- **100**: Perfect determinism - all runs produced identical results
- **95-99**: Slight variance - acceptable for most use cases
- **90-94**: Moderate variance - investigate potential issues
- **< 90**: High variance - likely indicates bugs or data problems

### Common Issues Detected

- `"Varying trade counts detected"` - Different number of trades across runs
- `"High variance in total_return"` - Returns not consistent
- `"High variance in sharpe_ratio"` - Risk-adjusted returns differ
- `"High variance in max_drawdown"` - Drawdowns vary significantly
- `"High variance in final_portfolio_value"` - Portfolio values diverge

---

## Code Examples

### Python

```python
import requests

# Using API key authentication
headers = {
    "X-API-Key": "your_api_key_here",
    "Content-Type": "application/json"
}

payload = {
    "strategy_id": "momentum-v2",
    "runs": [
        {
            "run_id": "run-1",
            "timestamp": "2026-02-16T10:00:00Z",
            "total_return": 0.15,
            "sharpe_ratio": 1.8,
            "max_drawdown": 0.12,
            "trade_count": 42,
            "final_portfolio_value": 115000.0,
            "execution_time_ms": 1250
        },
        {
            "run_id": "run-2",
            "timestamp": "2026-02-16T10:05:00Z",
            "total_return": 0.15,
            "sharpe_ratio": 1.8,
            "max_drawdown": 0.12,
            "trade_count": 42,
            "final_portfolio_value": 115000.0,
            "execution_time_ms": 1230
        }
    ],
    "threshold": 95.0
}

response = requests.post(
    "https://api.aurelius.ai/api/primitives/v1/determinism/score",
    headers=headers,
    json=payload
)

if response.status_code == 200:
    result = response.json()
    score = result["data"]["score"]
    passed = result["data"]["passed"]
    
    print(f"Determinism Score: {score}")
    print(f"Passed: {passed}")
    
    if not passed:
        print("Issues detected:")
        for issue in result["data"]["issues"]:
            print(f"  - {issue}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

### Python with AURELIUS SDK (Coming Soon)

```python
from aurelius import Client

client = Client(api_key="your_api_key_here")

# Score determinism
result = client.determinism.score(
    strategy_id="momentum-v2",
    runs=[run1, run2],
    threshold=95.0
)

print(f"Score: {result.score}")
print(f"Passed: {result.passed}")
```

### cURL

```bash
curl -X POST https://api.aurelius.ai/api/primitives/v1/determinism/score \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "momentum-v2",
    "runs": [
      {
        "run_id": "run-1",
        "timestamp": "2026-02-16T10:00:00Z",
        "total_return": 0.15,
        "sharpe_ratio": 1.8,
        "max_drawdown": 0.12,
        "trade_count": 42,
        "final_portfolio_value": 115000.0,
        "execution_time_ms": 1250
      },
      {
        "run_id": "run-2",
        "timestamp": "2026-02-16T10:05:00Z",
        "total_return": 0.15,
        "sharpe_ratio": 1.8,
        "max_drawdown": 0.12,
        "trade_count": 42,
        "final_portfolio_value": 115000.0,
        "execution_time_ms": 1230
      }
    ],
    "threshold": 95.0
  }'
```

### JavaScript/TypeScript

```javascript
const axios = require('axios');

const headers = {
  'X-API-Key': 'your_api_key_here',
  'Content-Type': 'application/json'
};

const payload = {
  strategy_id: 'momentum-v2',
  runs: [
    {
      run_id: 'run-1',
      timestamp: '2026-02-16T10:00:00Z',
      total_return: 0.15,
      sharpe_ratio: 1.8,
      max_drawdown: 0.12,
      trade_count: 42,
      final_portfolio_value: 115000.0,
      execution_time_ms: 1250
    },
    {
      run_id: 'run-2',
      timestamp: '2026-02-16T10:05:00Z',
      total_return: 0.15,
      sharpe_ratio: 1.8,
      max_drawdown: 0.12,
      trade_count: 42,
      final_portfolio_value: 115000.0,
      execution_time_ms: 1230
    }
  ],
  threshold: 95.0
};

axios.post(
  'https://api.aurelius.ai/api/primitives/v1/determinism/score',
  payload,
  { headers }
)
.then(response => {
  const { data, meta } = response.data;
  console.log(`Determinism Score: ${data.score}`);
  console.log(`Passed: ${data.passed}`);
  console.log(`Request ID: ${meta.request_id}`);
})
.catch(error => {
  console.error('Error:', error.response?.data || error.message);
});
```

---

## Error Responses

### 401 Unauthorized

Missing or invalid authentication credentials.

```json
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Authentication credentials missing or invalid"
  },
  "meta": {
    "timestamp": "2026-02-17T14:30:00Z",
    "request_id": "req-error-123"
  }
}
```

### 422 Validation Error

Invalid request parameters (e.g., fewer than 2 runs, invalid threshold).

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "runs": ["At least 2 runs required for comparison"]
    }
  },
  "meta": {
    "timestamp": "2026-02-17T14:30:00Z",
    "request_id": "req-error-456"
  }
}
```

### 429 Rate Limit Exceeded

Too many requests within the time window.

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Retry after reset time."
  },
  "meta": {
    "timestamp": "2026-02-17T14:30:00Z",
    "request_id": "req-error-789"
  }
}
```

**Headers:**
- `X-RateLimit-Limit`: Total request limit per hour
- `X-RateLimit-Remaining`: Remaining requests in window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

### 503 Service Unavailable

Primitive is disabled via feature flag.

```json
{
  "error": {
    "code": "PRIMITIVE_DISABLED",
    "message": "Determinism primitive is currently disabled"
  },
  "meta": {
    "timestamp": "2026-02-17T14:30:00Z",
    "request_id": "req-error-101"
  }
}
```

---

## Best Practices

### 1. Run Backtests with Identical Parameters

Ensure all runs use the same:
- Data feed and time range
- Initial capital and position sizing
- Risk parameters and stop losses
- Random seed (if applicable)
- Market holidays and calendar

### 2. Minimum of 3 Runs for Statistical Significance

While 2 runs are technically sufficient, 3+ runs provide better statistical confidence in the variance measurements.

### 3. Set Appropriate Thresholds

- **Production strategies**: Use threshold of 99.0 or higher
- **Development/testing**: 95.0 is acceptable
- **Research/exploration**: 90.0 may be tolerable

### 4. Monitor Variance Metrics

Pay attention to which specific metrics show variance:
- **Trade count variance**: Often indicates order routing or execution timing issues
- **Return variance**: Suggests strategy logic problems or data inconsistencies
- **Drawdown variance**: May indicate risk management bugs

### 5. Investigate Issues Promptly

Non-determinism rarely resolves itself. When `passed: false`:
1. Review the specific `issues` array
2. Check data feeds for inconsistencies
3. Verify random seed handling
4. Inspect timestamp-dependent logic
5. Review parallel execution (if applicable)

---

## Health Check

**Endpoint:** `GET /api/primitives/v1/determinism/health`

**Authentication:** None required

**Response:**
```json
{
  "status": "ok"
}
```

Use this endpoint for monitoring and uptime checks.

---

## Related Primitives

- **Risk Primitive** - Validate portfolio risk metrics against thresholds
- **Policy Primitive** - Check regulatory and business rule compliance
- **Gates Primitive** - Gate verification and certification registry
- **Orchestrator Primitive** - Compose multiple primitives into workflows

---

## Support

- **Developer Portal:** https://developers.aurelius.ai
- **API Reference:** https://api.aurelius.ai/api/primitives/openapi/v1.json
- **Email:** api@aurelius.ai
- **Status Page:** https://status.aurelius.ai
