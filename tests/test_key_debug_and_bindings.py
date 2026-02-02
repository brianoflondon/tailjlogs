from tailjlogs import log_view


def test_logview_has_c_and_ctrlk_bindings():
    keys = [b.key for b in log_view.LogView.BINDINGS]
    assert "c" in keys
    assert "ctrl+k" in keys


def test_key_debug_widget_present_in_compose():
    # Ensure KeyDebug class exists and has message reactive
    assert hasattr(log_view, "KeyDebug")
    kd = log_view.KeyDebug()
    assert hasattr(kd, "message")
    # update message and ensure attribute updated
    kd.message = "test"
    assert kd.message == "test"