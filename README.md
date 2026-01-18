# TailJLogs

[![PyPI](https://img.shields.io/pypi/v/tailjlogs.svg)](https://pypi.org/project/tailjlogs/)
[![Tests](https://github.com/brianoflondon/tailjlogs/actions/workflows/tests.yml/badge.svg)](https://github.com/brianoflondon/tailjlogs/actions/workflows/tests.yml)

> **Based on [Textualize/toolong](https://github.com/Textualize/toolong) by Will McGugan**
> 
> A terminal application to view, tail, merge, and search log files with **enhanced JSONL support**.

![TailJLogs Screenshot](https://github.com/brianoflondon/tailjlogs/assets/screenshot.png)

## What's New in v2.0

TailJLogs v2.0 is a complete rewrite based on the excellent [Toolong](https://github.com/Textualize/toolong) project by Will McGugan. Key enhancements:

- **JSONL Compact Format**: JSONL logs display in a readable format: `01-15T09:36:38.194 INFO module 39 : message`
- **Separate Filter Dialog** (`\` key): Hide non-matching lines (vs Find which highlights matches)
- **Full TUI Experience**: Navigate with arrow keys, view detailed JSON with Enter
- **Updated for Textual 7.x**: Modern async terminal UI

## Features

- 📋 Live tailing of log files
- 🎨 Syntax highlights common web server log formats
- ⚡ Fast - opens multi-gigabyte files instantly
- 📝 **Enhanced JSONL support**: Compact formatted display + pretty-printed detail view
- 📦 Opens `.bz` and `.bz2` files automatically
- 🔀 Merges log files by auto-detecting timestamps
- 🔍 **Find** (`/` or `Ctrl+F`): Highlight matching lines
- 🔎 **Filter** (`\`): Show only matching lines

## Installation

```bash
# Using pip
pip install tailjlogs

# Using uv (recommended)
uv tool install tailjlogs

# Using pipx
pipx install tailjlogs
```

After installation, use either `tailjlogs` or `tl` command.

## Usage

```bash
# View a log file
tailjlogs /path/to/logfile.jsonl
tl /path/to/logfile.jsonl

# View multiple files (merged by timestamp)
tl access.log error.log app.jsonl

# View a directory of log files
tl /var/log/myapp/
```

## Keyboard Shortcuts

### Navigation
| Key | Action |
|-----|--------|
| `↑`/`↓` or `w`/`s` or `k`/`j` | Move up/down a line |
| `←`/`→` or `h`/`l` | Scroll left/right |
| `Page Up`/`Page Down` or `Space` | Next/previous page |
| `Home` or `G` | Jump to start |
| `End` or `g` | Jump to end (press twice to tail) |
| `m`/`M` | Advance +1/-1 minutes |
| `o`/`O` | Advance +1/-1 hours |
| `d`/`D` | Advance +1/-1 days |

### Features
| Key | Action |
|-----|--------|
| `/` or `Ctrl+F` | **Find** - highlight matching lines |
| `\` | **Filter** - show only matching lines |
| `Enter` | Toggle pointer mode / View JSON detail |
| `Ctrl+L` | Toggle line numbers |
| `Ctrl+T` | Tail current file |
| `?` | Show help |
| `Ctrl+C` or `q` | Exit |

## JSONL Format

TailJLogs displays JSONL log entries in a compact format:

```
01-15T09:36:38.194 INFO     auth                  42 : User logged in
01-15T09:36:39.521 WARNING  api                  156 : Rate limit approaching
01-15T09:36:40.003 ERROR    database             89 : Connection timeout
```

Press `Enter` on any line to see the full JSON object, pretty-printed.

Expected JSONL fields:
```json
{
  "timestamp": "2025-01-15T09:36:38.194Z",
  "level": "INFO",
  "message": "User logged in",
  "module": "auth",
  "line": 42
}
```

## Development

```bash
git clone https://github.com/brianoflondon/tailjlogs.git
cd tailjlogs
uv sync
uv run tailjlogs --help
```

## Credits

This project is based on [Toolong](https://github.com/Textualize/toolong) by [Will McGugan](https://www.willmcgugan.com/) and the [Textualize](https://www.textualize.io/) team. Built with [Textual](https://textual.textualize.io/).

## License

MIT License - see [LICENSE](LICENSE) for details.

Original Toolong: Copyright (c) 2024 Will McGugan  
This fork: Copyright (c) 2025 Brian of London
