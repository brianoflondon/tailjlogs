"""Tests for the CLI module."""

import pytest
from click.testing import CliRunner

from tailjlogs.cli import run


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
