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


def test_keydebug_is_bindable_to_logview():
    # KeyDebug should expose a reactive attribute 'show_key_debug' so it can be
    # data-bound to LogView.show_key_debug without raising exceptions.
    kd = log_view.KeyDebug()
    assert hasattr(kd, "show_key_debug")

    # We can't call data_bind outside of a running Textual app (it requires
    # an active message pump), but we can assert that both `KeyDebug` and
    # `LogView` expose the reactive attribute names so binding at compose-time
    # in the app will succeed.
    assert hasattr(log_view.LogView, "show_key_debug")
    assert hasattr(kd, "show_key_debug")
