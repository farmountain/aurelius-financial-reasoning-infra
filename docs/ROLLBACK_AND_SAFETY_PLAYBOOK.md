# Rollback and Safety Playbook

## Staged Rollout Flags

- `ENABLE_TRUTH_BACKTESTS`
- `ENABLE_TRUTH_VALIDATION`
- `ENABLE_TRUTH_GATES`

Set a flag to `false` to stop that truth-path route class during rollout.

## Trigger Conditions for Rollback

Rollback should be initiated when any of the following occurs:

1. sustained parity failures (`parity_check_failed`)
2. deterministic replay failures (`replay_pass=false`)
3. repeated production promotion blocks from lineage gaps
4. materially increased route latency beyond agreed SLO

## Immediate Rollback Actions

1. Set relevant `ENABLE_TRUTH_*` flag(s) to `false`.
2. Redeploy API with updated environment.
3. Confirm status endpoints show blocked execution mode.
4. Preserve failed run artifacts for investigation.

## Recovery Checklist

1. Fix root cause.
2. Run end-to-end acceptance script.
3. Re-enable flags progressively.
4. Confirm gate evidence passes before production claims.
