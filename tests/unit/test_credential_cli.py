"""Unit tests for interactive Windows credential management."""

import json
from pathlib import Path

from pytest import CaptureFixture

from proofread_it.credential_cli import main


class FakeCredentialStore:
    def __init__(self) -> None:
        self.writes: list[tuple[str, str]] = []
        self.deleted_targets: list[str] = []

    def read(self, target: str) -> str:
        raise AssertionError("read must not be called")

    def write(self, target: str, api_key: str) -> None:
        self.writes.append((target, api_key))

    def delete(self, target: str) -> None:
        self.deleted_targets.append(target)


def _write_settings(path: Path, source: str = "windows_credential_manager") -> None:
    credential = (
        {"source": source, "target": "ProofreadIt/Test"}
        if source == "windows_credential_manager"
        else {"source": source}
    )
    path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "api": {
                    "model": "gpt-5.6-luna",
                    "timeout_seconds": 30,
                    "max_output_tokens": 2048,
                    "retry_count": 2,
                },
                "credential": credential,
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


def test_set_prompts_for_and_writes_the_key_without_printing_it(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    settings_path = tmp_path / "settings.json"
    _write_settings(settings_path)
    store = FakeCredentialStore()
    sentinel = "management-sentinel-must-not-appear"

    exit_code = main(
        ["--settings", str(settings_path), "set"],
        store=store,
        prompt=lambda _message: sentinel,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert store.writes == [("ProofreadIt/Test", sentinel)]
    assert sentinel not in captured.out + captured.err


def test_remove_deletes_only_the_configured_target(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    settings_path = tmp_path / "settings.json"
    _write_settings(settings_path)
    store = FakeCredentialStore()

    exit_code = main(["--settings", str(settings_path), "remove"], store=store)

    assert exit_code == 0
    assert store.deleted_targets == ["ProofreadIt/Test"]
    assert "ProofreadIt/Test" in capsys.readouterr().out


def test_file_source_cannot_be_managed_as_a_windows_credential(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    settings_path = tmp_path / "settings.json"
    _write_settings(settings_path, source="file")

    exit_code = main(
        ["--settings", str(settings_path), "set"],
        store=FakeCredentialStore(),
        prompt=lambda _message: "must-not-be-read",
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "windows_credential_manager" in captured.err
    assert "must-not-be-read" not in captured.out + captured.err


def test_powershell_management_wrapper_never_accepts_or_reads_the_key() -> None:
    wrapper = Path("scripts/manage-credential.ps1").read_text(encoding="utf-8")

    assert "ApiKey" not in wrapper
    assert "Read-Host" not in wrapper
    assert "Get-Content" not in wrapper
    assert "credential_cli" in wrapper
