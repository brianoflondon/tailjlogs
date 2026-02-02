import sys
import types
from unittest.mock import Mock

import pytest

from tailjlogs import log_view


def test_copy_uses_pbcopy_on_macos(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")

    mock_run = Mock()
    monkeypatch.setattr(log_view, "subprocess", types.SimpleNamespace(run=mock_run))

    ok, err = log_view._copy_to_clipboard("hello")

    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert args[0] == ["pbcopy"]
    assert kwargs.get("input") == b"hello"
    assert ok is True
    assert err is None


def test_copy_uses_wl_copy_when_present(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")

    # Simulate wl-copy present and subprocess.run available
    monkeypatch.setattr(
        log_view,
        "shutil",
        types.SimpleNamespace(
            which=lambda name: "/usr/bin/wl-copy" if name == "wl-copy" else None
        ),
    )
    mock_run = Mock()
    monkeypatch.setattr(log_view, "subprocess", types.SimpleNamespace(run=mock_run))

    ok, err = log_view._copy_to_clipboard("{" + '"a":1' + "}")

    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert args[0] == ["wl-copy"]
    assert kwargs.get("input") == b'{"a":1}'
    assert ok is True
    assert err is None


def test_copy_falls_back_to_tkinter(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")

    # No clipboard utilities
    monkeypatch.setattr(log_view, "shutil", types.SimpleNamespace(which=lambda name: None))

    # Provide a fake tkinter module
    class FakeTk:
        def __init__(self):
            pass

        def withdraw(self):
            pass

        def clipboard_clear(self):
            pass

        def clipboard_append(self, text):
            self._text = text

        def update(self):
            pass

        def destroy(self):
            pass

    fake_module = types.SimpleNamespace(Tk=FakeTk)
    monkeypatch.setitem(sys.modules, "tkinter", fake_module)

    ok, err = log_view._copy_to_clipboard("hi")
    assert ok is True
    assert err is None


def test_format_line_for_copy_pretty_and_raw():
    line = '{"a":1,"b":"text"}'
    pretty = log_view._format_line_for_copy(line, raw=False)
    assert pretty.startswith('{\n  "a": 1,')
    raw = log_view._format_line_for_copy(line, raw=True)
    assert raw == line


def test_format_line_for_copy_invalid_raises():
    bad = "not a json"

    with pytest.raises(ValueError):
        log_view._format_line_for_copy(bad, raw=False)
