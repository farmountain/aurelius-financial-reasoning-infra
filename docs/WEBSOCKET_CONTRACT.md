# WebSocket Contract

Canonical envelope used by backend emitters and dashboard listeners:

```json
{
  "event": "strategy_created",
  "timestamp": "2026-02-15T12:34:56.000000",
  "version": "1.0",
  "payload": {}
}
```

## Supported events

- `connected`
- `subscribed`
- `unsubscribed`
- `pong`
- `strategy_created`
- `backtest_started`
- `backtest_completed`
- `backtest_failed`
- `validation_completed`
- `gate_verified`
- `reflexion_iteration_created`
- `orchestrator_run_created`
- `orchestrator_stage_updated`

Any contract drift between backend and dashboard should fail CI via tests.
