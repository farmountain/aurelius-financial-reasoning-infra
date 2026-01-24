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

- Run `cargo fmt` to format your code
- Run `cargo clippy` to check for common mistakes and improve code quality
- Fix all clippy warnings before submitting a PR

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
2. Ensure code is formatted: `cargo fmt --all -- --check`
3. Ensure no clippy warnings: `cargo clippy --all -- -D warnings`
4. Update documentation as needed
5. Describe your changes in the PR description
6. Link any related issues

## Questions?

If you have questions about contributing, please open an issue for discussion.

## License

By contributing to AURELIUS, you agree that your contributions will be licensed under the Apache License 2.0.
