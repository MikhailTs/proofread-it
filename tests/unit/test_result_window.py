"""Tests for the result-presentation boundary."""

import tkinter as tk
from types import SimpleNamespace
from typing import Any

from pytest import MonkeyPatch

from proofread_it.presentation import result_window


def test_show_result_supplies_both_fields_to_renderer(monkeypatch: MonkeyPatch) -> None:
    rendered: list[result_window.ResultView] = []
    monkeypatch.setattr(result_window, "_show_tkinter_window", rendered.append)

    result_window.show_result(
        explanations=("Fix the spelling.", "Keep the original tone."),
        final_text="This is the corrected text.",
    )

    assert rendered == [
        result_window.ResultView(
            explanation="Fix the spelling.\nKeep the original tone.",
            final_text="This is the corrected text.",
        )
    ]


class _TextStub:
    def __init__(self) -> None:
        self.inserted: tuple[str, str] | None = None
        self.configuration: dict[str, object] = {}
        self.bindings: dict[str, tuple[object, str | None]] = {}
        self.clipboard: list[str] = []
        self.focused = False
        self.selected_text = "selected result"
        self.tag_range: tuple[str, str, str] | None = None
        self.insertion_mark: tuple[str, str] | None = None
        self.visible_index: str | None = None

    def insert(self, index: str, value: str) -> None:
        self.inserted = (index, value)

    def configure(self, **options: object) -> None:
        self.configuration.update(options)

    def bind(self, sequence: str, callback: object, add: str | None = None) -> None:
        self.bindings[sequence] = (callback, add)

    def focus_set(self) -> None:
        self.focused = True

    def tag_add(self, tag: str, start: str, end: str) -> None:
        self.tag_range = (tag, start, end)

    def mark_set(self, mark: str, index: str) -> None:
        self.insertion_mark = (mark, index)

    def see(self, index: str) -> None:
        self.visible_index = index

    def get(self, start: str, end: str) -> str:
        assert (start, end) == (tk.SEL_FIRST, tk.SEL_LAST)
        return self.selected_text

    def clipboard_clear(self) -> None:
        self.clipboard.clear()

    def clipboard_append(self, value: str) -> None:
        self.clipboard.append(value)


def _event(widget: _TextStub) -> Any:
    return SimpleNamespace(widget=widget)


def test_result_text_is_focusable_read_only_and_has_copy_shortcuts(
    monkeypatch: MonkeyPatch,
) -> None:
    widget = _TextStub()
    monkeypatch.setattr(result_window.scrolledtext, "ScrolledText", lambda *_args, **_kwargs: widget)

    created = result_window._read_only_text(object(), "Corrected text", height=5)  # type: ignore[arg-type]

    assert created is widget
    assert widget.inserted == ("1.0", "Corrected text")
    assert widget.configuration == {"state": tk.DISABLED, "takefocus": True}
    assert set(widget.bindings) == {
        "<Button-1>",
        "<Control-a>",
        "<Control-A>",
        "<Control-c>",
        "<Control-C>",
    }
    assert widget.bindings["<Button-1>"][1] == "+"


def test_click_focuses_disabled_text_and_control_a_selects_it() -> None:
    widget = _TextStub()

    result_window._focus_text(_event(widget))
    binding_result = result_window._select_all(_event(widget))

    assert widget.focused is True
    assert widget.tag_range == (tk.SEL, "1.0", "end-1c")
    assert widget.insertion_mark == (tk.INSERT, "1.0")
    assert widget.visible_index == "1.0"
    assert binding_result == "break"


def test_control_c_copies_selected_text() -> None:
    widget = _TextStub()

    binding_result = result_window._copy_selection(_event(widget))

    assert widget.clipboard == ["selected result"]
    assert binding_result == "break"


def test_copy_text_replaces_clipboard_with_complete_result() -> None:
    widget = _TextStub()
    widget.clipboard.append("old value")

    result_window._copy_text(widget, "Complete corrected result")  # type: ignore[arg-type]

    assert widget.clipboard == ["Complete corrected result"]
