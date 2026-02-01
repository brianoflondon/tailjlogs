"""Log file summary functionality.

Scans log files in a directory (and subdirectories) and provides summary statistics
grouped by filename root (before rotation suffixes like .001.jsonl).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator

from tailjlogs import timestamps

# Log level hierarchy (higher number = more severe)
LOG_LEVEL_ORDER = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "WARN": 30,
    "ERROR": 40,
    "CRITICAL": 50,
    "FATAL": 50,
}

# Common field names for log level and timestamp in JSON
LEVEL_FIELDS = ["level", "levelname", "severity", "log_level", "loglevel"]
TIMESTAMP_FIELDS = ["timestamp", "time", "ts", "@timestamp", "datetime", "date"]

# Pattern to match rotation suffixes like .001.jsonl, .002.log, etc.
ROTATION_PATTERN = re.compile(r"\.(\d{3,})(\.\w+)$")


@dataclass
class LogGroupSummary:
    """Summary statistics for a group of related log files."""

    name: str
    files: list[str] = field(default_factory=list)
    first_log: datetime | None = None
    last_log: datetime | None = None
    level_counts: dict[str, int] = field(default_factory=dict)
    total_lines: int = 0
    error_count: int = 0

    @property
    def timespan(self) -> timedelta | None:
        """Calculate the timespan between first and last log."""
        if self.first_log and self.last_log:
            return self.last_log - self.first_log
        return None

    @property
    def level_range(self) -> str:
        """Get the range of log levels (min to max severity)."""
        if not self.level_counts:
            return "N/A"

        levels_present = [
            level
            for level in self.level_counts
            if level.upper() in LOG_LEVEL_ORDER
        ]
        if not levels_present:
            return "N/A"

        # Sort by severity order
        sorted_levels = sorted(
            levels_present, key=lambda x: LOG_LEVEL_ORDER.get(x.upper(), 0)
        )
        min_level = sorted_levels[0]
        max_level = sorted_levels[-1]

        if min_level == max_level:
            return min_level.upper()
        return f"{min_level.upper()} to {max_level.upper()}"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "files": self.files,
            "first_log": self.first_log.isoformat() if self.first_log else None,
            "last_log": self.last_log.isoformat() if self.last_log else None,
            "timespan_seconds": self.timespan.total_seconds() if self.timespan else None,
            "timespan_human": format_timedelta(self.timespan) if self.timespan else None,
            "level_range": self.level_range,
            "level_counts": self.level_counts,
            "total_lines": self.total_lines,
        }


def format_timedelta(td: timedelta | None) -> str:
    """Format a timedelta as a human-readable string."""
    if td is None:
        return "N/A"

    total_seconds = int(td.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")

    return " ".join(parts)


def get_filename_root(filepath: Path) -> str:
    """Extract the root filename before any rotation suffix.

    Examples:
        api_v2.jsonl -> api_v2
        hive_monitor_v2.001.jsonl -> hive_monitor_v2
        hive_monitor_v2.002.jsonl -> hive_monitor_v2
    """
    name = filepath.name

    # Check for rotation pattern like .001.jsonl
    match = ROTATION_PATTERN.search(name)
    if match:
        # Remove the rotation suffix
        root = name[: match.start()]
        return root

    # Remove the extension
    stem = filepath.stem
    # Handle double extensions like .jsonl.gz
    if stem.endswith((".json", ".jsonl", ".log")):
        stem = Path(stem).stem
    return stem


def find_log_files(path: Path, recursive: bool = True) -> Iterator[Path]:
    """Find all log files in the given path.

    Args:
        path: Directory path to search
        recursive: Whether to search subdirectories

    Yields:
        Path objects for each log file found
    """
    LOG_EXTENSIONS = (".jsonl", ".json", ".log", ".txt")

    if path.is_file():
        if path.suffix.lower() in LOG_EXTENSIONS:
            yield path
        return

    if not path.is_dir():
        return

    pattern = "**/*" if recursive else "*"
    for ext in LOG_EXTENSIONS:
        for file_path in path.glob(f"{pattern}{ext}"):
            if file_path.is_file():
                yield file_path


def _get_field(data: dict, field_names: list[str]) -> str | None:
    """Try to get a field value from multiple possible field names."""
    for name in field_names:
        if name in data:
            value = data[name]
            return str(value) if value is not None else None
    return None


def _parse_json_line(line: str) -> tuple[datetime | None, str | None]:
    """Parse a JSON log line and extract timestamp and level.

    Returns:
        Tuple of (timestamp, level) - either can be None if not found
    """
    line = line.strip()
    if not line:
        return None, None

    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None, None

    # Extract level
    level = _get_field(data, LEVEL_FIELDS)

    # Extract timestamp
    ts_str = _get_field(data, TIMESTAMP_FIELDS)
    timestamp = None
    if ts_str:
        scanner = timestamps.TimestampScanner()
        timestamp = scanner.scan(ts_str)

    return timestamp, level


def scan_log_file(filepath: Path) -> tuple[datetime | None, datetime | None, dict[str, int], int]:
    """Scan a log file and extract summary statistics.

    Returns:
        Tuple of (first_timestamp, last_timestamp, level_counts, line_count)
    """
    first_ts: datetime | None = None
    last_ts: datetime | None = None
    level_counts: dict[str, int] = {}
    line_count = 0

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line_count += 1
                timestamp, level = _parse_json_line(line)

                if timestamp:
                    if first_ts is None or timestamp < first_ts:
                        first_ts = timestamp
                    if last_ts is None or timestamp > last_ts:
                        last_ts = timestamp

                if level:
                    level_upper = level.upper()
                    level_counts[level_upper] = level_counts.get(level_upper, 0) + 1

    except (OSError, IOError):
        # File couldn't be read
        pass

    return first_ts, last_ts, level_counts, line_count


def summarize_logs(path: Path, recursive: bool = True) -> list[LogGroupSummary]:
    """Scan all log files in a path and return grouped summaries.

    Args:
        path: Directory path to scan
        recursive: Whether to search subdirectories

    Returns:
        List of LogGroupSummary objects, sorted by name
    """
    # Group files by their root name
    groups: dict[str, list[Path]] = {}

    for file_path in find_log_files(path, recursive):
        root = get_filename_root(file_path)
        if root not in groups:
            groups[root] = []
        groups[root].append(file_path)

    # Build summaries for each group
    summaries: list[LogGroupSummary] = []

    for name, files in sorted(groups.items()):
        summary = LogGroupSummary(name=name)

        for file_path in sorted(files):
            summary.files.append(str(file_path))
            first_ts, last_ts, level_counts, line_count = scan_log_file(file_path)

            # Update timestamps
            if first_ts:
                if summary.first_log is None or first_ts < summary.first_log:
                    summary.first_log = first_ts
            if last_ts:
                if summary.last_log is None or last_ts > summary.last_log:
                    summary.last_log = last_ts

            # Merge level counts
            for level, count in level_counts.items():
                summary.level_counts[level] = summary.level_counts.get(level, 0) + count

            summary.total_lines += line_count

        summaries.append(summary)

    return summaries


def format_summary_text(summaries: list[LogGroupSummary]) -> str:
    """Format summaries as human-readable text output.

    Args:
        summaries: List of LogGroupSummary objects

    Returns:
        Formatted text string
    """
    if not summaries:
        return "No log files found."

    lines: list[str] = []
    lines.append("=" * 80)
    lines.append("LOG FILE SUMMARY")
    lines.append("=" * 80)
    lines.append("")

    for summary in summaries:
        lines.append(f"📁 {summary.name}")
        lines.append("-" * 60)
        lines.append(f"   Files: {len(summary.files)}")
        for f in summary.files:
            lines.append(f"          - {f}")
        lines.append(f"   Total Lines: {summary.total_lines:,}")
        lines.append("")
        lines.append(f"   First Log: {summary.first_log.strftime('%Y-%m-%d %H:%M:%S') if summary.first_log else 'N/A'}")
        lines.append(f"   Last Log:  {summary.last_log.strftime('%Y-%m-%d %H:%M:%S') if summary.last_log else 'N/A'}")
        lines.append(f"   Timespan:  {format_timedelta(summary.timespan)}")
        lines.append("")
        lines.append(f"   Level Range: {summary.level_range}")
        lines.append("   Level Counts:")

        # Sort levels by severity for display
        sorted_levels = sorted(
            summary.level_counts.items(),
            key=lambda x: LOG_LEVEL_ORDER.get(x[0], 100),
        )
        for level, count in sorted_levels:
            lines.append(f"      {level:<10} : {count:>8,}")

        lines.append("")
        lines.append("")

    return "\n".join(lines)


def format_summary_json(summaries: list[LogGroupSummary]) -> str:
    """Format summaries as JSON output.

    Args:
        summaries: List of LogGroupSummary objects

    Returns:
        JSON string
    """
    data = {
        "log_summaries": [s.to_dict() for s in summaries],
        "total_groups": len(summaries),
        "total_files": sum(len(s.files) for s in summaries),
        "total_lines": sum(s.total_lines for s in summaries),
    }
    return json.dumps(data, indent=2, default=str)
