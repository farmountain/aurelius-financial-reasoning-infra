export const WS_ENVELOPE_VERSION = '1.0';

export const WS_EVENTS = [
  'connected',
  'subscribed',
  'unsubscribed',
  'pong',
  'strategy_created',
  'backtest_started',
  'backtest_completed',
  'backtest_failed',
  'validation_completed',
  'gate_verified',
  'reflexion_iteration_created',
  'orchestrator_run_created',
  'orchestrator_stage_updated',
];

export const WS_SUPPORTED_EVENT_SET = new Set(WS_EVENTS);
