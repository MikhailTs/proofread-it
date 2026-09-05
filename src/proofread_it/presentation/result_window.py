"""Minimal desktop presentation for a complete proofreading result."""

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

    ttk.Button(content, text="Close", command=root.destroy).grid(row=4, column=0, sticky="e")
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
    widget.configure(state=tk.DISABLED)
    return widget
