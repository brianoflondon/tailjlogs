from __future__ import annotations

import os
import sys
from glob import glob
from importlib.metadata import version
from pathlib import Path

import click

from tailjlogs.ui import UI


def expand_file_patterns(patterns: tuple[str, ...]) -> list[str]:
    """Expand glob patterns and resolve paths.

    Handles wildcards like *.jsonl, **/*.log, etc.
    Also expands directories to include log files within them.
    """
    LOG_EXTENSIONS = (".jsonl", ".json", ".log", ".txt", ".gz", ".bz2")

    expanded: list[str] = []
    seen: set[str] = set()

    for pattern in patterns:
        path = Path(pattern)

        # Check if it's a glob pattern
        if any(c in pattern for c in "*?["):
            # Expand the glob pattern
            matches = sorted(glob(pattern, recursive=True))
            for match in matches:
                match_path = Path(match)
                if match_path.is_file():
                    abs_path = str(match_path.resolve())
                    if abs_path not in seen:
                        seen.add(abs_path)
                        expanded.append(abs_path)
        elif path.is_dir():
            # If it's a directory, find all log files in it
            for ext in LOG_EXTENSIONS:
                for file_path in sorted(path.glob(f"*{ext}")):
                    if file_path.is_file():
                        abs_path = str(file_path.resolve())
                        if abs_path not in seen:
                            seen.add(abs_path)
                            expanded.append(abs_path)
        elif path.is_file():
            # Regular file
            abs_path = str(path.resolve())
            if abs_path not in seen:
                seen.add(abs_path)
                expanded.append(abs_path)
        elif path.exists():
            # Some other type of path
            abs_path = str(path.resolve())
            if abs_path not in seen:
                seen.add(abs_path)
                expanded.append(abs_path)
        else:
            # Path doesn't exist - might be a glob that matched nothing
            # or a typo. Let it through so the UI can show an error.
            if pattern not in seen:
                seen.add(pattern)
                expanded.append(pattern)

    return expanded


@click.command()
@click.version_option(version("tailjlogs"))
@click.argument("files", metavar="FILE1 FILE2", nargs=-1)
@click.option("-m", "--merge", is_flag=True, help="Merge files.")
@click.option(
    "-o",
    "--output-merge",
    metavar="PATH",
    nargs=1,
    help="Path to save merged file (requires -m).",
)
def run(files: tuple[str, ...], merge: bool, output_merge: str) -> None:
    """View / tail / search log files.

    Supports glob patterns like *.jsonl, logs/*.log, **/*.jsonl

    Examples:
        tl app.jsonl                    # Single file
        tl *.jsonl                      # All .jsonl files in current dir
        tl logs/                        # All log files in logs/ directory
        tl "logs/**/*.jsonl"            # Recursive glob (quote to prevent shell expansion)
        tl app.log error.log --merge    # Merge multiple files
    """
    stdin_tty = sys.__stdin__.isatty()

    # Expand glob patterns and directories
    expanded_files = expand_file_patterns(files) if files else []

    if not expanded_files and stdin_tty:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()
    if stdin_tty:
        try:
            ui = UI(expanded_files, merge=merge, save_merge=output_merge)
            ui.run()
        except Exception:
            pass
    else:
        import selectors
        import signal
        import subprocess
        import tempfile

        def request_exit(*args) -> None:
            """Don't write anything when a signal forces an error."""
            sys.stderr.write("^C")

        signal.signal(signal.SIGINT, request_exit)
        signal.signal(signal.SIGTERM, request_exit)

        # Write piped data to a temporary file
        with tempfile.NamedTemporaryFile(mode="w+b", buffering=0, prefix="tl_") as temp_file:
            # Get input directly from /dev/tty to free up stdin
            with open("/dev/tty", "rb", buffering=0) as tty_stdin:
                # Launch a new process to render the UI
                with subprocess.Popen(
                    [sys.argv[0], temp_file.name],
                    stdin=tty_stdin,
                    close_fds=True,
                    env={**os.environ, "TEXTUAL_ALLOW_SIGNALS": "1"},
                ) as process:
                    # Current process copies from stdin to the temp file
                    selector = selectors.SelectSelector()
                    selector.register(sys.stdin.fileno(), selectors.EVENT_READ)

                    while process.poll() is None:
                        for _, event in selector.select(0.1):
                            if process.poll() is not None:
                                break
                            if event & selectors.EVENT_READ:
                                if line := os.read(sys.stdin.fileno(), 1024 * 64):
                                    temp_file.write(line)
                                else:
                                    break
