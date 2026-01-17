import os
import time
from pathlib import Path

import pytest

from tailjlogs import get_jsonl_files, read_and_merge_files


def touch(path: Path, mtime: float):
    path.write_text(path.read_text() if path.exists() else "")
    os.utime(path, (mtime, mtime))


def test_get_jsonl_files_with_rotations(tmp_path: Path):
    """Ensure rotated files like .jsonl.1 are discovered and non-numeric suffixes ignored."""
    a = tmp_path / "app.jsonl"
    b = tmp_path / "app.jsonl.1"
    c = tmp_path / "app.jsonl.2"
    d = tmp_path / "app.jsonl.bak"

    # Create files with specific mtimes so sorting is predictable
    now = time.time()
    a.write_text("{}\n")
    touch(a, now - 30)
    b.write_text("{}\n")
    touch(b, now - 60)
    c.write_text("{}\n")
    touch(c, now - 90)
    d.write_text("{}\n")
    touch(d, now - 15)

    result = get_jsonl_files(str(tmp_path))

    # Should include .jsonl, .jsonl.1 and .jsonl.2, but not .jsonl.bak
    names = [Path(p).name for p in result]
    assert "app.jsonl" in names
    assert "app.jsonl.1" in names
    assert "app.jsonl.2" in names
    assert "app.jsonl.bak" not in names

    # Sorted by mtime (oldest first): c (.2), b (.1), a (base)
    assert names == ["app.jsonl.2", "app.jsonl.1", "app.jsonl"]


@pytest.mark.asyncio
async def test_read_and_merge_includes_rotated(tmp_path: Path):
    """Read and merge entries from rotated and base files by timestamp."""
    base = tmp_path / "svc.jsonl"
    rot = tmp_path / "svc.jsonl.1"

    # Older entry in rotated file
    rot.write_text('{"timestamp": "2026-01-15T10:00:00+00:00", "message": "rotated"}\n')
    # Newer entry in current file
    base.write_text('{"timestamp": "2026-01-15T11:00:00+00:00", "message": "current"}\n')

    merged = await read_and_merge_files([str(rot), str(base)], n_lines=10)
    # merged is list of tuples (short_name, line, timestamp)
    messages = [m for (_, m, _) in merged]

    assert any("rotated" in line for line in messages)
    assert any("current" in line for line in messages)
    # Ensure ordering by timestamp: rotated then current
    assert messages[0].strip().endswith('"rotated"}')
    assert messages[-1].strip().endswith('"current"}')
