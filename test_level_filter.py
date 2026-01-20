#!/usr/bin/env python3
import json

LOG_LEVEL_ORDER = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "WARN": 30,
    "ERROR": 40,
    "CRITICAL": 50,
    "FATAL": 50,
}
LEVEL_FIELDS = ["level", "levelname", "severity", "log_level", "loglevel"]


def check_level_match(line: str, min_level_value: int) -> bool:
    if not min_level_value:
        return True
    if not line:
        return True

    try:
        data = json.loads(line.strip())
        if not isinstance(data, dict):
            return True

        level_str = None
        for field in LEVEL_FIELDS:
            if field in data:
                level_str = str(data[field]).upper()
                break

        if not level_str:
            return True

        line_level_value = LOG_LEVEL_ORDER.get(level_str, 0)
        return line_level_value >= min_level_value
    except (json.JSONDecodeError, ValueError):
        return True


# Test
min_level = "INFO"
min_level_value = LOG_LEVEL_ORDER.get(min_level.upper(), 0)
print(f"min_level_value = {min_level_value}")

test_lines = [
    '{"level": "DEBUG", "message": "debug msg"}',
    '{"level": "INFO", "message": "info msg"}',
    '{"level": "WARNING", "message": "warning msg"}',
    '{"level": "ERROR", "message": "error msg"}',
]

for line in test_lines:
    result = check_level_match(line, min_level_value)
    data = json.loads(line)
    print(f"{data['level']:10} -> passes={result}")
