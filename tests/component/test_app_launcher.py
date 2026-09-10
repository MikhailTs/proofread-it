"""Static security contracts for the development application launcher."""

import os
import subprocess
import time
from pathlib import Path


def test_launcher_starts_automation_without_reading_or_injecting_the_secret() -> None:
    launcher = Path("scripts/start.ps1").read_text(encoding="utf-8")

    assert "-ArgumentList @([System.IO.Path]::GetFullPath($AutomationPath))" in launcher
    assert "-FilePath $resolvedAutoHotkeyPath" in launcher
    assert "openai_token.txt" not in launcher
    assert "SetEnvironmentVariable" not in launcher
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


def test_launcher_keeps_secret_out_of_automation_and_its_unrelated_child(
    tmp_path: Path,
) -> None:
    repository_root = Path(__file__).parents[2]
    api_key_env = "PROOFREAD_IT_SENTINEL_API_KEY"
    sentinel = "launcher-sentinel-must-not-appear"
    result_path = tmp_path / "automation-environment.txt"
    automation_path = tmp_path / "host.ps1"
    automation_path.write_text(
        f"""
$hostValue = [Environment]::GetEnvironmentVariable("{api_key_env}", "Process")
$childValue = & powershell.exe -NoProfile -NonInteractive -Command `
    "[Environment]::GetEnvironmentVariable('{api_key_env}', 'Process')"
[System.IO.File]::WriteAllText(
    $env:PROOFREAD_IT_LAUNCH_RESULT,
    "$hostValue|$childValue"
)
""".strip(),
        encoding="utf-8",
    )
    secret_path = tmp_path / ".secrets" / "openai_token.txt"
    secret_path.parent.mkdir()
    secret_path.write_text(sentinel, encoding="utf-8")
    environment = os.environ.copy()
    environment["USERPROFILE"] = str(tmp_path)
    environment["PROOFREAD_IT_LAUNCH_RESULT"] = str(result_path)
    environment.pop(api_key_env, None)
    original_parent_value = os.environ.get(api_key_env)

    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(repository_root / "scripts" / "start.ps1"),
            "-AutoHotkeyPath",
            "powershell.exe",
            "-AutomationPath",
            str(automation_path),
        ],
        cwd=repository_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    deadline = time.monotonic() + 5
    while not result_path.exists() and time.monotonic() < deadline:
        time.sleep(0.05)

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert result_path.read_text(encoding="utf-8") == "|"
    assert sentinel not in output
    assert sentinel not in " ".join(result.args)
    assert os.environ.get(api_key_env) == original_parent_value
