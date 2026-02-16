# Release Maturity Guide

AURELIUS capability claims must align with measurable runtime evidence.

## Capability Labels

- **experimental**: early path; not all parity/governance checks are satisfied.
- **validated**: deterministic and lineage-complete with truth parity, but not yet fully production-gated.
- **production**: passes truth parity, determinism, contract parity, and lineage completeness.

## Production Gate Inputs

The release gate evaluates the following evidence:

1. `truth_parity` (CLI/API parity checks)
2. `determinism` (replay pass)
3. `contract_parity` (OpenAPI/client drift checks)
4. `lineage_completeness` (required lineage fields present)

If any required input fails, production promotion is blocked and reasons are persisted.

## External Claims Policy

- Public docs and release notes must use the maturity label from gate evidence.
- Do not label features as production-ready unless the gate outcome is `passed=true` and `maturity_label=production`.
- If a capability regresses, downgrade claims in release notes before shipment.
