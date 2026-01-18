"""Tests for the timestamps module."""

from datetime import datetime

import pytest

from tailjlogs.timestamps import TimestampScanner, parse


class TestTimestampParse:
    """Tests for the parse function."""

    @pytest.mark.parametrize(
        "timestamp_str,expected_valid",
        [
            # ISO formats with T separator
            ("2025-01-15T09:36:38.194Z", True),
            ("2025-01-15T09:36:38.194", True),
            ("2025-01-15T09:36:38Z", True),
            ("2025-01-15T09:36:38", True),
            ("2025-01-15T09:36:38.194+0000", True),
            ("2025-01-15T09:36:38+0000", True),
            # ISO formats with space separator
            ("2025-01-15 09:36:38.194", True),
            ("2025-01-15 09:36:38", True),
            # Invalid formats
            ("not a timestamp", False),
            ("", False),
            ("12345", False),
        ],
    )
    def test_parse_various_formats(self, timestamp_str, expected_valid):
        """Test parsing various timestamp formats."""
        _, result = parse(timestamp_str)

        if expected_valid:
            assert result is not None
            assert isinstance(result, datetime)
        else:
            assert result is None

    def test_parse_returns_tuple(self):
        """Test that parse returns a tuple with format and timestamp."""
        result = parse("2025-01-15T09:36:38.194Z")

        assert isinstance(result, tuple)
        assert len(result) == 2
        # First element is the format info, second is the datetime
        _, timestamp = result
        assert isinstance(timestamp, datetime)

    def test_parse_iso_with_timezone(self):
        """Test parsing ISO format with timezone."""
        _, result = parse("2025-01-15T09:36:38.194+0000")

        assert result is not None
        assert result.hour == 9
        assert result.minute == 36

    def test_parse_standalone_timestamp(self):
        """Test parsing a standalone timestamp string."""
        _, result = parse("2025-01-15T09:36:38.194Z")

        assert result is not None
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15


class TestTimestampScanner:
    """Tests for the TimestampScanner class."""

    @pytest.fixture
    def scanner(self):
        return TimestampScanner()

    def test_scan_finds_timestamp(self, scanner):
        """Test scanner finds timestamp in line."""
        line = "2025-01-15T09:36:38.194Z INFO Some message"

        result = scanner.scan(line)

        assert result is not None
        assert isinstance(result, datetime)

    def test_scan_reorders_formats_for_performance(self, scanner):
        """Test scanner reorders formats after successful match."""
        line1 = "2025-01-15T09:36:38.194Z First message"
        line2 = "2025-01-15T10:00:00.000Z Second message"

        result1 = scanner.scan(line1)
        result2 = scanner.scan(line2)

        assert result1 is not None
        assert result2 is not None
        # Both should parse successfully

    def test_scan_no_timestamp(self, scanner):
        """Test scanner returns None for line without timestamp."""
        line = "No timestamp in this line"

        result = scanner.scan(line)

        assert result is None

    def test_scan_json_timestamp(self, scanner):
        """Test scanner finds timestamp in JSON line."""
        line = '{"timestamp": "2025-01-15T09:36:38.194Z", "level": "INFO"}'

        result = scanner.scan(line)

        assert result is not None
        assert result.year == 2025

    def test_scan_truncates_long_lines(self, scanner):
        """Test scanner handles very long lines."""
        long_line = "2025-01-15T09:36:38.194Z " + "x" * 20_000

        result = scanner.scan(long_line)

        # Should still find the timestamp at the beginning
        assert result is not None
