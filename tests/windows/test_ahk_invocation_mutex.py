"""Exercise the real AutoHotkey mutex from independent host processes."""

import subprocess
import time
from pathlib import Path

import pytest


def _autohotkey_executable(repository_root: Path) -> str:
    result = subprocess.run(
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
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip("AutoHotkey v2 is not installed")
    return result.stdout.strip()


def _host_script(path: Path, included_script: Path, *, hold_ms: int) -> None:
    path.write_text(
        "\n".join(
            (
                "#Requires AutoHotkey v2.0",
                "mutexHandle := TryAcquireInvocationMutex()",
                'FileAppend(mutexHandle ? "acquired" : "busy", A_Args[1], "UTF-8")',
                "if mutexHandle {",
                f"    Sleep({hold_ms})",
                "    ReleaseInvocationMutex(mutexHandle)",
                "}",
                "ExitApp",
                f'#Include "{included_script}"',
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _read_marker(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def test_separate_hosts_reject_overlap_and_recover_after_owner_exit(tmp_path: Path) -> None:
    repository_root = Path(__file__).parents[2]
    executable = _autohotkey_executable(repository_root)
    included_script = repository_root / "automation" / "windows" / "proofread-it.ahk"
    first_host = tmp_path / "first-host.ahk"
    second_host = tmp_path / "second-host.ahk"
    first_marker = tmp_path / "first.txt"
    second_marker = tmp_path / "second.txt"
    after_exit_marker = tmp_path / "after-exit.txt"
    after_release_marker = tmp_path / "after-release.txt"
    _host_script(first_host, included_script, hold_ms=10_000)
    _host_script(second_host, included_script, hold_ms=0)

    first = subprocess.Popen(
        [executable, "/ErrorStdOut=UTF-8", str(first_host), str(first_marker)],
        cwd=repository_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 5
        while (
            (not first_marker.exists() or first_marker.stat().st_size == 0)
            and time.monotonic() < deadline
        ):
            if first.poll() is not None:
                break
            time.sleep(0.05)
        assert first_marker.exists(), first.communicate(timeout=1)
        assert _read_marker(first_marker) == "acquired"

        second = subprocess.run(
            [executable, "/ErrorStdOut=UTF-8", str(second_host), str(second_marker)],
            cwd=repository_root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        assert second.returncode == 0, second.stdout + second.stderr
        assert _read_marker(second_marker) == "busy"
    finally:
        if first.poll() is None:
            first.terminate()
        first.communicate(timeout=5)

    after_exit = subprocess.run(
        [executable, "/ErrorStdOut=UTF-8", str(second_host), str(after_exit_marker)],
        cwd=repository_root,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert after_exit.returncode == 0, after_exit.stdout + after_exit.stderr
    assert _read_marker(after_exit_marker) == "acquired"

    after_release = subprocess.run(
        [executable, "/ErrorStdOut=UTF-8", str(second_host), str(after_release_marker)],
        cwd=repository_root,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert after_release.returncode == 0, after_release.stdout + after_release.stderr
    assert _read_marker(after_release_marker) == "acquired"
