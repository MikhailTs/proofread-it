"""Unit tests for direct credential resolution."""

from pathlib import Path

import pytest

from proofread_it.config.schemas import CredentialSettings
from proofread_it.providers.credentials import (
    CredentialError,
    WindowsCredentialStore,
    resolve_api_key,
)


class FakeNativeCredentialApi:
    def __init__(self, blob: bytes = b"") -> None:
        self.blob = blob
        self.read_targets: list[str] = []
        self.writes: list[tuple[str, str, bytes]] = []
        self.deleted_targets: list[str] = []

    def read_blob(self, target: str) -> bytes:
        self.read_targets.append(target)
        return self.blob

    def write_blob(self, target: str, username: str, blob: bytes) -> None:
        self.writes.append((target, username, blob))

    def delete(self, target: str) -> None:
        self.deleted_targets.append(target)


class FailingStore:
    def __init__(self) -> None:
        self.read_targets: list[str] = []

    def read(self, target: str) -> str:
        self.read_targets.append(target)
        raise CredentialError("configured credential is unavailable")

    def write(self, target: str, api_key: str) -> None:
        raise AssertionError("write must not be called")

    def delete(self, target: str) -> None:
        raise AssertionError("delete must not be called")


def test_file_source_reads_fixed_user_profile_path(tmp_path: Path) -> None:
    secret_path = tmp_path / ".secrets" / "openai_token.txt"
    secret_path.parent.mkdir()
    secret_path.write_text("  sentinel-api-key\n", encoding="utf-8")

    api_key = resolve_api_key(
        CredentialSettings(source="file"),
        environ={"USERPROFILE": str(tmp_path)},
    )

    assert api_key == "sentinel-api-key"


@pytest.mark.parametrize("state", ["missing_profile", "missing_file", "empty"])
def test_unusable_file_source_fails_safely(tmp_path: Path, state: str) -> None:
    environment: dict[str, str] = {}
    if state != "missing_profile":
        environment["USERPROFILE"] = str(tmp_path)
    if state == "empty":
        secret_path = tmp_path / ".secrets" / "openai_token.txt"
        secret_path.parent.mkdir()
        secret_path.write_text(" \r\n\t", encoding="utf-8")

    with pytest.raises(CredentialError) as raised:
        resolve_api_key(CredentialSettings(source="file"), environ=environment)

    assert "sentinel" not in str(raised.value)


def test_windows_source_reads_unicode_generic_credential() -> None:
    native = FakeNativeCredentialApi("  sentinel-api-key  ".encode("utf-16-le"))
    store = WindowsCredentialStore(native)

    api_key = resolve_api_key(
        CredentialSettings(
            source="windows_credential_manager",
            target="ProofreadIt/Test",
        ),
        store=store,
    )

    assert api_key == "sentinel-api-key"
    assert native.read_targets == ["ProofreadIt/Test"]


@pytest.mark.parametrize("blob", [b"", b"x", b"\x00\xd8"])
def test_empty_or_malformed_windows_value_is_rejected(blob: bytes) -> None:
    store = WindowsCredentialStore(FakeNativeCredentialApi(blob))

    with pytest.raises(CredentialError, match=r"empty|malformed"):
        store.read("ProofreadIt/Test")


def test_windows_store_writes_unicode_and_deletes_by_target() -> None:
    native = FakeNativeCredentialApi()
    store = WindowsCredentialStore(native)

    store.write("ProofreadIt/Test", "  sentinel-api-key  ")
    store.delete("ProofreadIt/Test")

    assert native.writes == [
        (
            "ProofreadIt/Test",
            "OPENAI_API_KEY",
            "sentinel-api-key".encode("utf-16-le"),
        )
    ]
    assert native.deleted_targets == ["ProofreadIt/Test"]


def test_windows_source_never_falls_back_to_existing_file(tmp_path: Path) -> None:
    secret_path = tmp_path / ".secrets" / "openai_token.txt"
    secret_path.parent.mkdir()
    secret_path.write_text("file-sentinel", encoding="utf-8")
    store = FailingStore()

    with pytest.raises(CredentialError, match="unavailable"):
        resolve_api_key(
            CredentialSettings(
                source="windows_credential_manager",
                target="ProofreadIt/Missing",
            ),
            environ={"USERPROFILE": str(tmp_path)},
            store=store,
        )

    assert store.read_targets == ["ProofreadIt/Missing"]
