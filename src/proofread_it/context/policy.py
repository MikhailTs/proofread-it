"""Portable source-exclusion matching."""

import re
from dataclasses import dataclass
from pathlib import PureWindowsPath
from typing import Literal

from proofread_it.config.schemas import ExclusionSettings


@dataclass(frozen=True, slots=True)
class ExclusionMatch:
    """The first configured rule that blocks a source."""

    kind: Literal["process_name", "window_title_word"]
    value: str


def find_source_exclusion(
    process_name: str | None,
    window_title: str | None,
    exclusions: ExclusionSettings,
) -> ExclusionMatch | None:
    """Return the deterministic first exclusion matching observed source metadata."""
    if process_name:
        executable_name = PureWindowsPath(process_name).name
        normalized_executable = executable_name.casefold()
        for configured_name in exclusions.process_names:
            if configured_name.casefold() == normalized_executable:
                return ExclusionMatch(kind="process_name", value=configured_name)

    if window_title:
        for configured_word in exclusions.window_title_words:
            if re.search(
                rf"(?<!\w){re.escape(configured_word)}(?!\w)",
                window_title,
                flags=re.IGNORECASE,
            ):
                return ExclusionMatch(kind="window_title_word", value=configured_word)

    return None
