"""Tests for the summary module."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from tailjlogs.summary import (
    LogGroupSummary,
    find_log_files,
    format_summary_json,
    format_summary_text,
    format_timedelta,
    get_filename_root,
    scan_log_file,
    summarize_logs,
)


class TestGetFilenameRoot:
    """Tests for the get_filename_root function."""

    def test_simple_filename(self):
        """Test extracting root from simple filename."""
        assert get_filename_root(Path("app.jsonl")) == "app"
        assert get_filename_root(Path("error.log")) == "error"
        assert get_filename_root(Path("test.json")) == "test"

    def test_rotated_filename(self):
        """Test extracting root from rotated log files."""
        assert get_filename_root(Path("hive_monitor_v2.001.jsonl")) == "hive_monitor_v2"
        assert get_filename_root(Path("api_v2.002.jsonl")) == "api_v2"
        assert get_filename_root(Path("access.003.log")) == "access"

    def test_multiple_rotation_numbers(self):
        """Test with different rotation number lengths."""
        assert get_filename_root(Path("app.0001.jsonl")) == "app"
        assert get_filename_root(Path("server.00001.log")) == "server"

    def test_path_with_directory(self):
        """Test with full path including directory."""
        assert get_filename_root(Path("/var/log/app.jsonl")) == "app"
        assert get_filename_root(Path("/var/log/rotation/app.001.jsonl")) == "app"


class TestFormatTimedelta:
    """Tests for the format_timedelta function."""

    def test_none_timedelta(self):
        """Test formatting None returns N/A."""
        assert format_timedelta(None) == "N/A"

    def test_seconds_only(self):
        """Test formatting seconds."""
        assert format_timedelta(timedelta(seconds=45)) == "45s"
        assert format_timedelta(timedelta(seconds=0)) == "0s"

    def test_minutes_and_seconds(self):
        """Test formatting minutes and seconds."""
        assert format_timedelta(timedelta(minutes=5, seconds=30)) == "5m 30s"

    def test_hours_minutes_seconds(self):
        """Test formatting hours, minutes, and seconds."""
        assert format_timedelta(timedelta(hours=2, minutes=15, seconds=45)) == "2h 15m 45s"

    def test_days(self):
        """Test formatting days."""
        assert format_timedelta(timedelta(days=3, hours=5)) == "3d 5h"
        assert format_timedelta(timedelta(days=1)) == "1d"


class TestLogGroupSummary:
    """Tests for the LogGroupSummary dataclass."""

    def test_timespan_calculation(self):
        """Test timespan property calculation."""
        summary = LogGroupSummary(
            name="test",
            first_log=datetime(2026, 1, 1, 10, 0, 0),
            last_log=datetime(2026, 1, 1, 12, 30, 0),
        )
        assert summary.timespan == timedelta(hours=2, minutes=30)

    def test_timespan_none_when_missing_timestamps(self):
        """Test timespan is None when timestamps are missing."""
        summary = LogGroupSummary(name="test")
        assert summary.timespan is None

        summary2 = LogGroupSummary(name="test", first_log=datetime.now())
        assert summary2.timespan is None

    def test_level_range_single_level(self):
        """Test level range with single level."""
        summary = LogGroupSummary(name="test", level_counts={"INFO": 100})
        assert summary.level_range == "INFO"

    def test_level_range_multiple_levels(self):
        """Test level range with multiple levels."""
        summary = LogGroupSummary(
            name="test",
            level_counts={"DEBUG": 50, "INFO": 100, "ERROR": 10},
        )
        assert summary.level_range == "DEBUG to ERROR"

    def test_level_range_no_levels(self):
        """Test level range with no levels."""
        summary = LogGroupSummary(name="test")
        assert summary.level_range == "N/A"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        summary = LogGroupSummary(
            name="test",
            files=["file1.jsonl", "file2.jsonl"],
            first_log=datetime(2026, 1, 1, 10, 0, 0),
            last_log=datetime(2026, 1, 1, 12, 0, 0),
            level_counts={"INFO": 50, "ERROR": 5},
            total_lines=100,
        )
        result = summary.to_dict()
        assert result["name"] == "test"
        assert len(result["files"]) == 2
        assert result["total_lines"] == 100
        assert "timespan_seconds" in result
        assert result["timespan_seconds"] == 7200.0


class TestFindLogFiles:
    """Tests for the find_log_files function."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory with test log files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # Create some log files
            (base / "app.jsonl").write_text('{"level": "INFO"}\n')
            (base / "error.log").write_text("Error occurred\n")
            (base / "data.txt").write_text("Some data\n")
            (base / "readme.md").write_text("# Readme\n")  # Should be excluded

            # Create subdirectory with files
            subdir = base / "subdir"
            subdir.mkdir()
            (subdir / "nested.jsonl").write_text('{"level": "DEBUG"}\n')

            yield base

    def test_find_files_recursive(self, temp_log_dir):
        """Test finding files recursively."""
        files = list(find_log_files(temp_log_dir, recursive=True))
        filenames = [f.name for f in files]

        assert "app.jsonl" in filenames
        assert "error.log" in filenames
        assert "data.txt" in filenames
        assert "nested.jsonl" in filenames
        assert "readme.md" not in filenames

    def test_find_files_non_recursive(self, temp_log_dir):
        """Test finding files non-recursively."""
        files = list(find_log_files(temp_log_dir, recursive=False))
        filenames = [f.name for f in files]

        assert "app.jsonl" in filenames
        assert "nested.jsonl" not in filenames


class TestScanLogFile:
    """Tests for the scan_log_file function."""

    @pytest.fixture
    def sample_log_file(self):
        """Create a temporary log file with sample data."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            entries = [
                {"timestamp": "2026-01-15T09:00:00Z", "level": "INFO", "message": "Start"},
                {"timestamp": "2026-01-15T09:30:00Z", "level": "WARNING", "message": "Warning"},
                {"timestamp": "2026-01-15T10:00:00Z", "level": "ERROR", "message": "Error"},
                {"timestamp": "2026-01-15T10:30:00Z", "level": "INFO", "message": "End"},
            ]
            for entry in entries:
                f.write(json.dumps(entry) + "\n")
            f.flush()
            yield Path(f.name)
        os.unlink(f.name)

    def test_scan_log_file(self, sample_log_file):
        """Test scanning a log file for statistics."""
        first_ts, last_ts, level_counts, line_count = scan_log_file(sample_log_file)

        assert line_count == 4
        assert first_ts is not None
        assert last_ts is not None
        assert first_ts < last_ts
        assert level_counts["INFO"] == 2
        assert level_counts["WARNING"] == 1
        assert level_counts["ERROR"] == 1


class TestSummarizeLogs:
    """Tests for the summarize_logs function."""

    @pytest.fixture
    def temp_log_structure(self):
        """Create a temporary directory with grouped log files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # Create main log files
            entries_main = [
                {"timestamp": "2026-01-15T09:00:00Z", "level": "INFO", "message": "Main start"},
                {"timestamp": "2026-01-15T10:00:00Z", "level": "ERROR", "message": "Main error"},
            ]
            with open(base / "app.jsonl", "w") as f:
                for entry in entries_main:
                    f.write(json.dumps(entry) + "\n")

            # Create rotated files
            rotation_dir = base / "rotation"
            rotation_dir.mkdir()

            entries_rot1 = [
                {"timestamp": "2026-01-14T08:00:00Z", "level": "DEBUG", "message": "Rot1"},
            ]
            with open(rotation_dir / "app.001.jsonl", "w") as f:
                for entry in entries_rot1:
                    f.write(json.dumps(entry) + "\n")

            entries_rot2 = [
                {"timestamp": "2026-01-14T12:00:00Z", "level": "WARNING", "message": "Rot2"},
            ]
            with open(rotation_dir / "app.002.jsonl", "w") as f:
                for entry in entries_rot2:
                    f.write(json.dumps(entry) + "\n")

            yield base

    def test_summarize_groups_by_root(self, temp_log_structure):
        """Test that logs are grouped by filename root."""
        summaries = summarize_logs(temp_log_structure, recursive=True)

        # Should have one group for "app"
        assert len(summaries) == 1
        assert summaries[0].name == "app"
        assert len(summaries[0].files) == 3  # app.jsonl, app.001.jsonl, app.002.jsonl

    def test_summarize_level_counts(self, temp_log_structure):
        """Test that level counts are aggregated correctly."""
        summaries = summarize_logs(temp_log_structure, recursive=True)

        level_counts = summaries[0].level_counts
        assert level_counts["INFO"] == 1
        assert level_counts["ERROR"] == 1
        assert level_counts["DEBUG"] == 1
        assert level_counts["WARNING"] == 1


class TestFormatOutput:
    """Tests for output formatting functions."""

    def test_format_text_empty(self):
        """Test formatting empty summaries."""
        result = format_summary_text([])
        assert "No log files found" in result

    def test_format_text_with_data(self):
        """Test formatting summaries as text."""
        summary = LogGroupSummary(
            name="test",
            files=["test.jsonl"],
            first_log=datetime(2026, 1, 1, 10, 0, 0),
            last_log=datetime(2026, 1, 1, 12, 0, 0),
            level_counts={"INFO": 50},
            total_lines=100,
        )
        result = format_summary_text([summary])
        assert "test" in result
        assert "100" in result
        assert "INFO" in result

    def test_format_json(self):
        """Test formatting summaries as JSON."""
        summary = LogGroupSummary(
            name="test",
            files=["test.jsonl"],
            first_log=datetime(2026, 1, 1, 10, 0, 0),
            last_log=datetime(2026, 1, 1, 12, 0, 0),
            level_counts={"INFO": 50},
            total_lines=100,
        )
        result = format_summary_json([summary])
        data = json.loads(result)
        assert data["total_groups"] == 1
        assert data["log_summaries"][0]["name"] == "test"


# ============================================================================
# Tests using local test data - these are skipped on GitHub Actions
# ============================================================================

# Check if running in GitHub Actions
IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"

LOCAL_DATA_PATH = Path(__file__).parent / "local-data" / "logs_docker"


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Skipped in GitHub Actions - uses local test data")
@pytest.mark.skipif(not LOCAL_DATA_PATH.exists(), reason="Local test data not available")
class TestWithLocalData:
    """Tests using local test data files.

    These tests are skipped on GitHub Actions as the test data is not
    committed to the repository.
    """

    def test_summarize_local_logs(self):
        """Test summarizing local log files."""
        summaries = summarize_logs(LOCAL_DATA_PATH, recursive=True)

        # Should have multiple log groups
        assert len(summaries) > 0

        # Check that we found expected log groups
        names = [s.name for s in summaries]
        assert "api_v2" in names
        assert "hive_monitor_v2" in names

    def test_local_logs_have_timestamps(self):
        """Test that local logs have valid timestamps extracted."""
        summaries = summarize_logs(LOCAL_DATA_PATH, recursive=True)

        for summary in summaries:
            # Each summary should have timestamps
            assert summary.first_log is not None, f"{summary.name} missing first_log"
            assert summary.last_log is not None, f"{summary.name} missing last_log"
            assert summary.first_log <= summary.last_log

    def test_local_logs_have_level_counts(self):
        """Test that local logs have level counts."""
        summaries = summarize_logs(LOCAL_DATA_PATH, recursive=True)

        for summary in summaries:
            # Each summary should have at least one level
            assert len(summary.level_counts) > 0, f"{summary.name} has no levels"
            assert summary.total_lines > 0, f"{summary.name} has no lines"

    def test_rotation_files_grouped(self):
        """Test that rotated log files are grouped correctly."""
        summaries = summarize_logs(LOCAL_DATA_PATH, recursive=True)

        # Find the hive_monitor_v2 group - should include rotation files
        hive_summary = next((s for s in summaries if s.name == "hive_monitor_v2"), None)
        assert hive_summary is not None

        # Should have multiple files (main + rotated)
        assert len(hive_summary.files) > 1, "Expected rotated files to be grouped"

    def test_text_output_format(self):
        """Test text output with local data."""
        summaries = summarize_logs(LOCAL_DATA_PATH, recursive=True)
        output = format_summary_text(summaries)

        assert "LOG FILE SUMMARY" in output
        assert "api_v2" in output
        assert "hive_monitor_v2" in output
        assert "First Log:" in output
        assert "Last Log:" in output
        assert "Level Range:" in output

    def test_json_output_format(self):
        """Test JSON output with local data."""
        summaries = summarize_logs(LOCAL_DATA_PATH, recursive=True)
        output = format_summary_json(summaries)

        data = json.loads(output)
        assert "log_summaries" in data
        assert "total_groups" in data
        assert "total_files" in data
        assert "total_lines" in data
        assert data["total_groups"] > 0
