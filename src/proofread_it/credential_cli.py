"""Interactive management for the configured Windows generic credential."""

import argparse
import getpass
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from proofread_it.config.loader import ConfigurationError, load_settings
from proofread_it.providers.credentials import (
    CredentialError,
    CredentialStore,
    WindowsCredentialStore,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="proofread-it-credential")
    parser.add_argument("--settings", required=True, type=Path)
    parser.add_argument("action", choices=("set", "remove"))
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    store: CredentialStore | None = None,
    prompt: Callable[[str], str] = getpass.getpass,
) -> int:
    """Set or remove the configured generic credential without printing its value."""
    options = _parser().parse_args(argv)
    try:
        settings = load_settings(options.settings)
        if settings.credential.source != "windows_credential_manager":
            raise ConfigurationError(
                "settings.credential.source must be 'windows_credential_manager' "
                "for credential management"
            )
        target = settings.credential.target
        if target is None:
            raise ConfigurationError("settings.credential.target is required")

        selected_store = WindowsCredentialStore() if store is None else store
        if options.action == "set":
            api_key = prompt("OpenAI API key: ")
            selected_store.write(target, api_key)
            del api_key
            print(f"Stored Windows credential {target!r} for the current user.")
        else:
            selected_store.delete(target)
            print(f"Removed Windows credential {target!r} for the current user.")
    except (ConfigurationError, CredentialError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
