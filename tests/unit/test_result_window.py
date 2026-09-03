"""Tests for the result-presentation boundary."""

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
