"""Tests for the CLI module."""

import os
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from tailjlogs.cli import expand_file_patterns, run


class TestExpandFilePatterns:
    """Tests for the expand_file_patterns function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "app.jsonl").write_text('{"msg": "test"}')
            (Path(tmpdir) / "error.jsonl").write_text('{"msg": "error"}')
            (Path(tmpdir) / "access.log").write_text("GET /")
            (Path(tmpdir) / "data.txt").write_text("data")
            (Path(tmpdir) / "readme.md").write_text("# Readme")
            
            # Create subdirectory with files
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            (subdir / "nested.jsonl").write_text('{"msg": "nested"}')
            
            yield tmpdir

    def test_expand_single_file(self, temp_dir):
        """Test expanding a single file path."""
        file_path = os.path.join(temp_dir, "app.jsonl")
        result = expand_file_patterns((file_path,))
        
        assert len(result) == 1
        assert result[0].endswith("app.jsonl")

    def test_expand_glob_pattern(self, temp_dir):
        """Test expanding a glob pattern."""
        pattern = os.path.join(temp_dir, "*.jsonl")
        result = expand_file_patterns((pattern,))
        
        assert len(result) == 2
        filenames = [os.path.basename(f) for f in result]
        assert "app.jsonl" in filenames
        assert "error.jsonl" in filenames

    def test_expand_directory(self, temp_dir):
        """Test expanding a directory to find log files."""
        result = expand_file_patterns((temp_dir,))
        
        # Should find .jsonl, .log, and .txt files (not .md)
        filenames = [os.path.basename(f) for f in result]
        assert "app.jsonl" in filenames
        assert "error.jsonl" in filenames
        assert "access.log" in filenames
        assert "data.txt" in filenames
        assert "readme.md" not in filenames

    def test_expand_multiple_patterns(self, temp_dir):
        """Test expanding multiple patterns."""
        pattern1 = os.path.join(temp_dir, "*.jsonl")
        pattern2 = os.path.join(temp_dir, "*.log")
        result = expand_file_patterns((pattern1, pattern2))
        
        filenames = [os.path.basename(f) for f in result]
        assert "app.jsonl" in filenames
        assert "error.jsonl" in filenames
        assert "access.log" in filenames

    def test_expand_recursive_glob(self, temp_dir):
        """Test expanding a recursive glob pattern."""
        pattern = os.path.join(temp_dir, "**", "*.jsonl")
        result = expand_file_patterns((pattern,))
        
        filenames = [os.path.basename(f) for f in result]
        assert "app.jsonl" in filenames
        assert "error.jsonl" in filenames
        assert "nested.jsonl" in filenames

    def test_expand_deduplicates(self, temp_dir):
        """Test that duplicate paths are removed."""
        file_path = os.path.join(temp_dir, "app.jsonl")
        pattern = os.path.join(temp_dir, "*.jsonl")
        result = expand_file_patterns((file_path, pattern))
        
        # app.jsonl should only appear once
        app_count = sum(1 for f in result if f.endswith("app.jsonl"))
        assert app_count == 1

    def test_expand_nonexistent_passes_through(self):
        """Test that non-existent paths pass through for error handling."""
        result = expand_file_patterns(("/nonexistent/file.log",))
        
        assert len(result) == 1
        assert result[0] == "/nonexistent/file.log"

    def test_expand_empty_input(self):
        """Test expanding empty input."""
        result = expand_file_patterns(())
        
        assert result == []


class TestCLI:
    """Tests for CLI commands."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_version_flag(self, runner):
        """Test --version flag shows version."""
        result = runner.invoke(run, ["--version"])

        assert result.exit_code == 0
        assert "version" in result.output.lower()

    def test_help_flag(self, runner):
        """Test --help flag shows help."""
        result = runner.invoke(run, ["--help"])

        assert result.exit_code == 0
        assert "View / tail / search log files" in result.output

    def test_merge_flag_accepted(self, runner):
        """Test -m/--merge flag is recognized."""
        result = runner.invoke(run, ["--help"])

        # Verify merge option is documented
        assert "--merge" in result.output or "-m" in result.output

    def test_output_merge_flag_accepted(self, runner):
        """Test -o/--output-merge flag is recognized."""
        result = runner.invoke(run, ["--help"])

        # Verify output-merge option is documented
        assert "--output-merge" in result.output or "-o" in result.output
