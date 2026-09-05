"""Portable normalization of source metadata captured by platform adapters."""

from pathlib import PureWindowsPath

_FRIENDLY_APPLICATIONS = {
    "discord.exe": "Discord",
    "firefox.exe": "Firefox",
    "telegram.exe": "Telegram",
}


def normalize_source_context(
    process_name: str | None,
    window_title: str | None,
) -> dict[str, str | None]:
    """Build deterministic source context from optional Windows metadata."""
    normalized_process = process_name or None
    application_name: str | None = None
    if normalized_process is not None:
        executable_name = PureWindowsPath(normalized_process).name
        application_name = _FRIENDLY_APPLICATIONS.get(executable_name.casefold())
        if application_name is None:
            application_name = PureWindowsPath(executable_name).stem or executable_name

    return {
        "application_name": application_name,
        "process_name": normalized_process,
        "window_title": window_title or None,
    }
