"""Tests for log formatting functions."""

import json
import re

from tailjlogs import (
    LEVEL_COLORS,
    LEVEL_PRIORITY,
    RESET_COLOR,
    format_log_entry,
    get_short_filename,
    process_line,
    strip_ansi_codes,
)


class TestStripAnsiCodes:
    """Tests for strip_ansi_codes function."""

    def test_removes_color_codes(self):
        """Test that ANSI color codes are removed."""
        colored = f"{LEVEL_COLORS['INFO']}test message{RESET_COLOR}"
        assert strip_ansi_codes(colored) == "test message"

    def test_plain_text_unchanged(self):
        """Test that plain text is unchanged."""
        plain = "plain text message"
        assert strip_ansi_codes(plain) == plain

    def test_multiple_codes(self):
        """Test removal of multiple ANSI codes."""
        text = "\033[31mred\033[0m \033[32mgreen\033[0m"
        assert strip_ansi_codes(text) == "red green"


class TestGetShortFilename:
    """Tests for get_short_filename function."""

    def test_removes_jsonl_extension(self):
        """Test that .jsonl extension is removed."""
        assert get_short_filename("/path/to/file.jsonl") == "file"

    def test_removes_jsonl_rotation_suffix(self):
        """Test that rotation suffix is removed."""
        assert get_short_filename("/path/to/file.jsonl.1") == "file"
        assert get_short_filename("/path/to/file.jsonl.10") == "file"

    def test_removes_log_extension(self):
        """Test that .log extension is removed."""
        assert get_short_filename("/path/to/file.log") == "file"

    def test_truncates_long_names(self):
        """Test that long names are truncated."""
        long_name = "this_is_a_very_long_filename.jsonl"
        result = get_short_filename(f"/path/to/{long_name}", max_len=10)
        assert len(result) == 10
        assert result.endswith("…")

    def test_short_names_unchanged(self):
        """Test that short names are not truncated."""
        result = get_short_filename("/path/to/short.jsonl", max_len=15)
        assert result == "short"


class TestFormatLogEntry:
    """Tests for format_log_entry function."""

    def test_formats_basic_entry(self, sample_log_entry):
        """Test formatting a basic log entry."""
        result = format_log_entry(sample_log_entry, show_colors=False)
        assert result is not None
        assert "INFO" in result
        assert "Test message" in result
        assert "test_module" in result

    def test_includes_timestamp(self, sample_log_entry):
        """Test that timestamp is included."""
        result = format_log_entry(sample_log_entry, show_colors=False)
        # Should contain time portion
        assert "15:07:31" in result or "07:31" in result

    def test_colored_output(self, sample_log_entry):
        """Test that colors are applied."""
        result = format_log_entry(sample_log_entry, show_colors=True)
        assert LEVEL_COLORS["INFO"] in result
        assert RESET_COLOR in result

    def test_no_colors_when_disabled(self, sample_log_entry):
        """Test that colors are not applied when disabled."""
        result = format_log_entry(sample_log_entry, show_colors=False)
        assert LEVEL_COLORS["INFO"] not in result
        assert RESET_COLOR not in result

    def test_handles_missing_fields(self):
        """Test handling of entries with missing fields."""
        minimal_entry = {"message": "Just a message"}
        result = format_log_entry(minimal_entry, show_colors=False)
        assert result is not None
        assert "Just a message" in result

    def test_filename_prefix(self, sample_log_entry):
        """Test that filename prefix is included."""
        result = format_log_entry(sample_log_entry, show_colors=False, filename="testfile")
        assert "testfile" in result

    def test_verbose_format(self, sample_log_entry):
        """Test verbose format output."""
        result = format_log_entry(sample_log_entry, show_colors=False, compact=False)
        assert result is not None
        # Verbose format includes logger and function
        assert "test_logger" in result or "test_function" in result


class TestProcessLine:
    """Tests for process_line function."""

    def test_parses_json_line(self, sample_log_entry):
        """Test parsing a JSON line."""
        line = json.dumps(sample_log_entry)
        result = process_line(line, show_colors=False)
        assert result is not None
        assert "Test message" in result

    def test_empty_line_returns_none(self):
        """Test that empty lines return None."""
        assert process_line("") is None
        assert process_line("   ") is None

    def test_invalid_json_returned_as_is(self):
        """Test that invalid JSON is returned as-is."""
        line = "Not valid JSON"
        result = process_line(line, show_colors=False)
        assert result == line

    def test_level_filtering(self, sample_debug_entry, sample_log_entry):
        """Test filtering by log level."""
        debug_line = json.dumps(sample_debug_entry)
        info_line = json.dumps(sample_log_entry)

        # With WARNING filter, DEBUG should be filtered out
        assert process_line(debug_line, min_level="WARNING", show_colors=False) is None
        assert process_line(info_line, min_level="WARNING", show_colors=False) is None

        # With DEBUG filter, both should pass
        assert process_line(debug_line, min_level="DEBUG", show_colors=False) is not None
        assert process_line(info_line, min_level="DEBUG", show_colors=False) is not None

    def test_grep_pattern_include(self, sample_log_entry):
        """Test grep pattern inclusion."""
        line = json.dumps(sample_log_entry)
        pattern = re.compile("Test", re.IGNORECASE)

        result = process_line(line, grep_pattern=pattern, show_colors=False)
        assert result is not None

        # Pattern that doesn't match
        no_match_pattern = re.compile("xyz123", re.IGNORECASE)
        result = process_line(line, grep_pattern=no_match_pattern, show_colors=False)
        assert result is None

    def test_grep_pattern_exclude(self, sample_log_entry):
        """Test grep pattern exclusion."""
        line = json.dumps(sample_log_entry)
        exclude_pattern = re.compile("Test", re.IGNORECASE)

        result = process_line(line, grep_exclude=exclude_pattern, show_colors=False)
        assert result is None

        # Pattern that doesn't match should not exclude
        no_match_pattern = re.compile("xyz123", re.IGNORECASE)
        result = process_line(line, grep_exclude=no_match_pattern, show_colors=False)
        assert result is not None


class TestLevelPriority:
    """Tests for level priority constants."""

    def test_priority_order(self):
        """Test that priorities are in correct order."""
        assert LEVEL_PRIORITY["DEBUG"] < LEVEL_PRIORITY["INFO"]
        assert LEVEL_PRIORITY["INFO"] < LEVEL_PRIORITY["WARNING"]
        assert LEVEL_PRIORITY["WARNING"] < LEVEL_PRIORITY["ERROR"]
        assert LEVEL_PRIORITY["ERROR"] < LEVEL_PRIORITY["CRITICAL"]

    def test_all_levels_have_colors(self):
        """Test that all log levels have associated colors."""
        for level in LEVEL_PRIORITY:
            assert level in LEVEL_COLORS
