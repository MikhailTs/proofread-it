"""Unit tests for source-context normalization."""

import pytest

from proofread_it.config.schemas import ExclusionSettings
from proofread_it.context.normalize import normalize_source_context
from proofread_it.context.policy import ExclusionMatch, find_source_exclusion


@pytest.mark.parametrize(
    ("process_name", "application_name"),
    [
        ("firefox.exe", "Firefox"),
        ("Discord.exe", "Discord"),
        ("KeePass.exe", "KeePass"),
        ("Telegram.exe", "Telegram"),
        ("code.exe", "code"),
        (r"C:\\Tools\\editor.exe", "editor"),
        (None, None),
    ],
)
def test_maps_known_and_unknown_processes_deterministically(
    process_name: str | None,
    application_name: str | None,
) -> None:
    context = normalize_source_context(process_name, "Draft" if process_name else "")

    assert context == {
        "application_name": application_name,
        "process_name": process_name,
        "window_title": "Draft" if process_name else None,
    }


def test_process_exclusion_matches_executable_basename_case_insensitively() -> None:
    match = find_source_exclusion(
        r"C:\Portable\KEEPASS.EXE",
        "Ordinary note",
        ExclusionSettings(process_names=("KeePass.exe",)),
    )

    assert match == ExclusionMatch(kind="process_name", value="KeePass.exe")


@pytest.mark.parametrize(
    "title",
    ["Password", "enter PASSWORD now", "vault: password-required"],
)
def test_title_exclusion_matches_a_whole_word_case_insensitively(title: str) -> None:
    match = find_source_exclusion(
        "editor.exe",
        title,
        ExclusionSettings(window_title_words=("password",)),
    )

    assert match == ExclusionMatch(kind="window_title_word", value="password")


@pytest.mark.parametrize("title", ["passwords", "onepassword", "password_manager", ""])
def test_title_exclusion_does_not_match_part_of_another_word(title: str) -> None:
    assert (
        find_source_exclusion(
            "editor.exe",
            title,
            ExclusionSettings(window_title_words=("password",)),
        )
        is None
    )


def test_process_rules_precede_title_rules_and_missing_values_do_not_match() -> None:
    exclusions = ExclusionSettings(
        process_names=("KeePass.exe",),
        window_title_words=("password",),
    )

    assert find_source_exclusion("KeePass.exe", "Password", exclusions) == ExclusionMatch(
        kind="process_name", value="KeePass.exe"
    )
    assert find_source_exclusion(None, None, exclusions) is None
