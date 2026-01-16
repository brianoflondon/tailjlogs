# CLAUDE.md - Project Context for AI Assistants

## Project Overview

**TailJLogs** is a Python command-line tool for tailing and following JSONL (JSON Lines) log files with pretty formatting. It's similar to `tail -f` but designed specifically for structured JSON log output.

## Architecture

### Main File: `tailjlogs.py`

The entire application is in a single file with these key components:

1. **CLI Setup** - Uses Typer for command-line argument parsing
2. **Log Formatting** - `format_log_entry()` and `process_line()` handle JSON parsing and colorized output
3. **File Reading** - `read_last_n_lines()` efficiently reads from file end
4. **File Following** - Uses `watchdog` library to monitor file changes in real-time
5. **Multi-file Support** - Can merge logs from multiple files by timestamp

### Key Classes

- `LogLevel` - Enum for log level filtering (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LogFileHandler` - Watchdog event handler for single file monitoring
- `MultiFileHandler` - Watchdog event handler for multiple file monitoring

### Dependencies

- `typer` - CLI framework
- `aiofiles` - Async file I/O
- `watchdog` - File system monitoring
- `single-source` - Version from pyproject.toml

## Version Management

The version is single-sourced from `pyproject.toml` using the `single-source` library:

```python
from single_source import get_version
__version__ = get_version(__name__, Path(__file__).parent)
```

## Entry Point

The CLI entry point is defined in `pyproject.toml`:

```toml
[project.scripts]
tailjlogs = "tailjlogs:app"
```

## Development Commands

```bash
# Install dependencies
uv sync

# Run the tool
uv run tailjlogs --help

# Run with a log file
uv run tailjlogs /path/to/logs.jsonl -f

# Build package
uv build
```

## Testing

Currently no test suite. When adding tests, create a `tests/` directory with pytest.

## Code Style

- Python 3.13+
- Type hints using `Annotated` for Typer options
- Async/await for file operations
- ANSI color codes for terminal output
