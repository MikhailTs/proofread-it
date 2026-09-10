"""Component tests for process-local live-test credential injection."""

import json
import os
import subprocess
from pathlib import Path

import pytest

_API_KEY_ENV = "PROOFREAD_IT_SENTINEL_API_KEY"
_SENTINEL = "live-wrapper-sentinel-must-not-appear"


def _write_settings(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "api": {
                    "model": "gpt-5.6-luna",
                    "api_key_env": _API_KEY_ENV,
                    "timeout_seconds": 30,
                    "max_output_tokens": 2048,
                    "retry_count": 2,
                },
                "default_profile": "proofread",
                "context": {
                    "fields": [],
                    "exclusions": {"process_names": [], "window_title_words": []},
                },
                "logging": {"path": "events.jsonl"},
            }
        ),
        encoding="utf-8",
    )


def _run_wrapper(
    repository_root: Path,
    settings_path: Path,
    user_profile: Path,
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["USERPROFILE"] = str(user_profile)
    environment.pop(_API_KEY_ENV, None)
    return subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(repository_root / "scripts" / "test-live.ps1"),
            "-SettingsPath",
            str(settings_path),
            "-TestPath",
            str(repository_root / "tests" / "live" / "test_credential_environment.py"),
        ],
        cwd=repository_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )


def test_wrapper_injects_a_temporary_secret_only_into_the_live_test_process(
    tmp_path: Path,
) -> None:
    repository_root = Path(__file__).parents[2]
    settings_path = tmp_path / "settings.json"
    secret_path = tmp_path / ".secrets" / "openai_token.txt"
    secret_path.parent.mkdir()
    secret_path.write_text(f"  {_SENTINEL}\n", encoding="utf-8")
    _write_settings(settings_path)
    original_parent_value = os.environ.get(_API_KEY_ENV)

    result = _run_wrapper(repository_root, settings_path, tmp_path)

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "1 passed" in output
    assert _SENTINEL not in output
    assert _SENTINEL not in " ".join(result.args)
    assert os.environ.get(_API_KEY_ENV) == original_parent_value


@pytest.mark.parametrize("secret_state", ["missing", "empty", "unreadable"])
def test_wrapper_fails_before_live_tests_when_secret_file_is_unusable(
    tmp_path: Path,
    secret_state: str,
) -> None:
    repository_root = Path(__file__).parents[2]
    settings_path = tmp_path / "settings.json"
    secret_path = tmp_path / ".secrets" / "openai_token.txt"
    secret_path.parent.mkdir()
    if secret_state == "empty":
        secret_path.write_text(" \r\n\t", encoding="utf-8")
    elif secret_state == "unreadable":
        secret_path.mkdir()
    _write_settings(settings_path)

    result = _run_wrapper(repository_root, settings_path, tmp_path)

    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "1 passed" not in output
    assert _SENTINEL not in output


def test_wrapper_never_targets_persistent_environment_scopes() -> None:
    repository_root = Path(__file__).parents[2]

    wrapper = (repository_root / "scripts" / "test-live.ps1").read_text(encoding="utf-8")

    assert '"Process"' in wrapper
    assert '"User"' not in wrapper
    assert '"Machine"' not in wrapper
