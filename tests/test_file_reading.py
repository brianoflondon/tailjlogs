"""Tests for file reading functions."""

from pathlib import Path

import pytest

from tailjlogs import get_jsonl_files, get_timestamp_from_line, read_last_n_lines


class TestGetJsonlFiles:
    """Tests for get_jsonl_files function."""

    def test_single_file(self, test_data_file: Path):
        """Test getting a single file."""
        result = get_jsonl_files(str(test_data_file))
        assert len(result) == 1
        assert result[0] == str(test_data_file)

    def test_directory(self, fixtures_dir: Path):
        """Test getting files from directory."""
        result = get_jsonl_files(str(fixtures_dir))
        assert len(result) >= 2  # Should find both test data files
        for path in result:
            assert ".jsonl" in path

    def test_nonexistent_path(self, tmp_path: Path):
        """Test with non-existent path."""
        result = get_jsonl_files(str(tmp_path / "nonexistent"))
        assert result == []

    def test_empty_directory(self, tmp_path: Path):
        """Test with empty directory."""
        result = get_jsonl_files(str(tmp_path))
        assert result == []


class TestGetTimestampFromLine:
    """Tests for get_timestamp_from_line function."""

    def test_valid_timestamp(self):
        """Test parsing valid timestamp."""
        line = '{"timestamp": "2026-01-15T15:07:31.332918+00:00", "level": "INFO"}'
        result = get_timestamp_from_line(line)
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 15

    def test_invalid_json(self):
        """Test with invalid JSON."""
        from datetime import datetime, timezone

        result = get_timestamp_from_line("not json")
        assert result == datetime.min.replace(tzinfo=timezone.utc)

    def test_missing_timestamp(self):
        """Test with missing timestamp field."""
        from datetime import datetime, timezone

        line = '{"level": "INFO", "message": "test"}'
        result = get_timestamp_from_line(line)
        assert result == datetime.min.replace(tzinfo=timezone.utc)

    def test_naive_and_aware_timestamps(self):
        """Test that naive timestamps are assumed UTC and comparisons work."""
        naive = '{"timestamp": "2026-01-15T11:00:00", "level": "INFO"}'
        aware = '{"timestamp": "2026-01-15T10:00:00+00:00", "level": "INFO"}'

        t_naive = get_timestamp_from_line(naive)
        t_aware = get_timestamp_from_line(aware)

        assert t_naive.tzinfo is not None
        assert t_aware.tzinfo is not None
        # aware 10:00 should be before naive 11:00 (both interpreted as UTC)
        assert t_aware < t_naive


@pytest.mark.asyncio
class TestReadLastNLines:
    """Tests for read_last_n_lines function."""

    async def test_reads_last_lines(self, test_data_file: Path):
        """Test reading last N lines from file."""
        lines = await read_last_n_lines(str(test_data_file), 5)
        assert len(lines) == 5

    async def test_reads_all_if_less_than_n(self, tmp_path: Path):
        """Test reading all lines if file has fewer than N."""
        test_file = tmp_path / "small.jsonl"
        test_file.write_text('{"line": 1}\n{"line": 2}\n')

        lines = await read_last_n_lines(str(test_file), 10)
        assert len(lines) == 2

    async def test_empty_file(self, tmp_path: Path):
        """Test reading empty file."""
        test_file = tmp_path / "empty.jsonl"
        test_file.write_text("")

        lines = await read_last_n_lines(str(test_file), 10)
        assert lines == []

    async def test_returns_lines_in_order(self, tmp_path: Path):
        """Test that lines are returned in correct order."""
        test_file = tmp_path / "ordered.jsonl"
        test_file.write_text('{"n": 1}\n{"n": 2}\n{"n": 3}\n')

        lines = await read_last_n_lines(str(test_file), 3)
        assert '{"n": 1}' in lines[0]
        assert '{"n": 3}' in lines[2]
