"""Tests for log level filtering functionality."""

import json
import os
import tempfile
from threading import Event

import pytest

from tailjlogs.log_file import LogFile
from tailjlogs.log_lines import LEVEL_FIELDS, LOG_LEVEL_ORDER


class TestLogLevelOrder:
    """Tests for log level order and hierarchy."""

    def test_log_level_order_defined(self):
        """Test that log level order is defined correctly."""
        assert LOG_LEVEL_ORDER["DEBUG"] == 10
        assert LOG_LEVEL_ORDER["INFO"] == 20
        assert LOG_LEVEL_ORDER["WARNING"] == 30
        assert LOG_LEVEL_ORDER["WARN"] == 30
        assert LOG_LEVEL_ORDER["ERROR"] == 40
        assert LOG_LEVEL_ORDER["CRITICAL"] == 50
        assert LOG_LEVEL_ORDER["FATAL"] == 50

    def test_level_fields_defined(self):
        """Test that common level field names are defined."""
        assert "level" in LEVEL_FIELDS
        assert "levelname" in LEVEL_FIELDS
        assert "severity" in LEVEL_FIELDS

    def test_level_hierarchy(self):
        """Test that levels are correctly ordered."""
        assert LOG_LEVEL_ORDER["DEBUG"] < LOG_LEVEL_ORDER["INFO"]
        assert LOG_LEVEL_ORDER["INFO"] < LOG_LEVEL_ORDER["WARNING"]
        assert LOG_LEVEL_ORDER["WARNING"] < LOG_LEVEL_ORDER["ERROR"]
        assert LOG_LEVEL_ORDER["ERROR"] < LOG_LEVEL_ORDER["CRITICAL"]


class TestLevelFilterLogic:
    """Tests for the level filtering logic."""

    @pytest.mark.parametrize(
        "line_level,min_level,should_pass",
        [
            # At threshold - should pass
            ("DEBUG", "DEBUG", True),
            ("INFO", "INFO", True),
            ("WARNING", "WARNING", True),
            ("ERROR", "ERROR", True),
            ("CRITICAL", "CRITICAL", True),
            # Above threshold - should pass
            ("INFO", "DEBUG", True),
            ("WARNING", "DEBUG", True),
            ("ERROR", "DEBUG", True),
            ("CRITICAL", "DEBUG", True),
            ("WARNING", "INFO", True),
            ("ERROR", "INFO", True),
            ("CRITICAL", "INFO", True),
            ("ERROR", "WARNING", True),
            ("CRITICAL", "WARNING", True),
            ("CRITICAL", "ERROR", True),
            # Below threshold - should NOT pass
            ("DEBUG", "INFO", False),
            ("DEBUG", "WARNING", False),
            ("DEBUG", "ERROR", False),
            ("DEBUG", "CRITICAL", False),
            ("INFO", "WARNING", False),
            ("INFO", "ERROR", False),
            ("INFO", "CRITICAL", False),
            ("WARNING", "ERROR", False),
            ("WARNING", "CRITICAL", False),
            ("ERROR", "CRITICAL", False),
        ],
    )
    def test_level_filter_comparison(self, line_level, min_level, should_pass):
        """Test the level comparison logic."""
        min_level_value = LOG_LEVEL_ORDER.get(min_level, 0)
        line_level_value = LOG_LEVEL_ORDER.get(line_level, 0)
        result = line_level_value >= min_level_value
        assert result == should_pass, (
            f"Level {line_level} (value={line_level_value}) >= "
            f"{min_level} (value={min_level_value}) should be {should_pass}"
        )


class TestLevelFilterIntegration:
    """Integration tests for level filtering with JSON parsing."""

    def test_parse_json_with_level_field(self):
        """Test parsing JSON lines with level field."""
        import json

        test_lines = [
            '{"level": "DEBUG", "message": "debug message"}',
            '{"level": "INFO", "message": "info message"}',
            '{"level": "WARNING", "message": "warning message"}',
            '{"level": "ERROR", "message": "error message"}',
        ]

        def check_level(line: str, min_level: str) -> bool:
            """Simulate _check_level_match logic."""
            min_level_value = LOG_LEVEL_ORDER.get(min_level, 0)
            if not min_level_value:
                return True
            try:
                data = json.loads(line.strip())
                if not isinstance(data, dict):
                    return True
                level_str = None
                for field in LEVEL_FIELDS:
                    if field in data:
                        level_str = str(data[field]).upper()
                        break
                if not level_str:
                    return True
                line_level_value = LOG_LEVEL_ORDER.get(level_str, 0)
                return line_level_value >= min_level_value
            except (json.JSONDecodeError, ValueError):
                return True

        # Test INFO filter
        results = [check_level(line, "INFO") for line in test_lines]
        assert results == [False, True, True, True], (
            "INFO filter should exclude DEBUG but include INFO, WARNING, ERROR"
        )

        # Test WARNING filter
        results = [check_level(line, "WARNING") for line in test_lines]
        assert results == [False, False, True, True], (
            "WARNING filter should exclude DEBUG and INFO"
        )

    def test_parse_json_with_alternative_field_names(self):
        """Test parsing JSON with alternative level field names."""
        import json

        test_lines = [
            '{"levelname": "DEBUG", "msg": "debug"}',  # Python logging style
            '{"severity": "INFO", "msg": "info"}',  # GCP style
            '{"log_level": "WARNING", "msg": "warn"}',
        ]

        def get_level(line: str) -> str | None:
            """Extract level from JSON line."""
            try:
                data = json.loads(line.strip())
                for field in LEVEL_FIELDS:
                    if field in data:
                        return str(data[field]).upper()
            except (json.JSONDecodeError, ValueError):
                pass
            return None

        levels = [get_level(line) for line in test_lines]
        assert levels == ["DEBUG", "INFO", "WARNING"]

    def test_non_json_lines_pass_through(self):
        """Test that non-JSON lines are included (pass filter)."""
        import json

        def check_level(line: str, min_level: str) -> bool:
            """Simulate _check_level_match logic."""
            min_level_value = LOG_LEVEL_ORDER.get(min_level, 0)
            try:
                data = json.loads(line.strip())
                if not isinstance(data, dict):
                    return True
                level_str = None
                for field in LEVEL_FIELDS:
                    if field in data:
                        level_str = str(data[field]).upper()
                        break
                if not level_str:
                    return True
                line_level_value = LOG_LEVEL_ORDER.get(level_str, 0)
                return line_level_value >= min_level_value
            except (json.JSONDecodeError, ValueError):
                return True

        # Non-JSON lines should always pass
        assert check_level("plain text log line", "ERROR") is True
        assert check_level("2024-01-15 INFO some log", "ERROR") is True
        assert check_level("not valid json {", "CRITICAL") is True

    def test_json_without_level_field_passes(self):
        """Test that JSON without level field passes filter."""
        import json

        def check_level(line: str, min_level: str) -> bool:
            """Simulate _check_level_match logic."""
            min_level_value = LOG_LEVEL_ORDER.get(min_level, 0)
            try:
                data = json.loads(line.strip())
                if not isinstance(data, dict):
                    return True
                level_str = None
                for field in LEVEL_FIELDS:
                    if field in data:
                        level_str = str(data[field]).upper()
                        break
                if not level_str:
                    return True
                line_level_value = LOG_LEVEL_ORDER.get(level_str, 0)
                return line_level_value >= min_level_value
            except (json.JSONDecodeError, ValueError):
                return True

        # JSON without level field should pass
        assert check_level('{"message": "no level field"}', "ERROR") is True
        assert check_level('{"timestamp": "2024-01-15", "msg": "test"}', "CRITICAL") is True


class TestScanTimestampsBasic:
    """Basic tests for scan_timestamps (filtering now happens at display time)."""

    def test_scan_timestamps_returns_all_lines(self):
        """Test that scan_timestamps returns all lines (no filtering at scan level)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
                f.write(
                    json.dumps(
                        {
                            "level": level,
                            "message": f"{level} message",
                            "timestamp": "2024-01-15T10:00:00.000Z",
                        }
                    )
                    + "\n"
                )
            temp_path = f.name

        try:
            exit_event = Event()
            log_file = LogFile(temp_path)
            log_file.open(exit_event)
            results = []
            for batch in log_file.scan_timestamps():
                results.extend(batch)
            log_file.close()

            assert len(results) == 4, f"Expected 4 lines, got {len(results)}"
        finally:
            os.unlink(temp_path)
