"""Pytest configuration and fixtures."""

import json

import pytest


@pytest.fixture
def sample_jsonl_content():
    """Sample JSONL log content for testing."""
    return [
        {
            "timestamp": "2025-01-15T09:36:38.194Z",
            "level": "INFO",
            "message": "Application started",
            "module": "main",
            "line": 10,
        },
        {
            "timestamp": "2025-01-15T09:36:39.521Z",
            "level": "WARNING",
            "message": "Rate limit approaching",
            "module": "api",
            "line": 156,
        },
        {
            "timestamp": "2025-01-15T09:36:40.003Z",
            "level": "ERROR",
            "message": "Connection timeout",
            "module": "database",
            "line": 89,
        },
    ]


@pytest.fixture
def sample_jsonl_file(tmp_path, sample_jsonl_content):
    """Create a temporary JSONL file for testing."""
    log_file = tmp_path / "test.jsonl"
    with open(log_file, "w") as f:
        for entry in sample_jsonl_content:
            f.write(json.dumps(entry) + "\n")
    return log_file


@pytest.fixture
def sample_plain_log_file(tmp_path):
    """Create a temporary plain text log file for testing."""
    log_file = tmp_path / "test.log"
    log_file.write_text(
        "2025-01-15 09:36:38 INFO Application started\n"
        "2025-01-15 09:36:39 WARNING Rate limit approaching\n"
        "2025-01-15 09:36:40 ERROR Connection timeout\n"
    )
    return log_file


@pytest.fixture
def empty_log_file(tmp_path):
    """Create an empty log file for testing."""
    log_file = tmp_path / "empty.log"
    log_file.write_text("")
    return log_file
