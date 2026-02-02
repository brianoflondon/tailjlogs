from __future__ import annotations

import json
import shutil
import subprocess
import sys
from asyncio import Lock
from datetime import datetime

from textual import events, on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.dom import NoScreen
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


def _copy_to_clipboard(text: str) -> tuple[bool, str | None]:
    """Copy text to the system clipboard using platform utilities.

    Tries macOS `pbcopy`, Wayland `wl-copy`, X11 `xclip`/`xsel`, then falls back to
    Tkinter if available. Returns (True, None) on success or (False, error_message).
    """
    try:
        # macOS
        if sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
            return True, None

        # Windows
        if sys.platform.startswith("win"):
            subprocess.run("clip", input=text.encode("utf-8"), check=True, shell=True)
            return True, None

        # Linux / BSD - try common clipboard tools
        if shutil.which("wl-copy"):
            subprocess.run(["wl-copy"], input=text.encode("utf-8"), check=True)
            return True, None
        if shutil.which("xclip"):
            subprocess.run(
                ["xclip", "-selection", "clipboard"], input=text.encode("utf-8"), check=True
            )
            return True, None
        if shutil.which("xsel"):
            subprocess.run(
                ["xsel", "--clipboard", "--input"], input=text.encode("utf-8"), check=True
            )
            return True, None

        # Final fallback: Tkinter if available
        try:
            import tkinter as _tk

            root = _tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            root.destroy()
            return True, None
        except Exception as exc:  # pragma: no cover - environment dependent
            return False, f"No clipboard utility found: {exc}"
    except Exception as exc:  # pragma: no cover - runtime error
        return False, str(exc)


def _format_line_for_copy(line: str, raw: bool = False) -> str:
    """Return the string that should be copied for the given line.

    - If raw is True, returns the original line unchanged.
    - If raw is False, attempts to parse and pretty-print JSON; raises ValueError
      if parsing fails.
    """
    if raw:
        return line

    try:
        data = json.loads(line)
    except Exception as exc:  # pragma: no cover - parsing error handled by caller
        raise ValueError("Not valid JSON") from exc

    return json.dumps(data, indent=2, ensure_ascii=False)


from tailjlogs.find_dialog import FilterDialog, FindDialog
from tailjlogs.line_panel import LinePanel
from tailjlogs.log_lines import LogLines
from tailjlogs.messages import (
    DismissOverlay,
    Goto,
    PendingLines,
    PointerMoved,
    ScanComplete,
    ScanProgress,
    TailFile,
)
from tailjlogs.scan_progress_bar import ScanProgressBar
from tailjlogs.watcher import WatcherBase

SPLIT_REGEX = r"[\s/\[\]]"

MAX_DETAIL_LINE_LENGTH = 100_000


class KeyDebug(Widget):
    """Temporary overlay to display the last key event received (for debugging).

    Shows the last key event and auto-hides after `hide_timeout` seconds of
    inactivity (default 3s)."""

    DEFAULT_CSS = """
    KeyDebug {
        display: none;
        dock: top;
        align: right top;
        layer: overlay;
        padding: 0 1;
        margin: 1;
        background: $panel-darken-1;
        color: $accent;
        border: heavy $accent;
        width: auto;
        height: auto;
    }

    KeyDebug .message {
        width: auto;
        height: auto;
    }
    KeyDebug.visible {
        display: block;
    }
    """

    message = reactive("")
    hide_timeout: reactive[float] = reactive(3.0)
    # Bound from LogView to control visibility
    show_key_debug: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        super().__init__()
        self._hide_timer = None

    def watch_show_key_debug(self, show: bool) -> None:
        # toggle visible class when bound attribute changes
        self.set_class(show, "visible")

    def compose(self) -> ComposeResult:
        yield Label("", classes="message")

    def _clear_message(self) -> None:
        self.message = ""
        if self._hide_timer is not None:
            try:
                self._hide_timer.stop()
            except Exception:
                pass
            self._hide_timer = None

    def watch_message(self, message: str) -> None:
        # Only update the label if the widget is mounted and a Label child exists.
        if not getattr(self, "is_mounted", False):
            return
        try:
            self.query_one(Label).update(message)
        except Exception:
            # No Label present yet or query failed; ignore for now.
            pass

        # Cancel any existing timer and set a new one when message is non-empty
        if self._hide_timer is not None:
            try:
                self._hide_timer.stop()
            except Exception:
                pass
            self._hide_timer = None

        if message:
            # Schedule auto-hide after hide_timeout seconds
            try:
                self._hide_timer = self.set_timer(self.hide_timeout, self._clear_message)
            except Exception:
                # set_timer might not be available in very old Textual versions
                self._hide_timer = None

    def on_click(self) -> None:
        # Clicking clears the message
        self._clear_message()


class InfoOverlay(Widget):
    """Displays text under the lines widget when there are new lines."""

    DEFAULT_CSS = """
    InfoOverlay {
        display: none;
        dock: bottom;
        layer: overlay;
        width: 1fr;
        visibility: hidden;
        offset-y: -1;
        text-style: bold;
    }

    InfoOverlay Horizontal {
        width: 1fr;
        align: center bottom;
    }

    InfoOverlay Label {
        visibility: visible;
        width: auto;
        height: 1;
        background: $panel;
        color: $success;
        padding: 0 1;

        &:hover {
            background: $success;
            color: auto 90%;
            text-style: bold;
        }
    }
    """

    message = reactive("")
    tail = reactive(False)

    def compose(self) -> ComposeResult:
        self.tooltip = "Click to tail file"
        with Horizontal():
            yield Label("")

    def watch_message(self, message: str) -> None:
        self.display = bool(message.strip())
        self.query_one(Label).update(message)

    def watch_tail(self, tail: bool) -> None:
        if not tail:
            self.message = ""
        self.display = bool(self.message.strip() and not tail)

    def on_click(self) -> None:
        self.post_message(TailFile())


class FooterKey(Label):
    """Displays a clickable label for a key."""

    DEFAULT_CSS = """
    FooterKey {
        color: $success;
        &:light {
            color: $primary;
        }
        padding: 0 1 0 0;
        &:hover {
            text-style: bold underline;
        }
    }
    """
    DEFAULT_CLASSES = "key"

    def __init__(self, key: str, key_display: str, description: str, action: str) -> None:
        self.key = key
        self.key_display = key_display
        self.description = description
        self.action = action
        super().__init__()

    def render(self) -> str:
        return f"[reverse]{self.key_display}[/reverse] {self.description}"

    async def on_click(self) -> None:
        await self.app.run_action(self.action)


class MetaLabel(Label):
    DEFAULT_CSS = """
    MetaLabel {
        margin-left: 1;
    }
    MetaLabel:hover {
        text-style: underline;
    }
    """

    def on_click(self) -> None:
        self.post_message(Goto())


class LogFooter(Widget):
    """Shows a footer with information about the file and keys."""

    DEFAULT_CSS = """
    LogFooter {
        layout: horizontal;
        height: 1;
        width: 1fr;
        dock: bottom;
        Horizontal {
            width: 1fr;
            height: 1;
        }

        .key {
            color: $warning;
        }

        .meta {
            width: auto;
            height: 1;
            color: $success;
            padding: 0 1 0 0;
        }

        .tail {
            padding: 0 1;
            margin: 0 1;
            background: $success 15%;
            color: $success;
            text-style: bold;
            display: none;
            &.on {
                display: block;
            }
        }
    }
    """
    line_no: reactive[int | None] = reactive(None)
    filename: reactive[str] = reactive("")
    timestamp: reactive[datetime | None] = reactive(None)
    tail: reactive[bool] = reactive(False)
    can_tail: reactive[bool] = reactive(False)
    # Reflects copy mode for detail panel (False=Pretty, True=Raw)
    copy_raw: reactive[bool] = reactive(False)
    # Whether the detail panel is shown
    show_panel: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        self.lock = Lock()
        super().__init__()

    def compose(self) -> ComposeResult:
        with Horizontal(classes="key-container"):
            pass
        yield Label("TAIL", classes="tail")
        yield MetaLabel("", classes="meta")

    async def mount_keys(self) -> None:
        try:
            if self.screen != self.app.screen:
                return
        except NoScreen:
            pass
        async with self.lock:
            with self.app.batch_update():
                key_container = self.query_one(".key-container")
                await key_container.query("*").remove()
                bindings = [
                    active_binding.binding
                    for active_binding in self.app.active_bindings.values()
                    if active_binding.binding.show
                ]

                await key_container.mount_all(
                    [
                        FooterKey(
                            binding.key,
                            binding.key_display or binding.key,
                            binding.description,
                            binding.action,
                        )
                        for binding in bindings
                        if binding.action != "toggle_tail"
                        or (binding.action == "toggle_tail" and self.can_tail)
                    ]
                )

    async def on_mount(self):
        self.watch(self.screen, "focused", self.mount_keys)
        self.watch(self.screen, "stack_updates", self.mount_keys)
        self.call_after_refresh(self.mount_keys)

    def update_meta(self) -> None:
        meta: list[str] = []
        if self.filename:
            meta.append(self.filename)
        if self.timestamp is not None:
            meta.append(f"{self.timestamp:%x %X}")
        if self.line_no is not None:
            meta.append(f"{self.line_no + 1}")

        # Show copy mode indicator when the detail panel is visible
        if self.show_panel:
            meta.append(f"Copy: {'Raw' if self.copy_raw else 'Pretty'}")

        meta_line = " • ".join(meta)
        # Be defensive if widget not fully mounted
        try:
            self.query_one(".meta", Label).update(meta_line)
        except Exception:
            pass

    def watch_tail(self, tail: bool) -> None:
        self.query(".tail").set_class(tail and self.can_tail, "on")

    async def watch_can_tail(self, can_tail: bool) -> None:
        await self.mount_keys()

    def watch_filename(self, filename: str) -> None:
        self.update_meta()

    def watch_line_no(self, line_no: int | None) -> None:
        self.update_meta()

    def watch_timestamp(self, timestamp: datetime | None) -> None:
        self.update_meta()


class LogView(Horizontal):
    """Widget that contains log lines and associated widgets."""

    DEFAULT_CSS = """
    LogView {
        &.show-panel {
            LinePanel {
                display: block;
            }
        }
        LogLines {
            width: 1fr;
        }
        LinePanel {
            width: 50%;
            display: none;
        }
    }
    """

    BINDINGS = [
        Binding("ctrl+t", "toggle_tail", "Tail", key_display="^t"),
        Binding("ctrl+l", "toggle('show_line_numbers')", "Line nos.", key_display="^l"),
        Binding("ctrl+f", "show_find_dialog", "Find", key_display="^f"),
        Binding("slash", "show_find_dialog", "Find", key_display="^f", show=False),
        Binding("backslash", "show_filter_dialog", "Filter", key_display="\\"),
        Binding("ctrl+g", "goto", "Go to", key_display="^g"),
        # Copy JSON detail to system clipboard:
        Binding("meta+c", "copy_json", "Copy JSON", key_display="⌘C"),
        Binding("ctrl+shift+c", "copy_json", "Copy JSON", key_display="^⇧C", show=False),
        # Direct copy with plain 'c' key (handy on mac) and toggle for debug overlay
        Binding("c", "copy_json", "Copy JSON (c)", show=False),
        Binding("ctrl+k", "toggle_key_debug", "Key debug", key_display="^K"),
        # Toggle copy format between Pretty (default) and Raw
        Binding("y", "toggle_copy_format", "Toggle copy format", key_display="y"),
    ]

    show_find: reactive[bool] = reactive(False)
    show_filter: reactive[bool] = reactive(False)
    show_panel: reactive[bool] = reactive(False)
    show_line_numbers: reactive[bool] = reactive(False)
    tail: reactive[bool] = reactive(False)
    can_tail: reactive[bool] = reactive(True)
    # When False (default) copy uses pretty-printed JSON; when True copies raw JSON line
    copy_raw: reactive[bool] = reactive(False)
    # Key debug overlay visibility
    show_key_debug: reactive[bool] = reactive(False)

    def __init__(
        self,
        file_paths: list[str],
        watcher: WatcherBase,
        can_tail: bool = True,
        max_lines: int | None = None,
        min_level: str | None = None,
    ) -> None:
        self.file_paths = file_paths
        self.watcher = watcher
        self.max_lines = max_lines
        self.min_level = min_level
        super().__init__()
        self.can_tail = can_tail

    def compose(self) -> ComposeResult:
        yield (
            log_lines := LogLines(
                self.watcher, self.file_paths, max_lines=self.max_lines, min_level=self.min_level
            ).data_bind(
                LogView.tail,
                LogView.show_line_numbers,
                LogView.show_find,
                LogView.can_tail,
            )
        )
        yield LinePanel()
        yield FindDialog(log_lines._suggester)
        yield FilterDialog(log_lines._suggester)
        yield InfoOverlay().data_bind(LogView.tail)
        yield LogFooter().data_bind(
            LogView.tail, LogView.can_tail, LogView.copy_raw, LogView.show_panel
        )
        # Key debug overlay (toggleable)
        yield KeyDebug().data_bind(LogView.show_key_debug)

    @on(FindDialog.Update)
    def find_dialog_update(self, event: FindDialog.Update) -> None:
        log_lines = self.query_one(LogLines)
        log_lines.find = event.find
        log_lines.regex = event.regex
        log_lines.case_sensitive = event.case_sensitive

    @on(FilterDialog.Update)
    def filter_dialog_update(self, event: FilterDialog.Update) -> None:
        log_lines = self.query_one(LogLines)
        log_lines.filter_text = event.filter_text
        log_lines.filter_regex = event.regex
        log_lines.filter_case_sensitive = event.case_sensitive

    async def watch_show_find(self, show_find: bool) -> None:
        if not self.is_mounted:
            return
        find_dialog = self.query_one(FindDialog)
        find_dialog.set_class(show_find, "visible")
        if show_find:
            find_dialog.focus_input()
        else:
            self.query_one(LogLines).focus()

    async def watch_show_filter(self, show_filter: bool) -> None:
        if not self.is_mounted:
            return
        filter_dialog = self.query_one(FilterDialog)
        filter_dialog.set_class(show_filter, "visible")
        if show_filter:
            filter_dialog.focus_input()
        else:
            self.query_one(LogLines).focus()

    async def watch_show_panel(self, show_panel: bool) -> None:
        self.set_class(show_panel, "show-panel")
        await self.update_panel()

    async def watch_show_key_debug(self, show: bool) -> None:
        try:
            key_debug = self.query_one(KeyDebug)
        except Exception:
            return
        key_debug.set_class(show, "visible")

    @on(FindDialog.Dismiss)
    def dismiss_find_dialog(self, event: FindDialog.Dismiss) -> None:
        event.stop()
        self.show_find = False

    @on(FilterDialog.Dismiss)
    def dismiss_filter_dialog(self, event: FilterDialog.Dismiss) -> None:
        event.stop()
        self.show_filter = False

    @on(FindDialog.MovePointer)
    def move_pointer(self, event: FindDialog.MovePointer) -> None:
        event.stop()
        log_lines = self.query_one(LogLines)
        log_lines.advance_search(event.direction)

    @on(FindDialog.SelectLine)
    def select_line(self) -> None:
        self.show_panel = not self.show_panel

    @on(DismissOverlay)
    def dismiss_overlay(self) -> None:
        if self.show_find:
            self.show_find = False
        elif self.show_filter:
            self.show_filter = False
        elif self.show_panel:
            self.show_panel = False
        else:
            self.query_one(LogLines).pointer_line = None

    @on(TailFile)
    def on_tail_file(self, event: TailFile) -> None:
        self.tail = event.tail
        event.stop()

    async def update_panel(self) -> None:
        if not self.show_panel:
            return
        pointer_line = self.query_one(LogLines).pointer_line
        if pointer_line is not None:
            line, text, timestamp = self.query_one(LogLines).get_text(
                pointer_line,
                block=True,
                abbreviate=True,
                max_line_length=MAX_DETAIL_LINE_LENGTH,
            )
            await self.query_one(LinePanel).update(line, text, timestamp)

    @on(PointerMoved)
    async def pointer_moved(self, event: PointerMoved):
        if event.pointer_line is None:
            self.show_panel = False
        if self.show_panel:
            await self.update_panel()

        log_lines = self.query_one(LogLines)
        pointer_line = (
            log_lines.scroll_offset.y if event.pointer_line is None else event.pointer_line
        )
        log_file, _, _ = log_lines.index_to_span(pointer_line)
        log_footer = self.query_one(LogFooter)
        log_footer.line_no = pointer_line
        if len(log_lines.log_files) > 1:
            log_footer.filename = log_file.name

        timestamp = log_lines.get_timestamp(pointer_line)
        log_footer.timestamp = timestamp

    @on(PendingLines)
    def on_pending_lines(self, event: PendingLines) -> None:
        if self.app._exit:
            return
        event.stop()
        self.query_one(InfoOverlay).message = f"+{event.count:,} lines"

    @on(ScanProgress)
    def on_scan_progress(self, event: ScanProgress):
        event.stop()
        scan_progress_bar = self.query_one(ScanProgressBar)
        scan_progress_bar.message = event.message
        scan_progress_bar.complete = event.complete

    @on(ScanComplete)
    async def on_scan_complete(self, event: ScanComplete) -> None:
        self.query_one(ScanProgressBar).remove()
        log_lines = self.query_one(LogLines)
        log_lines.loading = False
        self.query_one("LogLines").remove_class("-scanning")
        self.post_message(PointerMoved(log_lines.pointer_line))
        self.tail = True

        footer = self.query_one(LogFooter)
        footer.call_after_refresh(footer.mount_keys)

    @on(events.DescendantFocus)
    @on(events.DescendantBlur)
    def on_descendant_focus(self, event: events.DescendantBlur) -> None:
        self.set_class(isinstance(self.screen.focused, LogLines), "lines-view")

    def action_toggle_tail(self) -> None:
        if not self.can_tail:
            self.notify("Can't tail this file", title="Tail", severity="error")
        else:
            self.tail = not self.tail

    def action_toggle_key_debug(self) -> None:
        """Toggle the key-debug overlay that shows last key events."""
        self.show_key_debug = not self.show_key_debug
        mode = "on" if self.show_key_debug else "off"
        self.notify(f"Key debug: {mode}", title="Debug")

    @on(events.Key)
    def on_key_event(self, event: events.Key) -> None:
        # Do not stop event propagation; this is purely observational.
        if not self.show_key_debug:
            return
        # Try common attributes for key and modifiers; be defensive.
        key = (
            getattr(event, "key", None)
            or getattr(event, "character", None)
            or getattr(event, "key_name", None)
            or str(event)
        )
        mods: list[str] = []
        for m in ("ctrl", "shift", "meta", "alt"):
            try:
                if getattr(event, m, False):
                    mods.append(m)
            except Exception:
                pass
        # Some Textual versions provide a 'modifiers' tuple
        if hasattr(event, "modifiers"):
            try:
                mods.extend([str(x) for x in event.modifiers])
            except Exception:
                pass
        mod_text = ",".join(mods) if mods else "none"
        message = f"Key: {key} | Mods: {mod_text}"
        try:
            self.query_one(KeyDebug).message = message
        except Exception:
            pass

    def action_show_find_dialog(self) -> None:
        find_dialog = self.query_one(FindDialog)
        if not self.show_find or not any(input.has_focus for input in find_dialog.query("Input")):
            self.show_find = True
            find_dialog.focus_input()

    def action_show_filter_dialog(self) -> None:
        filter_dialog = self.query_one(FilterDialog)
        if not self.show_filter or not any(
            input.has_focus for input in filter_dialog.query("Input")
        ):
            self.show_filter = True
            filter_dialog.focus_input()

    @on(Goto)
    def on_goto(self) -> None:
        self.action_goto()

    def action_goto(self) -> None:
        from tailjlogs.goto_screen import GotoScreen

        self.app.push_screen(GotoScreen(self.query_one(LogLines)))

    def action_copy_json(self) -> None:
        """Copy the JSON object shown in the detail panel to the clipboard.

        Uses the current copy format (pretty vs raw). If the detail panel is not
        open, or the selected line is not valid JSON when pretty is requested,
        a notification is shown.
        """
        if not self.show_panel:
            self.notify("Open the line panel (Enter) to view/copy JSON", title="Copy")
            return

        log_lines = self.query_one(LogLines)
        pointer_line = log_lines.pointer_line
        if pointer_line is None:
            self.notify("No line selected", title="Copy", severity="error")
            return

        line, _text, _timestamp = log_lines.get_text(pointer_line, block=True, abbreviate=False)

        try:
            out = _format_line_for_copy(line, raw=self.copy_raw)
        except ValueError:
            self.notify("Current line is not valid JSON", title="Copy", severity="error")
            return

        ok, err = _copy_to_clipboard(out)
        if ok:
            fmt = "Raw" if self.copy_raw else "Pretty"
            self.notify(f"Copied {fmt} JSON to clipboard", title="Copy")
        else:
            self.notify(f"Copy failed: {err}", title="Copy", severity="error")

    def action_toggle_copy_format(self) -> None:
        """Toggle between pretty-printed and raw JSON when copying."""
        self.copy_raw = not self.copy_raw
        mode = "Raw" if self.copy_raw else "Pretty"
        self.notify(f"Copy format: {mode}", title="Copy")
