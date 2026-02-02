import sys
from tailjlogs import log_view


def test_send_osc52_encodes(monkeypatch):
    writes = []

    class FakeStdout:
        def write(self, s):
            writes.append(s)
        def flush(self):
            pass

    monkeypatch.setattr(sys, "stdout", FakeStdout())

    ok, err = log_view._send_osc52("Hello", max_bytes=65536)
    assert ok is True
    assert err is None
    assert any("\x1b]52;c;SGVsbG8=\a" in w for w in writes)


def test_send_osc52_too_large():
    large = "a" * 70000
    ok, err = log_view._send_osc52(large, max_bytes=65536)
    assert ok is False
    assert "too large" in err.lower()


def test_copy_fallback_to_osc52(monkeypatch):
    # Simulate no clipboard utilities and force using OSC52
    monkeypatch.setenv("TAILJLOGS_COPY_METHOD", "osc52")
    monkeypatch.setattr(log_view, "shutil", type("S", (), {"which": lambda name: None})())

    called = {}

    def fake_osc52(text, max_bytes=0):
        called['text'] = text
        return True, None

    monkeypatch.setattr(log_view, "_send_osc52", fake_osc52)

    ok, err = log_view._copy_to_clipboard('{"a": 1}')
    assert ok is True
    assert 'text' in called