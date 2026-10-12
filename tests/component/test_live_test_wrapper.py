"""Component tests for the credential-free live-test launcher."""

import os
import subprocess
from pathlib import Path

_SENTINEL_ENV = "PROOFREAD_IT_SENTINEL_API_KEY"


def test_live_wrapper_passes_only_the_settings_path(tmp_path: Path) -> None:
    repository_root = Path(__file__).parents[2]
    settings_path = tmp_path / "settings.json"
    test_path = tmp_path / "selected-live-test.py"
    fake_bin = tmp_path / "bin"
    observed_path = tmp_path / "observed-settings.txt"
    fake_bin.mkdir()
    (fake_bin / "uv.cmd").write_text(
        f"""@echo off
if not "%{_SENTINEL_ENV}%"=="" exit /b 41
> "%PROOFREAD_IT_OBSERVED_SETTINGS%" echo %PROOFREAD_IT_LIVE_SETTINGS_PATH%
echo 1 passed
exit /b 0
""",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment["PATH"] = f"{fake_bin}{os.pathsep}{environment['PATH']}"
    environment["PROOFREAD_IT_OBSERVED_SETTINGS"] = str(observed_path)
    environment.pop(_SENTINEL_ENV, None)

    result = subprocess.run(
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
            str(test_path),
        ],
        cwd=repository_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
    assert observed_path.read_text(encoding="utf-8").strip() == str(settings_path.resolve())


def test_live_wrapper_contains_no_credential_transport_or_storage_access() -> None:
    wrapper = Path("scripts/test-live.ps1").read_text(encoding="utf-8")

    assert "openai_token.txt" not in wrapper
    assert "api_key" not in wrapper.casefold()
    assert "credential" not in wrapper.casefold()
    assert "Get-Content" not in wrapper
    assert "ConvertFrom-Json" not in wrapper
    assert '"User"' not in wrapper
    assert '"Machine"' not in wrapper
