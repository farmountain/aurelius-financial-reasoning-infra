## Context

A verification pass identified residual release-trust gaps after major stabilization work: acceptance evidence still includes gate-path failures in its latest appended runs, API README examples contain malformed executable content, Orchestrator retains a legacy run-history fallback in first-run launch logic, and trust-critical status docs still include wording that can be interpreted as stronger than evidence-gated maturity.

This change is intentionally narrow and corrective. It should close high-impact trust gaps without introducing architectural churn.

## Goals / Non-Goals

**Goals:**
- Produce current acceptance evidence that is explicit about environment and gate-path outcomes.
- Make API README request/response examples executable and contract-consistent.
- Remove residual Orchestrator dependence on run history for first-run execution.
- Align trust-critical maturity language with evidence-gated interpretation.
- Add or update guardrail tests/checks to prevent recurrence.

**Non-Goals:**
- Re-architect gate decision logic or acceptance orchestration flow.
- Introduce new trading or strategy-generation algorithms.
- Redesign dashboard IA or visual language.
- Rewrite all historical docs beyond trust-critical sections.

## Decisions

### Decision 1: Evidence quality is treated as a first-class capability
- We add a dedicated capability (`acceptance-evidence-quality`) instead of burying evidence requirements under generic docs updates.
- Rationale: release trust depends on evidence freshness and interpretability, not only code correctness.
- Alternative considered: keep evidence checks under documentation capability only (rejected: too weakly coupled to runtime outcomes).

### Decision 2: Orchestrator first-run launch uses strategy state only
- Start-run logic MUST resolve from selected/generated strategies, not prior runs.
- Rationale: hidden dependency on prior runs breaks clean-state UX guarantees.
- Alternative considered: keep run fallback as “safety” path (rejected: preserves non-deterministic UX behavior on clean environments).

### Decision 3: API README examples are validated as executable contracts
- Response/request examples are treated as testable artifacts, with JSON blocks kept syntactically valid and policy prose outside payload examples.
- Rationale: malformed examples create integration failures despite correct backend behavior.
- Alternative considered: rely on reviewer/manual docs edits (rejected: repeated regressions).

### Decision 4: Historical status docs keep snapshot framing with strict caveats
- Existing historical summary statements remain but are explicitly bounded by evidence-gated maturity language.
- Rationale: preserve historical context while preventing overclaiming.
- Alternative considered: remove historical claims entirely (rejected: loses useful project history).

## Risks / Trade-offs

- [Acceptance runs can still fail due to environment/data conditions] → Mitigation: classify environment caveats explicitly and include at least one clean contract-valid gate-path run in evidence.
- [Docs edits may drift again] → Mitigation: keep docs consistency checks in CI and extend checks for malformed JSON examples.
- [Orchestrator fallback removal could expose missing-strategy edge cases] → Mitigation: keep explicit “generate strategy” affordance and user-facing error state.
- [Narrow-scope change may leave non-critical wording debt elsewhere] → Mitigation: scope strict checks to trust-critical files first, then expand incrementally.

## Migration Plan

1. Evidence refresh
   - Run live acceptance flow in a known-good environment.
   - Append evidence block with explicit environment and gate-path outcomes.
2. API docs correction
   - Fix malformed strategy generation response JSON in `api/README.md`.
   - Move policy prose outside JSON examples.
3. UX correction
   - Remove `runs[0]?.strategy_id` fallback from Orchestrator start logic.
   - Ensure selection/generation path remains executable in empty-state.
4. Messaging alignment
   - Reword trust-critical status lines in `CURRENT_STATUS.md` and `PROJECT_COMPLETE.md` to reinforce evidence-gated interpretation.
5. Guardrails
   - Update/extend docs and regression checks for the fixed gaps.

Rollback strategy:
- Revert docs/UX patches independently if they introduce regressions.
- Keep previous acceptance sections as historical entries while marking superseded runs.

## Open Questions

- Should acceptance evidence require at least one gate-path success in every environment class, or permit only “contract-valid failures” for constrained environments?
- Should status docs enforce a standardized disclaimer block format across all snapshot files?
- Should API README example validation move from script-level checks to schema-driven extraction tests?
