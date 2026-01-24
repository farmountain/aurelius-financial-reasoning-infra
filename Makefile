.PHONY: fmt fmt-check clippy test ci

# Autoformat all code
fmt:
	cargo fmt

# Check formatting without modifying files (CI gate: fails on format violations)
fmt-check:
	cargo fmt --check

# Run clippy with warnings enabled (Sprint 1: shows warnings but does NOT fail)
clippy:
	@echo "Running clippy (Sprint 1: warnings only, no failures)..."
	cargo clippy --all-targets --all-features -- -W clippy::all || true

# Run all tests
test:
	cargo test --all

# Run full CI pipeline: format check, clippy, and tests
ci: fmt-check clippy test
	@echo "✓ All CI gates passed!"
