from __future__ import annotations

import mimetypes
import mmap
import os
import platform
import time
from datetime import datetime
from pathlib import Path
from threading import Event, Lock
from typing import IO, Callable, Iterable

import rich.repr

from tailjlogs.format_parser import FormatParser, ParseResult
from tailjlogs.timestamps import TimestampScanner

IS_WINDOWS = platform.system() == "Windows"


class LogError(Exception):
    """An error related to logs."""


@rich.repr.auto(angular=True)
class LogFile:
    """A single log file."""

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.name = self.path.name
        self.file: IO[bytes] | None = None
        self.size = 0
        self.can_tail = False
        self.timestamp_scanner = TimestampScanner()
        self.format_parser = FormatParser()
        self._lock = Lock()

    def __rich_repr__(self) -> rich.repr.Result:
        yield self.name
        yield "size", self.size

    @property
    def is_open(self) -> bool:
        return self.file is not None

    @property
    def fileno(self) -> int:
        assert self.file is not None
        return self.file.fileno()

    @property
    def is_compressed(self) -> bool:
        _, encoding = mimetypes.guess_type(self.path.name, strict=False)
        return encoding in ("gzip", "bzip2")

    def parse(self, line: str) -> ParseResult:
        """Parse a line."""
        return self.format_parser.parse(line)

    def get_create_time(self) -> datetime | None:
        try:
            stat_result = self.path.stat()
        except Exception:
            return None
        try:
            # This works on Mac
            create_time_seconds = stat_result.st_birthtime
        except AttributeError:
            # No birthtime for Linux, so we assume the epoch start
            return datetime.fromtimestamp(0)
        timestamp = datetime.fromtimestamp(create_time_seconds)
        return timestamp

    def open(self, exit_event: Event) -> bool:
        # Check for compressed files
        _, encoding = mimetypes.guess_type(self.path.name, strict=False)

        # Open compressed files
        if encoding in ("gzip", "bzip2"):
            return self.open_compressed(exit_event, encoding)

        # Open uncompressed file
        self.file = open(self.path, "rb", buffering=0)

        self.file.seek(0, os.SEEK_END)
        self.size = self.file.tell()
        self.can_tail = True
        return True

    def open_compressed(self, exit_event: Event, encoding: str) -> bool:
        from tempfile import TemporaryFile

        chunk_size = 1024 * 256

        temp_file = TemporaryFile("wb+")

        compressed_file: IO[bytes]
        if encoding == "gzip":
            import gzip

            compressed_file = gzip.open(self.path, "rb")
        elif encoding == "bzip2":
            import bz2

            compressed_file = bz2.open(self.path, "rb")
        else:
            # Shouldn't get here
            raise AssertionError("Not supported")

        try:
            while data := compressed_file.read(chunk_size):
                temp_file.write(data)
                if exit_event.is_set():
                    temp_file.close()
                    return False
        finally:
            compressed_file.close()

        temp_file.flush()
        self.file = temp_file
        self.size = temp_file.tell()
        self.can_tail = False
        return True

    def close(self) -> None:
        if self.file is not None:
            self.file.close()
            self.file = None

    if IS_WINDOWS:

        def get_raw(self, start: int, end: int) -> bytes:
            with self._lock:
                if start >= end or self.file is None:
                    return b""
                position = os.lseek(self.fileno, 0, os.SEEK_CUR)
                try:
                    os.lseek(self.fileno, start, os.SEEK_SET)
                    return os.read(self.fileno, end - start)
                finally:
                    os.lseek(self.fileno, position, os.SEEK_SET)

    else:

        def get_raw(self, start: int, end: int) -> bytes:
            if start >= end or self.file is None:
                return b""
            return os.pread(self.fileno, end - start, start)

    def get_line(self, start: int, end: int) -> str:
        return (
            self.get_raw(start, end).decode("utf-8", errors="replace").strip("\n\r").expandtabs(4)
        )

    def scan_line_breaks(self, batch_time: float = 0.25) -> Iterable[tuple[int, list[int]]]:
        """Scan the file for line breaks.

        Args:
            batch_time: Time to group the batches.

        Returns:
            An iterable of tuples, containing the scan position and a list of offsets of new lines.
        """
        fileno = self.fileno
        size = self.size
        if not size:
            return
        if IS_WINDOWS:
            log_mmap = mmap.mmap(fileno, size, access=mmap.ACCESS_READ)
        else:
            log_mmap = mmap.mmap(fileno, size, prot=mmap.PROT_READ)
        try:
            rfind = log_mmap.rfind
            position = size
            batch: list[int] = []
            append = batch.append
            get_length = batch.__len__
            monotonic = time.monotonic
            break_time = monotonic()

            if log_mmap[-1] != "\n":
                batch.append(position)

            while (position := rfind(b"\n", 0, position)) != -1:
                append(position)
                if get_length() % 1000 == 0 and monotonic() - break_time > batch_time:
                    break_time = monotonic()
                    yield (position, batch)
                    batch = []
                    append = batch.append
            yield (0, batch)
        finally:
            log_mmap.close()

    def scan_timestamps(
        self,
        batch_time: float = 0.25,
        max_lines: int | None = None,
        level_filter: Callable[[str], bool] | None = None,
    ) -> Iterable[list[tuple[int, int, float]]]:
        """Scan file for timestamps.

        Args:
            batch_time: Time between yielding batches.
            max_lines: If set, only scan the last N lines (for performance with large files).
            level_filter: Optional callable that takes a line and returns True if it should be included.
        """
        size = self.size
        if not size:
            return
        fileno = self.fileno
        if IS_WINDOWS:
            log_mmap = mmap.mmap(fileno, size, access=mmap.ACCESS_READ)
        else:
            log_mmap = mmap.mmap(fileno, size, prot=mmap.PROT_READ)

        try:
            # If max_lines is set, find the starting position for the last N lines
            start_position = 0
            if max_lines is not None and max_lines > 0:
                start_position = self._find_tail_start(log_mmap, size, max_lines)

            monotonic = time.monotonic
            scan_time = monotonic()
            scan = self.timestamp_scanner.scan
            line_no = 0
            position = start_position

            # Seek to start position
            log_mmap.seek(start_position)

            results: list[tuple[int, int, float]] = []
            append = results.append
            get_length = results.__len__
            while line_bytes := log_mmap.readline():
                line = line_bytes.decode("utf-8", errors="replace")
                position += len(line_bytes)

                # Apply level filter if provided
                if level_filter is not None and not level_filter(line):
                    continue

                timestamp = scan(line)
                append((line_no, position, timestamp.timestamp() if timestamp else 0.0))
                line_no += 1
                if results and get_length() % 1000 == 0 and monotonic() - scan_time > batch_time:
                    scan_time = monotonic()
                    yield results
                    results = []
                    append = results.append
            if results:
                yield results
        finally:
            log_mmap.close()

    def _find_tail_start(self, log_mmap: mmap.mmap, size: int, max_lines: int) -> int:
        """Find the byte position to start reading to get approximately the last N lines.

        Args:
            log_mmap: Memory-mapped file.
            size: Total file size.
            max_lines: Number of lines to include.

        Returns:
            Byte offset to start reading from.
        """
        # Estimate average line length (assume ~200 bytes for JSONL, add buffer)
        estimated_bytes_per_line = 300
        estimated_start = max(0, size - (max_lines * estimated_bytes_per_line))

        # Search backwards from estimated position to find actual line breaks
        # We want to find max_lines newlines from the end
        rfind = log_mmap.rfind
        position = size
        lines_found = 0

        while lines_found < max_lines and position > 0:
            new_pos = rfind(b"\n", 0, position)
            if new_pos == -1:
                # No more newlines, start from beginning
                return 0
            position = new_pos
            lines_found += 1

        # Position is at a newline, so start reading from the next character
        return position + 1 if position > 0 else 0
