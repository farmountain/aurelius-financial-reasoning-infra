# Contributing to AURELIUS Quant Reasoning Model

Thank you for your interest in contributing to AURELIUS! This document provides guidelines for contributing to the project.

## Code of Conduct

Please be respectful and professional in all interactions with the project community.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/AURELIUS_Quant_Reasoning_Model.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Guidelines

### Testing

- Maintain **90%+ test coverage** for critical modules
- All tests must pass before submitting a PR
- Add tests for new features and bug fixes
- Ensure determinism tests pass across multiple runs

### Code Quality

#### Formatting (Enforced)
- **Required**: Run `cargo fmt` to format your code before committing
- **CI Gate**: `cargo fmt --check` will fail the build if code is not properly formatted
- **How to fix**: Run `make fmt` or `cargo fmt --all`

#### Linting (Progressive Ratchet)
- **Current (Sprint 1)**: Run `cargo clippy` to check for common mistakes - warnings are shown but do NOT fail CI
- **How to run**: `make clippy` or `cargo clippy --all-targets --all-features`
- **How to fix warnings**: `cargo clippy --fix --all-targets --all-features`

**Clippy Ratchet Plan:**
This project uses a progressive ratchet approach to improve code quality over time without blocking current development:

- **Sprint 1 (Current)**: Clippy runs in CI but warnings do NOT fail builds. Developers are encouraged to fix warnings when touching related code.
- **Sprint 2**: Deny `clippy::correctness` warnings (bugs and logic errors must be fixed)
- **Sprint 3**: Deny `clippy::perf` warnings (performance issues must be addressed)
- **Sprint 4+**: Consider denying all clippy warnings globally

**Guidelines for handling lints:**
- **DO NOT** add `#![deny(warnings)]` to any crate - use the ratchet plan instead
- If scaffolding or generated code triggers pedantic lints:
  - **Prefer**: Refactor code to satisfy the lint
  - **Alternative**: Add narrowly scoped `#[allow(...)]` attributes at module level with explanatory comments
  - **Avoid**: Global `#[allow(...)]` of large lint groups

**If a new lint rule is added, it must be accompanied by either a code fix in the same PR or a ratchet milestone; do not add rules that fail on existing code.**

### Documentation

- Update documentation for any user-facing changes
- Add doc comments for public APIs
- Update README.md if adding new features or changing usage

### Commit Messages

- Use clear, descriptive commit messages
- Reference issue numbers when applicable
- Follow conventional commit format when possible

## Project Structure

The project is organized as a Cargo workspace with multiple crates:

- **`schema`**: Core traits and data structures
- **`cost`**: Cost model implementations
- **`broker_sim`**: Broker simulator for order execution
- **`engine`**: Backtest engine with portfolio management
- **`crv_verifier`**: Correctness, Robustness, and Validation suite
- **`cli`**: Command-line interface
- **`hipcortex`**: Content-addressed artifact storage
- **`python/aureus`**: Python orchestrator with evidence gates

## Adding New Features

### New Strategy

Implement the `Strategy` trait in `crates/schema/src/lib.rs` and add your strategy implementation to `crates/cli/src/strategies/`.

### New Cost Model

Implement the `CostModel` trait in `crates/schema/src/lib.rs` and add your cost model to `crates/cost/src/`.

### New CRV Rules

Add new verification rules to `crates/crv_verifier/src/lib.rs` and ensure comprehensive test coverage.

## Pull Request Process

1. Ensure all tests pass: `cargo test --all`
2. Ensure code is formatted: `make fmt` or `cargo fmt --all`
3. Run clippy and address relevant warnings: `make clippy`
4. Run the full CI pipeline locally: `make ci`
5. Update documentation as needed
6. Describe your changes in the PR description
7. Link any related issues

## Questions?

If you have questions about contributing, please open an issue for discussion.

## License

By contributing to AURELIUS, you agree that your contributions will be licensed under the Apache License 2.0.
