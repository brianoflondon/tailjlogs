"""Tests for the format_parser module."""

import json

import pytest

from tailjlogs.format_parser import DefaultLogFormat, FormatParser, JSONLogFormat


class TestJSONLogFormat:
    """Tests for JSONLogFormat class."""

    @pytest.fixture
    def parser(self):
        return JSONLogFormat()

    def test_parse_valid_jsonl_with_all_fields(self, parser):
        """Test parsing a complete JSONL log entry."""
        line = json.dumps(
            {
                "timestamp": "2025-01-15T09:36:38.194Z",
                "level": "INFO",
                "message": "User logged in",
                "module": "auth",
                "line": 42,
            }
        )

        result = parser.parse(line)

        assert result is not None
        timestamp, raw_line, text = result
        assert raw_line == line
        assert "User logged in" in text.plain
        assert "INFO" in text.plain
        assert "auth" in text.plain

    def test_parse_minimal_jsonl(self, parser):
        """Test parsing JSONL with only message field."""
        line = json.dumps({"message": "Simple message"})

        result = parser.parse(line)

        assert result is not None
        _, _, text = result
        assert "Simple message" in text.plain

    def test_parse_alternative_field_names(self, parser):
        """Test parsing JSONL with alternative field names."""
        line = json.dumps(
            {
                "time": "2025-01-15T09:36:38.194Z",
                "levelname": "WARNING",
                "msg": "Alternative fields",
                "logger": "mylogger",
                "lineno": 100,
            }
        )

        result = parser.parse(line)

        assert result is not None
        _, _, text = result
        assert "WARNING" in text.plain
        assert "Alternative fields" in text.plain
        assert "mylogger" in text.plain

    def test_parse_empty_line(self, parser):
        """Test parsing empty line returns None."""
        result = parser.parse("")
        assert result is None

    def test_parse_whitespace_only(self, parser):
        """Test parsing whitespace-only line returns None."""
        result = parser.parse("   \n\t  ")
        assert result is None

    def test_parse_invalid_json(self, parser):
        """Test parsing invalid JSON returns None."""
        result = parser.parse("not valid json {")
        assert result is None

    def test_parse_plain_text(self, parser):
        """Test parsing plain text returns None."""
        result = parser.parse("Just a plain text log line")
        assert result is None

    @pytest.mark.parametrize(
        "level,expected_in_output",
        [
            ("DEBUG", "DEBUG"),
            ("INFO", "INFO"),
            ("WARNING", "WARNING"),
            ("ERROR", "ERROR"),
            ("CRITICAL", "CRITICAL"),
            ("debug", "DEBUG"),  # lowercase should be uppercased
            ("info", "INFO"),
        ],
    )
    def test_parse_different_log_levels(self, parser, level, expected_in_output):
        """Test parsing different log levels."""
        line = json.dumps({"level": level, "message": "test"})

        result = parser.parse(line)

        assert result is not None
        _, _, text = result
        assert expected_in_output in text.plain

    def test_format_timestamp(self, parser):
        """Test timestamp formatting to compact form."""
        result = parser._format_timestamp("2025-01-15T09:36:38.194567Z")

        # Should be MM-DDThh:mm:ss.mmm format
        assert result.startswith("01-15T09:36:38.")

    def test_get_field_with_different_names(self, parser):
        """Test _get_field tries multiple field names."""
        data = {"msg": "test message"}

        result = parser._get_field(data, ["message", "msg", "text"])

        assert result == "test message"

    def test_get_field_returns_none_for_missing(self, parser):
        """Test _get_field returns None when no field matches."""
        data = {"other": "value"}

        result = parser._get_field(data, ["message", "msg"])

        assert result is None


class TestDefaultLogFormat:
    """Tests for DefaultLogFormat class."""

    @pytest.fixture
    def parser(self):
        return DefaultLogFormat()

    def test_parse_plain_text(self, parser):
        """Test parsing plain text log line."""
        line = "2025-01-15 09:36:38 INFO This is a plain log"

        result = parser.parse(line)

        assert result is not None
        timestamp, raw_line, text = result
        assert raw_line == line
        assert timestamp is None  # DefaultLogFormat doesn't extract timestamps

    def test_parse_empty_line(self, parser):
        """Test parsing empty line."""
        result = parser.parse("")

        assert result is not None
        _, raw_line, _ = result
        assert raw_line == ""


class TestFormatParser:
    """Tests for the main FormatParser class."""

    @pytest.fixture
    def parser(self):
        return FormatParser()

    def test_parse_jsonl_line(self, parser):
        """Test FormatParser correctly identifies and parses JSONL."""
        line = json.dumps(
            {
                "timestamp": "2025-01-15T09:36:38.194Z",
                "level": "INFO",
                "message": "Test message",
            }
        )

        result = parser.parse(line)

        assert result is not None
        _, raw_line, text = result
        assert raw_line == line
        assert "INFO" in text.plain

    def test_parse_plain_text_fallback(self, parser):
        """Test FormatParser falls back to DefaultLogFormat for plain text."""
        line = "Just a plain text log line"

        result = parser.parse(line)

        assert result is not None
        _, raw_line, _ = result
        assert raw_line == line

    def test_parse_truncates_long_lines(self, parser):
        """Test that very long lines are truncated."""
        long_line = "x" * 20_000

        result = parser.parse(long_line)

        # Should not crash, line should be handled
        assert result is not None

    def test_parse_empty_returns_empty_text(self, parser):
        """Test parsing empty line returns empty Text."""
        result = parser.parse("")

        timestamp, raw_line, text = result
        assert timestamp is None
        assert raw_line == ""
        assert text.plain == ""

    def test_format_priority_caching(self, parser):
        """Test that successful format is moved to front for caching."""
        # Parse JSONL first
        json_line = json.dumps({"message": "test"})
        parser.parse(json_line)

        # JSONLogFormat should now be first in the list
        assert isinstance(parser._formats[0], JSONLogFormat)
