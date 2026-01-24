.PHONY: fmt fmt-check clippy test ci

# Autoformat all code
fmt:
	cargo fmt

# Check formatting without modifying files
fmt-check:
	cargo fmt --check

# Run clippy with recommended warnings (Sprint 1: no PR failures on warnings)
clippy:
	cargo clippy --all-targets --all-features -- -W clippy::all -W clippy::pedantic

# Run all tests
test:
	cargo test --all

# Run full CI pipeline: format check, clippy, and tests
ci: fmt-check clippy test
	@echo "✓ All CI gates passed!"
