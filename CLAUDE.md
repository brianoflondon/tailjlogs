# CLAUDE.md - Project Context for AI Assistants

## Project Overview

**TailJLogs** is a terminal application to view, tail, merge, and search log files with enhanced JSONL support. It's based on [Toolong](https://github.com/Textualize/toolong) by Will McGugan.

## Key Enhancements over Toolong

1. **JSONL Compact Format** - JSONL logs display in readable format: `01-15T09:36:38.194 INFO module 39 : message`
2. **Separate Filter Dialog** (`\` key) - Hide non-matching lines (vs Find which highlights)
3. **Updated for Textual 7.x** - Modern async terminal UI

## Architecture

### Source Structure: `src/tailjlogs/`

| File | Purpose |
|------|---------|
| `cli.py` | CLI entry point using Click |
| `ui.py` | Main Textual App class |
| `log_view.py` | Log view widget containing log lines and panels |
| `log_lines.py` | Core scrollable log line display widget |
| `log_file.py` | Log file abstraction (handles compressed files) |
| `format_parser.py` | **Key file** - Parses log formats including JSONL |
| `find_dialog.py` | Find and Filter dialogs |
| `line_panel.py` | Detail panel for selected line |
| `timestamps.py` | Timestamp parsing and detection |
| `highlighter.py` | Syntax highlighting |
| `watcher.py` | File watching abstraction |
| `messages.py` | Textual message types |
| `help.py` | Help screen |

### Key Classes

- `JSONLogFormat` in `format_parser.py` - Handles JSONL formatting (compact display)
- `LogLines` in `log_lines.py` - Main scrollable widget for log display
- `LinePanel` in `line_panel.py` - Shows full JSON when pressing Enter
- `FindDialog` in `find_dialog.py` - Find and Filter functionality

### Dependencies

- `click` - CLI framework
- `textual` - Terminal UI framework
- `rich` - Text formatting and colors (bundled with textual)
- `typing-extensions` - Type hints backports

## Entry Points

```toml
[project.scripts]
tailjlogs = "tailjlogs.cli:run"
tl = "tailjlogs.cli:run"
```

## Development Commands

```bash
# Install dependencies
uv sync

# Run the tool
uv run tailjlogs --help
uv run tl /path/to/logs.jsonl

# Run with dev tools (textual console)
uv run textual run --dev src/tailjlogs/ui.py

# Build package
uv build
```

## Testing

```bash
uv run pytest
```

## Code Style

- Python 3.9+
- Type hints throughout
- Async/await for Textual widgets
- Textual CSS for styling

## JSONL Format Expected

```json
{
  "timestamp": "2025-01-15T09:36:38.194Z",
  "level": "INFO",
  "message": "User logged in",
  "module": "auth",
  "line": 42
}
```

Displayed as: `01-15T09:36:38.194 INFO     auth                  42 : User logged in`
