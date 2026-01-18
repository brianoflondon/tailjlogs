from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Optional

import rich.repr
from rich.highlighter import JSONHighlighter
from rich.text import Text
from typing_extensions import TypeAlias

from tailjlogs import timestamps
from tailjlogs.highlighter import LogHighlighter

ParseResult: TypeAlias = "tuple[Optional[datetime], str, Text]"


@rich.repr.auto
class LogFormat:
    def parse(self, line: str) -> ParseResult | None:
        raise NotImplementedError()


HTTP_GROUPS = {
    "1": "cyan",
    "2": "green",
    "3": "yellow",
    "4": "red",
    "5": "reverse red",
}


class RegexLogFormat(LogFormat):
    REGEX = re.compile(".*?")
    HIGHLIGHT_WORDS = [
        "GET",
        "POST",
        "PUT",
        "HEAD",
        "POST",
        "DELETE",
        "OPTIONS",
        "PATCH",
    ]

    highlighter = LogHighlighter()

    def parse(self, line: str) -> ParseResult | None:
        match = self.REGEX.fullmatch(line)
        if match is None:
            return None
        groups = match.groupdict()
        _, timestamp = timestamps.parse(groups["date"].strip("[]"))

        text = Text.from_ansi(line)
        if not text.spans:
            text = self.highlighter(text)
        if status := groups.get("status", None):
            text.highlight_words([f" {status} "], HTTP_GROUPS.get(status[0], "magenta"))
        text.highlight_words(self.HIGHLIGHT_WORDS, "bold yellow")

        return timestamp, line, text


class CommonLogFormat(RegexLogFormat):
    REGEX = re.compile(
        r'(?P<ip>.*?) (?P<remote_log_name>.*?) (?P<userid>.*?) (?P<date>\[.*?(?= ).*?\]) "(?P<request_method>.*?) (?P<path>.*?)(?P<request_version> HTTP\/.*)?" (?P<status>.*?) (?P<length>.*?) "(?P<referrer>.*?)"'
    )


class CombinedLogFormat(RegexLogFormat):
    REGEX = re.compile(
        r'(?P<ip>.*?) (?P<remote_log_name>.*?) (?P<userid>.*?) \[(?P<date>.*?)(?= ) (?P<timezone>.*?)\] "(?P<request_method>.*?) (?P<path>.*?)(?P<request_version> HTTP\/.*)?" (?P<status>.*?) (?P<length>.*?) "(?P<referrer>.*?)" "(?P<user_agent>.*?)" (?P<session_id>.*?) (?P<generation_time_micro>.*?) (?P<virtual_host>.*)'
    )


class DefaultLogFormat(LogFormat):
    highlighter = LogHighlighter()

    def parse(self, line: str) -> ParseResult | None:
        text = Text.from_ansi(line)
        if not text.spans:
            text = self.highlighter(text)
        return None, line, text


class JSONLogFormat(LogFormat):
    highlighter = JSONHighlighter()

    # Common field names for each JSON log field type
    TIMESTAMP_FIELDS = ["timestamp", "time", "ts", "@timestamp", "datetime", "date"]
    LEVEL_FIELDS = ["level", "levelname", "severity", "log_level", "loglevel"]
    MODULE_FIELDS = ["module", "logger", "name", "logger_name", "source"]
    LINE_FIELDS = ["line", "lineno", "line_number", "lineNumber"]
    MESSAGE_FIELDS = ["message", "msg", "text", "log"]

    # Color mapping for log levels
    LEVEL_COLORS = {
        "debug": "dim cyan",
        "info": "green",
        "warning": "yellow",
        "warn": "yellow",
        "error": "red",
        "critical": "bold red",
        "fatal": "bold red",
    }

    def _get_field(self, data: dict, field_names: list[str]) -> str | None:
        """Try to get a field value from multiple possible field names."""
        for name in field_names:
            if name in data:
                value = data[name]
                return str(value) if value is not None else None
        return None

    def _format_timestamp(self, ts_str: str) -> str:
        """Format timestamp to compact form: MM-DDThh:mm:ss.mmm"""
        _, timestamp = timestamps.parse(ts_str)
        if timestamp:
            return timestamp.strftime("%m-%dT%H:%M:%S.") + f"{timestamp.microsecond // 1000:03d}"
        # Fallback: try to extract just the time portion if parsing failed
        return ts_str[:23] if len(ts_str) >= 23 else ts_str

    def _format_compact_line(self, data: dict) -> Text:
        """Format JSON log data as a compact single line."""
        ts_raw = self._get_field(data, self.TIMESTAMP_FIELDS)
        level = self._get_field(data, self.LEVEL_FIELDS) or ""
        module = self._get_field(data, self.MODULE_FIELDS) or ""
        lineno = self._get_field(data, self.LINE_FIELDS) or ""
        message = self._get_field(data, self.MESSAGE_FIELDS) or ""

        # Format timestamp
        ts_formatted = self._format_timestamp(ts_raw) if ts_raw else "                       "

        # Format level (uppercase, fixed width of 8)
        level_upper = level.upper()
        level_formatted = f"{level_upper:<8}"

        # Format module (fixed width of 20, truncate if needed)
        module_formatted = f"{module:<20}"[:20]

        # Format line number (right-aligned, 4 chars)
        lineno_formatted = f"{lineno:>4}" if lineno else "    "

        # Build the formatted line: "01-15T09:36:38.194 INFO     module                39 : message"
        text = Text()
        text.append(ts_formatted, style="cyan")
        text.append(" ")
        level_color = self.LEVEL_COLORS.get(level.lower(), "white")
        text.append(level_formatted, style=level_color)
        text.append(" ")
        text.append(module_formatted, style="blue")
        text.append(" ")
        text.append(lineno_formatted, style="dim")
        text.append(" : ")
        text.append(message)

        return text

    def parse(self, line: str) -> ParseResult | None:
        line = line.strip()
        if not line:
            return None
        try:
            data = json.loads(line)
        except Exception:
            return None

        # Get timestamp for timeline/filtering features
        _, timestamp = timestamps.parse(line)

        # Format as compact line for display
        text = self._format_compact_line(data)

        # Return: (datetime for filtering, raw line for detail panel, formatted text for display)
        return timestamp, line, text


FORMATS = [
    JSONLogFormat(),
    CommonLogFormat(),
    CombinedLogFormat(),
    # DefaultLogFormat(),
]

default_log_format = DefaultLogFormat()


class FormatParser:
    """Parses a log line."""

    def __init__(self) -> None:
        self._formats = FORMATS.copy()

    def parse(self, line: str) -> ParseResult:
        """Parse a line."""
        if len(line) > 10_000:
            line = line[:10_000]
        if line.strip():
            for index, format in enumerate(self._formats):
                parse_result = format.parse(line)
                if parse_result is not None:
                    if index:
                        self._formats = [*self._formats[index:], *self._formats[:index]]
                    return parse_result
        parse_result = default_log_format.parse(line)
        if parse_result is not None:
            return parse_result
        return None, "", Text()
