"""Static security contracts for the development application launcher."""

import os
import subprocess
from pathlib import Path


def test_launcher_injects_secret_only_into_the_child_process_tree() -> None:
    launcher = Path("scripts/start.ps1").read_text(encoding="utf-8")

    assert 'Join-Path $env:USERPROFILE ".secrets\\openai_token.txt"' in launcher
    assert 'SetEnvironmentVariable($apiKeyEnv, $apiKey, "Process")' in launcher
    assert 'SetEnvironmentVariable($apiKeyEnv, $previousApiKey, "Process")' in launcher
    assert "-ArgumentList @([System.IO.Path]::GetFullPath($AutomationPath))" in launcher
    assert "-FilePath $resolvedAutoHotkeyPath" in launcher
    assert "$apiKey" not in launcher[launcher.index("Start-Process") : launcher.index("} finally")]
    assert '"User"' not in launcher
    assert '"Machine"' not in launcher


def _resolve_with_environment(
    repository_root: Path,
    environment: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(repository_root / "scripts" / "start.ps1"),
            "-PrintAutoHotkeyPath",
        ],
        cwd=repository_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )


def test_launcher_discovers_a_per_user_autohotkey_v2_installation(tmp_path: Path) -> None:
    repository_root = Path(__file__).parents[2]
    executable = tmp_path / "Programs" / "AutoHotkey" / "v2" / "AutoHotkey64.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"test executable placeholder")
    environment = os.environ.copy()
    environment["LOCALAPPDATA"] = str(tmp_path)

    result = _resolve_with_environment(repository_root, environment)

    assert result.returncode == 0, result.stdout + result.stderr
    assert Path(result.stdout.strip()) == executable


def test_launcher_reports_how_to_supply_a_missing_executable(tmp_path: Path) -> None:
    repository_root = Path(__file__).parents[2]
    environment = os.environ.copy()
    environment["LOCALAPPDATA"] = str(tmp_path / "local")
    environment["ProgramFiles"] = str(tmp_path / "program-files")
    environment["ProgramFiles(x86)"] = str(tmp_path / "program-files-x86")
    environment["PATH"] = ""

    result = _resolve_with_environment(repository_root, environment)

    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "AutoHotkey v2 was not found" in output
    assert "-AutoHotkeyPath" in output
