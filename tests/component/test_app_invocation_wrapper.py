"""Component tests for per-invocation backend credential delivery."""

import json
import os
import subprocess
from pathlib import Path

import pytest

_API_KEY_ENV = "PROOFREAD_IT_SENTINEL_API_KEY"
_SENTINEL = "invocation-wrapper-sentinel-must-not-appear"


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
                "concurrency": {"lock_path": "request.lock"},
                "logging": {"path": "events.jsonl"},
            }
        ),
        encoding="utf-8",
    )


def _write_fake_uv(path: Path) -> None:
    path.write_text(
        f"""@echo off
if "%~7"=="proofread_it.invocation_failure" (
> "%PROOFREAD_IT_LOG_MARKER%" echo failure-logger-ran
exit /b 0
)
if not \"%{_API_KEY_ENV}%\"==\"{_SENTINEL}\" exit /b 41
> \"%PROOFREAD_IT_BACKEND_MARKER%\" echo backend-observed-key
> \"%PROOFREAD_IT_BACKEND_ARGS_MARKER%\" echo %*
echo backend-output
exit /b 0
""",
        encoding="utf-8",
    )


def _run_wrapper(
    repository_root: Path,
    settings_path: Path,
    user_profile: Path,
    fake_bin: Path,
    marker_path: Path,
    profile: str | None = "proofread",
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["USERPROFILE"] = str(user_profile)
    environment["PROOFREAD_IT_BACKEND_MARKER"] = str(marker_path)
    environment["PROOFREAD_IT_BACKEND_ARGS_MARKER"] = str(
        marker_path.with_name("backend-args.txt")
    )
    environment["PROOFREAD_IT_LOG_MARKER"] = str(marker_path.with_name("failure-log.txt"))
    environment["PATH"] = f"{fake_bin}{os.pathsep}{environment['PATH']}"
    environment.pop(_API_KEY_ENV, None)
    arguments = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(repository_root / "scripts" / "invoke.ps1"),
        "-SettingsPath",
        str(settings_path),
    ]
    if profile is not None:
        arguments += ["-Profile", profile]
    arguments += ["-Action", "copy_final"]
    return subprocess.run(
        arguments,
        cwd=repository_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("profile", [None, "alternate"])
def test_wrapper_exposes_secret_only_to_the_selected_backend_tree(
    tmp_path: Path, profile: str | None
) -> None:
    repository_root = Path(__file__).parents[2]
    settings_path = tmp_path / "settings.json"
    secret_path = tmp_path / ".secrets" / "openai_token.txt"
    fake_bin = tmp_path / "bin"
    marker_path = tmp_path / "backend-ran.txt"
    secret_path.parent.mkdir()
    fake_bin.mkdir()
    secret_path.write_text(f"  {_SENTINEL}\n", encoding="utf-8")
    _write_settings(settings_path)
    _write_fake_uv(fake_bin / "uv.cmd")
    original_parent_value = os.environ.get(_API_KEY_ENV)

    result = _run_wrapper(repository_root, settings_path, tmp_path, fake_bin, marker_path, profile)

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert result.stdout.strip() == "backend-output"
    assert marker_path.read_text(encoding="utf-8").strip() == "backend-observed-key"
    backend_arguments = marker_path.with_name("backend-args.txt").read_text(encoding="utf-8")
    assert ("--profile" in backend_arguments) == (profile is not None)
    if profile is not None:
        assert f"--profile {profile}" in backend_arguments
    assert _SENTINEL not in output
    assert _SENTINEL not in " ".join(result.args)
    assert os.environ.get(_API_KEY_ENV) == original_parent_value


@pytest.mark.parametrize("secret_state", ["missing", "empty", "unreadable"])
def test_wrapper_fails_before_backend_when_secret_file_is_unusable(
    tmp_path: Path,
    secret_state: str,
) -> None:
    repository_root = Path(__file__).parents[2]
    settings_path = tmp_path / "settings.json"
    secret_path = tmp_path / ".secrets" / "openai_token.txt"
    fake_bin = tmp_path / "bin"
    marker_path = tmp_path / "backend-ran.txt"
    secret_path.parent.mkdir()
    fake_bin.mkdir()
    if secret_state == "empty":
        secret_path.write_text(" \r\n\t", encoding="utf-8")
    elif secret_state == "unreadable":
        secret_path.mkdir()
    _write_settings(settings_path)
    _write_fake_uv(fake_bin / "uv.cmd")

    result = _run_wrapper(repository_root, settings_path, tmp_path, fake_bin, marker_path)

    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert not marker_path.exists()
    assert marker_path.with_name("failure-log.txt").read_text(encoding="utf-8").strip() == (
        "failure-logger-ran"
    )
    assert _SENTINEL not in output


def test_wrapper_never_targets_persistent_environment_scopes_or_arguments() -> None:
    wrapper = Path("scripts/invoke.ps1").read_text(encoding="utf-8")

    assert 'SetEnvironmentVariable($apiKeyEnv, $apiKey, "Process")' in wrapper
    assert 'SetEnvironmentVariable($apiKeyEnv, $previousApiKey, "Process")' in wrapper
    assert '"User"' not in wrapper
    assert '"Machine"' not in wrapper
    backend_start = wrapper.index("& uv run --project")
    backend_command = wrapper[backend_start : wrapper.index("} finally", backend_start)]
    assert "$apiKey" not in backend_command


def test_missing_secret_is_logged_by_the_real_failure_helper(tmp_path: Path) -> None:
    repository_root = Path(__file__).parents[2]
    settings_path = tmp_path / "settings.json"
    _write_settings(settings_path)
    environment = os.environ.copy()
    environment["USERPROFILE"] = str(tmp_path)
    environment["PROOFREAD_IT_SOURCE_TEXT"] = "Captured draft"
    environment.pop(_API_KEY_ENV, None)

    result = subprocess.run(
        [
            "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
            "-File", str(repository_root / "scripts" / "invoke.ps1"),
            "-SettingsPath", str(settings_path), "-Action", "copy_final",
        ],
        cwd=repository_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    log_path = tmp_path / "events.jsonl"
    assert log_path.exists(), result.stdout + result.stderr
    raw_log = log_path.read_text(encoding="utf-8")
    event = json.loads(raw_log)
    assert result.returncode != 0
    assert event["event"] == "invocation_failed"
    assert event["stage"] == "credential"
    assert event["source_text"] == "Captured draft"
    assert event["logical_request"] is None
    assert _SENTINEL not in raw_log + result.stdout + result.stderr
