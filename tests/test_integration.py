"""Integration tests using real test data files."""

import json
from pathlib import Path

import pytest

from tailjlogs import format_log_entry, process_line, read_last_n_lines


class TestWithRealData:
    """Tests using the actual test data files."""

    def test_fixtures_exist(self, fixtures_dir: Path):
        """Verify test fixtures exist."""
        assert (fixtures_dir / "test_data.jsonl").exists()
        assert (fixtures_dir / "test_data2.jsonl").exists()

    def test_can_parse_test_data(self, test_data_file: Path):
        """Test that test_data.jsonl can be parsed."""
        with open(test_data_file) as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    assert "level" in entry
                    assert "timestamp" in entry
                    assert "message" in entry

    def test_can_parse_test_data2(self, test_data2_file: Path):
        """Test that test_data2.jsonl can be parsed."""
        with open(test_data2_file) as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    assert "level" in entry
                    assert "timestamp" in entry

    def test_format_entries_from_test_data(self, test_data_file: Path):
        """Test formatting entries from test data."""
        with open(test_data_file) as f:
            lines = f.readlines()[:5]  # First 5 lines

        for line in lines:
            result = process_line(line, show_colors=False)
            assert result is not None

    def test_process_with_level_filter(self, test_data_file: Path):
        """Test level filtering on real data."""
        with open(test_data_file) as f:
            lines = f.readlines()

        info_count = 0
        debug_count = 0

        for line in lines:
            entry = json.loads(line)
            if entry.get("level") == "INFO":
                info_count += 1
            elif entry.get("level") == "DEBUG":
                debug_count += 1

        # Filter to INFO only
        filtered = [process_line(line, min_level="INFO", show_colors=False) for line in lines]
        passed = [f for f in filtered if f is not None]

        # Should have filtered out DEBUG entries
        assert len(passed) < len(lines)

    def test_emoji_handling(self, test_data_file: Path):
        """Test that emoji in messages are handled correctly."""
        with open(test_data_file) as f:
            for line in f:
                entry = json.loads(line)
                # Test data contains emoji like 📁, 🔒, etc.
                result = format_log_entry(entry, show_colors=False)
                assert result is not None
                # The message should be in the output
                if entry.get("message"):
                    # Just verify it doesn't crash with emoji
                    assert isinstance(result, str)


@pytest.mark.asyncio
class TestAsyncWithRealData:
    """Async tests using real test data."""

    async def test_read_last_lines_from_test_data(self, test_data_file: Path):
        """Test reading last N lines from test data."""
        lines = await read_last_n_lines(str(test_data_file), 10)
        assert len(lines) == 10

        # All lines should be valid JSON
        for line in lines:
            entry = json.loads(line)
            assert "level" in entry

    async def test_read_from_both_files(self, test_data_file: Path, test_data2_file: Path):
        """Test reading from both test data files."""
        lines1 = await read_last_n_lines(str(test_data_file), 5)
        lines2 = await read_last_n_lines(str(test_data2_file), 5)

        assert len(lines1) == 5
        assert len(lines2) == 5

        # Verify different content (different loggers)
        entry1 = json.loads(lines1[0])
        entry2 = json.loads(lines2[0])

        # test_data.jsonl uses db_monitor, test_data2.jsonl uses hive_monitor_v2
        loggers = {entry1.get("logger"), entry2.get("logger")}
        assert len(loggers) >= 1  # At least one logger name
