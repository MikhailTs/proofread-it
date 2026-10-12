"""Component tests for the credential-free per-invocation launcher."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

_SENTINEL_ENV = "PROOFREAD_IT_SENTINEL_API_KEY"


def _write_fake_uv(path: Path) -> None:
    path.write_text(
        f"""@echo off
if not "%{_SENTINEL_ENV}%"=="" exit /b 41
> "%PROOFREAD_IT_BACKEND_ARGS_MARKER%" echo %*
echo backend-output
exit /b 0
""",
        encoding="utf-8",
    )


def _write_unicode_fake_uv(path: Path) -> None:
    path.write_text(
        f"""@echo off
if not "%{_SENTINEL_ENV}%"=="" exit /b 41
if not "%PYTHONIOENCODING%"=="utf-8" exit /b 42
"%PROOFREAD_IT_TEST_PYTHON%" -c "%PROOFREAD_IT_UNICODE_PROBE%"
exit /b %ERRORLEVEL%
""",
        encoding="utf-8",
    )


def _run_wrapper(
    repository_root: Path,
    settings_path: Path,
    fake_bin: Path,
    marker_path: Path,
    profile: str | None = "proofread",
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PROOFREAD_IT_BACKEND_ARGS_MARKER"] = str(marker_path)
    environment["PROOFREAD_IT_TEST_PYTHON"] = sys.executable
    environment["PROOFREAD_IT_UNICODE_PROBE"] = (
        "import sys; sys.stdout.buffer.write(('I received the caf' + chr(233) + ' menu.' "
        "+ chr(13) + chr(10) + 'It looks great ' + chr(8212) + ' thanks!').encode('utf-8'))"
    )
    environment["PATH"] = f"{fake_bin}{os.pathsep}{environment['PATH']}"
    environment.pop(_SENTINEL_ENV, None)
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
        encoding="utf-8",
    )


@pytest.mark.parametrize("profile", [None, "alternate"])
def test_wrapper_only_forwards_backend_arguments(
    tmp_path: Path,
    profile: str | None,
) -> None:
    repository_root = Path(__file__).parents[2]
    settings_path = tmp_path / "settings.json"
    fake_bin = tmp_path / "bin"
    marker_path = tmp_path / "backend-args.txt"
    fake_bin.mkdir()
    _write_fake_uv(fake_bin / "uv.cmd")

    result = _run_wrapper(repository_root, settings_path, fake_bin, marker_path, profile)

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "backend-output"
    backend_arguments = marker_path.read_text(encoding="utf-8")
    assert "proofread-it" in backend_arguments
    assert ("--profile" in backend_arguments) == (profile is not None)
    if profile is not None:
        assert f"--profile {profile}" in backend_arguments


def test_wrapper_contains_no_credential_transport_or_storage_access() -> None:
    wrapper = Path("scripts/invoke.ps1").read_text(encoding="utf-8")

    assert "openai_token.txt" not in wrapper
    assert "api_key" not in wrapper.casefold()
    assert "credential" not in wrapper.casefold()
    assert "Get-Content" not in wrapper
    assert "ConvertFrom-Json" not in wrapper
    assert '"User"' not in wrapper
    assert '"Machine"' not in wrapper
    assert 'SetEnvironmentVariable($pythonIoEncodingEnv, "utf-8", "Process")' in wrapper


def test_wrapper_round_trips_unicode_backend_output_as_utf8(tmp_path: Path) -> None:
    repository_root = Path(__file__).parents[2]
    settings_path = tmp_path / "settings.json"
    fake_bin = tmp_path / "bin"
    marker_path = tmp_path / "backend-args.txt"
    fake_bin.mkdir()
    _write_unicode_fake_uv(fake_bin / "uv.cmd")

    result = _run_wrapper(repository_root, settings_path, fake_bin, marker_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == "I received the café menu.\nIt looks great — thanks!"
    assert result.stderr == ""
