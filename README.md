# TailJLogs

A command line tool to tail and follow JSONL log files with pretty formatting.

## Features

- 📋 Display JSONL logs in a clean, readable format similar to `docker logs`
- 🔄 Follow mode (`-f`) for real-time log monitoring
- 🎨 Colorized output by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- 🔍 Filter by log level (`-l WARNING`)
- 🔎 Grep pattern matching (`-g "error|failed"`)
- 🚫 Exclude patterns (`-G "healthcheck"`)
- 📁 Directory support - merge multiple log files by timestamp
- ⚡ Async file reading for performance

## Installation

### Standalone Installation (Recommended)

Install TailJLogs as a standalone CLI tool available system-wide:

```bash
# Using uv (fastest)
uv tool install git+https://github.com/brianoflondon/tailjlogs.git

# Using pipx (alternative)
pipx install git+https://github.com/brianoflondon/tailjlogs.git
```

After installation, `tailjlogs` will be available in your PATH.

### From PyPI (when published)

```bash
uv tool install tailjlogs
# or
pipx install tailjlogs
```

### From Source (for development)

```bash
git clone https://github.com/brianoflondon/tailjlogs.git
cd tailjlogs
uv sync

# Run directly
uv run tailjlogs --help

# Or install in editable mode
uv pip install -e .
```

### Updating

```bash
# Using uv
uv tool upgrade tailjlogs

# Using pipx
pipx upgrade tailjlogs
```

### Uninstalling

```bash
# Using uv
uv tool uninstall tailjlogs

# Using pipx
pipx uninstall tailjlogs
```

## Usage

```bash
# Show last 50 lines and follow
tailjlogs logs/app.jsonl -f

# Show last 100 lines with WARNING or higher
tailjlogs logs/app.jsonl -n 100 -l WARNING

# Filter by regex pattern and follow
tailjlogs logs/app.jsonl -f -g "error|failed"

# Exclude health check logs
tailjlogs logs/app.jsonl -f -G "healthcheck"

# Tail a directory (merges all .jsonl files by timestamp)
tailjlogs logs/ -n 100 -f

# Show version
tailjlogs --version
```

## Options

| Option           | Short | Description                                                          |
| ---------------- | ----- | -------------------------------------------------------------------- |
| `--follow`       | `-f`  | Follow the log file for new entries (like tail -f)                   |
| `--tail`         | `-n`  | Number of lines to show from the end (default: 50)                   |
| `--level`        | `-l`  | Minimum log level to display (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `--grep`         | `-g`  | Filter messages by regex pattern (include matches)                   |
| `--grep-exclude` | `-G`  | Exclude messages matching regex pattern                              |
| `--no-color`     |       | Disable colored output                                               |
| `--verbose`      | `-v`  | Use verbose output format                                            |
| `--extras`       | `-e`  | Show extra fields in log entries                                     |
| `--version`      | `-V`  | Show version and exit                                                |

## Expected JSONL Format

TailJLogs expects log entries in JSONL format with the following fields:

```json
{
  "timestamp": "2025-01-16T10:30:45.123456Z",
  "level": "INFO",
  "message": "User logged in",
  "module": "auth",
  "line": 42,
  "logger": "app.auth",
  "function": "login"
}
```

## License

MIT
