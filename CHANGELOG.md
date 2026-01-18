# Changelog

All notable changes to this project will be documented in this file.

The format is based on "Keep a Changelog" and this project adheres to Semantic Versioning.

## [2.0.0] - 2026-01-18

### Changed

- **BREAKING:** Complete rebase of tailjlogs on the [toolong](https://github.com/Textualize/toolong) codebase by Will McGugan / Textualize.
- **feat:** Full interactive TUI powered by Textual framework with search, filtering, and navigation.
- **feat:** Support for viewing multiple log files in tabs or merged view.
- **feat:** Live tail mode with automatic scrolling and file rotation detection.
- **feat:** Syntax highlighting for JSON, Common Log Format, and Combined Log Format.
- **feat:** Compact JSONL formatting showing `timestamp level module line : message`.
- **feat:** Press `f` to filter/search, arrow keys to navigate, Enter to expand JSON details.
- **feat:** Added `q` and `Escape` keybindings to quit (avoids VS Code Ctrl+Q conflict).
- **chore:** Migrated from typer to Click for CLI.
- **chore:** Migrated from watchdog to Textual's built-in file watching.
- **chore:** New `src/` layout with hatchling build system.
- **chore:** Added `tl` as a short alias command.
- **docs:** Updated README with toolong credits and new usage instructions.
- **docs:** Updated LICENSE with dual copyright (original toolong MIT license preserved).

### Added

- **test:** New pytest test suite for format parsing, timestamp handling, and CLI.
  - `test_format_parser.py` - 24 tests for JSONL/log format detection and parsing.
  - `test_timestamps.py` - 19 tests for timestamp parsing and scanner caching.
  - `test_cli.py` - 4 tests for CLI options and help.

## [1.0.4] - 2026-01-17

### Fixed

- **fix:** Normalize timestamps to timezone-aware UTC datetimes when reading logs so merging/sorting across files does not raise TypeError (naive timestamps are interpreted as UTC).
- **test:** Add tests to ensure naive and aware timestamps compare consistently.

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
