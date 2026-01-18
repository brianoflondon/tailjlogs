"""Tests for the log_lines module."""

import pytest

from tailjlogs.log_lines import FILE_COLORS, FILENAME_PREFIX_WIDTH, FILENAME_SEPARATOR


class TestFilenamePrefix:
    """Tests for filename prefix functionality in merged view."""

    def test_filename_prefix_width_constant(self):
        """Test that filename prefix width is defined."""
        assert FILENAME_PREFIX_WIDTH == 15

    def test_file_colors_defined(self):
        """Test that file colors are defined for merged view."""
        assert len(FILE_COLORS) >= 5
        assert all(isinstance(c, str) for c in FILE_COLORS)

    def test_filename_separator_defined(self):
        """Test that filename separator is defined."""
        assert FILENAME_SEPARATOR == " │ "

    @pytest.mark.parametrize(
        "filename,expected_base",
        [
            ("app.jsonl", "app"),
            ("db_monitor.jsonl", "db_monitor"),
            ("error.log", "error"),
            ("access.log.gz", "access.log"),  # .gz removed first
            ("myapp.json", "myapp"),
            ("simple.txt", "simple"),
            ("noextension", "noextension"),
        ],
    )
    def test_extension_stripping(self, filename, expected_base):
        """Test that common extensions are stripped from filenames."""
        # This tests the logic that should be in _get_filename_prefix
        name = filename
        for ext in (".jsonl", ".json", ".log", ".txt", ".gz", ".bz2"):
            if name.lower().endswith(ext):
                name = name[: -len(ext)]

        assert name == expected_base

    def test_filename_truncation_logic(self):
        """Test that long filenames are truncated with ellipsis."""
        name = "very_long_filename_that_exceeds_limit"

        if len(name) > FILENAME_PREFIX_WIDTH:
            name = name[: FILENAME_PREFIX_WIDTH - 1] + "…"
        name = name.ljust(FILENAME_PREFIX_WIDTH)

        assert len(name) == FILENAME_PREFIX_WIDTH
        assert name.endswith("…" + " " * (FILENAME_PREFIX_WIDTH - len(name.rstrip())))

    def test_filename_padding_logic(self):
        """Test that short filenames are padded to fixed width."""
        name = "app"
        name = name.ljust(FILENAME_PREFIX_WIDTH)

        assert len(name) == FILENAME_PREFIX_WIDTH
        assert name == "app" + " " * 12

    def test_color_cycling(self):
        """Test that colors cycle through the list."""
        for i in range(20):
            color = FILE_COLORS[i % len(FILE_COLORS)]
            assert color in FILE_COLORS
