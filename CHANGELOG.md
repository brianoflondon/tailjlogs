# Changelog

All notable changes to this project will be documented in this file.

The format is based on "Keep a Changelog" and this project adheres to Semantic Versioning.

## [1.0.3] - 2026-01-17

### Added

- **feat:** Support rotated JSONL log files (e.g., `app.jsonl.1`, `app.jsonl.2`) when tailing directories. (PR #5)
- **feat:** Dynamically track rotated files during follow mode so rotations are picked up without restarting.
- **test:** Add tests to validate rotated filename discovery and merged ordering.

### Fixed

- **chore:** Minor improvements to file discovery regex and watcher behavior.

## [1.0.2] - 2026-01-17

### Changed

- **docs:** Promote PyPI install in the `README.md` and add a PyPI badge. (PR #4)
- **docs:** Remove duplicate "From PyPI" section to avoid confusion.
- **chore:** Bump package version to `1.0.2` and publish to PyPI.

### CI

- **ci:** Publish workflow triggered by release successfully published `v1.0.2` to PyPI.

## [1.0.1] - 2026-01-16

- Initial PyPI publish and README updates.

## [1.0.0] - 2026-01-16

- Initial package setup and CLI implementation.
