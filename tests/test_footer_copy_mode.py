from tailjlogs import log_view


def test_logfooter_has_copy_props():
    lf = log_view.LogFooter()
    assert hasattr(lf, "copy_raw")
    assert hasattr(lf, "show_panel")


def test_keydebug_timeout_default():
    kd = log_view.KeyDebug()
    assert kd.hide_timeout == 3.0
