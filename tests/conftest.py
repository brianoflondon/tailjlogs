"""Pytest configuration and fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def test_data_file(fixtures_dir: Path) -> Path:
    """Return path to test_data.jsonl."""
    return fixtures_dir / "test_data.jsonl"


@pytest.fixture
def test_data2_file(fixtures_dir: Path) -> Path:
    """Return path to test_data2.jsonl."""
    return fixtures_dir / "test_data2.jsonl"


@pytest.fixture
def sample_log_entry() -> dict:
    """Return a sample log entry for testing."""
    return {
        "level": "INFO",
        "timestamp": "2026-01-15T15:07:31.332918+00:00",
        "message": "Test message",
        "module": "test_module",
        "line": 42,
        "logger": "test_logger",
        "function": "test_function",
    }


@pytest.fixture
def sample_debug_entry() -> dict:
    """Return a sample DEBUG log entry."""
    return {
        "level": "DEBUG",
        "timestamp": "2026-01-15T15:07:29.609132+00:00",
        "message": "Debug message",
        "module": "debug_module",
        "line": 10,
    }


@pytest.fixture
def sample_error_entry() -> dict:
    """Return a sample ERROR log entry."""
    return {
        "level": "ERROR",
        "timestamp": "2026-01-15T15:07:31.000000+00:00",
        "message": "Error occurred",
        "module": "error_module",
        "line": 99,
    }
