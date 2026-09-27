"""Minimal desktop presentation for a complete proofreading result."""

import ctypes
import sys
import time
import tkinter as tk
from collections.abc import Sequence
from dataclasses import dataclass
from tkinter import scrolledtext, ttk


@dataclass(frozen=True, slots=True)
class ResultView:
    """Technology-neutral values rendered by the result window."""

    explanation: str
    final_text: str


def show_result(*, explanations: Sequence[str], final_text: str) -> None:
    """Show explanatory corrections and the complete result text."""
    explanation = "\n".join(explanations)
    _show_tkinter_window(ResultView(explanation=explanation, final_text=final_text))


def _show_tkinter_window(view: ResultView) -> None:
    root = tk.Tk()
    root.title("Proofread It")
    root.geometry("760x560")
    root.minsize(520, 380)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    content = ttk.Frame(root, padding=16)
    content.grid(row=0, column=0, sticky="nsew")
    content.columnconfigure(0, weight=1)
    content.rowconfigure(1, weight=1)
    content.rowconfigure(3, weight=2)

    ttk.Label(content, text="Explanation").grid(row=0, column=0, sticky="w", pady=(0, 6))
    explanation = _read_only_text(content, view.explanation, height=7)
    explanation.grid(row=1, column=0, sticky="nsew", pady=(0, 16))

    ttk.Label(content, text="Result").grid(row=2, column=0, sticky="w", pady=(0, 6))
    result = _read_only_text(content, view.final_text, height=14)
    result.grid(row=3, column=0, sticky="nsew", pady=(0, 16))

    actions = ttk.Frame(content)
    actions.grid(row=4, column=0, sticky="e")
    ttk.Button(
        actions,
        text="Copy result",
        command=lambda: _copy_text(root, view.final_text),
    ).grid(row=0, column=0, padx=(0, 8))
    ttk.Button(actions, text="Close", command=root.destroy).grid(row=0, column=1)
    root.bind("<Escape>", lambda _event: root.destroy())
    root.mainloop()


def _read_only_text(parent: ttk.Frame, value: str, *, height: int) -> scrolledtext.ScrolledText:
    widget = scrolledtext.ScrolledText(
        parent,
        height=height,
        wrap=tk.WORD,
        font=("Segoe UI", 10),
        padx=8,
        pady=8,
    )
    widget.insert("1.0", value)
    widget.configure(state=tk.DISABLED, takefocus=True)
    widget.bind("<Button-1>", _focus_text, add="+")
    widget.bind("<Control-a>", _select_all)
    widget.bind("<Control-A>", _select_all)
    widget.bind("<Control-c>", _copy_selection)
    widget.bind("<Control-C>", _copy_selection)
    return widget


def _focus_text(event: tk.Event[tk.Text]) -> None:
    event.widget.focus_set()


def _select_all(event: tk.Event[tk.Text]) -> str:
    event.widget.tag_add(tk.SEL, "1.0", "end-1c")
    event.widget.mark_set(tk.INSERT, "1.0")
    event.widget.see("1.0")
    return "break"


def _copy_selection(event: tk.Event[tk.Text]) -> str:
    try:
        selected_text = event.widget.get(tk.SEL_FIRST, tk.SEL_LAST)
    except tk.TclError:
        return "break"

    _copy_text(event.widget, selected_text)
    return "break"


def _copy_text(owner: tk.Misc, value: str) -> None:
    normalized = _normalize_clipboard_text(value)
    if sys.platform == "win32":
        _copy_windows_clipboard_text(normalized)
        return

    _copy_tk_clipboard_text(owner, normalized)


def _copy_tk_clipboard_text(owner: tk.Misc, value: str) -> None:
    owner.clipboard_clear()
    owner.clipboard_append(value)
    owner.update()


def _normalize_clipboard_text(value: str) -> str:
    """Represent every logical line break with one line feed."""
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _copy_windows_clipboard_text(value: str) -> None:
    """Transfer Unicode text ownership to Windows so it survives the result window."""
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.restype = ctypes.c_int
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = ctypes.c_int
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = ctypes.c_int
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.restype = ctypes.c_int
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.restype = ctypes.c_void_p

    for _attempt in range(5):
        if user32.OpenClipboard(None):
            break
        time.sleep(0.01)
    else:
        raise ctypes.WinError(ctypes.get_last_error())

    memory_handle: int | None = None
    ownership_transferred = False
    try:
        if not user32.EmptyClipboard():
            raise ctypes.WinError(ctypes.get_last_error())

        windows_text = value.replace("\n", "\r\n")
        payload = windows_text.encode("utf-16-le") + b"\x00\x00"
        memory_handle = kernel32.GlobalAlloc(0x0002, len(payload))
        if not memory_handle:
            raise ctypes.WinError(ctypes.get_last_error())

        pointer = kernel32.GlobalLock(memory_handle)
        if not pointer:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            ctypes.memmove(pointer, payload, len(payload))
        finally:
            kernel32.GlobalUnlock(memory_handle)

        if not user32.SetClipboardData(13, memory_handle):
            raise ctypes.WinError(ctypes.get_last_error())
        ownership_transferred = True
    finally:
        if memory_handle and not ownership_transferred:
            kernel32.GlobalFree(memory_handle)
        user32.CloseClipboard()
