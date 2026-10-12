"""Direct credential resolution at the provider boundary."""

import ctypes
import os
from collections.abc import Mapping
from ctypes import wintypes
from pathlib import Path
from typing import Any, Protocol

from proofread_it.config.schemas import CredentialSettings

_CRED_TYPE_GENERIC = 1
_CRED_PERSIST_LOCAL_MACHINE = 2
_ERROR_NOT_FOUND = 1168
_MAX_CREDENTIAL_BLOB_SIZE = 5 * 512
_FILE_RELATIVE_PATH = Path(".secrets") / "openai_token.txt"


class CredentialError(RuntimeError):
    """Raised when a required provider credential is unavailable or invalid."""


class CredentialStore(Protocol):
    """Secret-store operations used by runtime and management commands."""

    def read(self, target: str) -> str: ...

    def write(self, target: str, api_key: str) -> None: ...

    def delete(self, target: str) -> None: ...


class NativeCredentialApi(Protocol):
    """Mockable byte-level Windows Credential Manager boundary."""

    def read_blob(self, target: str) -> bytes: ...

    def write_blob(self, target: str, username: str, blob: bytes) -> None: ...

    def delete(self, target: str) -> None: ...


class _CredentialW(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


class Win32CredentialApi:
    """Thin ctypes wrapper around the native Credential Manager API."""

    def __init__(self) -> None:
        library = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
        self._cred_read: Any = library.CredReadW
        self._cred_write: Any = library.CredWriteW
        self._cred_delete: Any = library.CredDeleteW
        self._cred_free: Any = library.CredFree

        credential_pointer = ctypes.POINTER(_CredentialW)
        self._cred_read.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(credential_pointer),
        ]
        self._cred_read.restype = wintypes.BOOL
        self._cred_write.argtypes = [ctypes.POINTER(_CredentialW), wintypes.DWORD]
        self._cred_write.restype = wintypes.BOOL
        self._cred_delete.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        self._cred_delete.restype = wintypes.BOOL
        self._cred_free.argtypes = [ctypes.c_void_p]
        self._cred_free.restype = None

    def read_blob(self, target: str) -> bytes:
        credential = ctypes.POINTER(_CredentialW)()
        if not self._cred_read(
            target,
            _CRED_TYPE_GENERIC,
            0,
            ctypes.byref(credential),
        ):
            self._raise_error("read", target)
        try:
            loaded = credential.contents
            return ctypes.string_at(loaded.CredentialBlob, loaded.CredentialBlobSize)
        finally:
            self._cred_free(credential)

    def write_blob(self, target: str, username: str, blob: bytes) -> None:
        if len(blob) > _MAX_CREDENTIAL_BLOB_SIZE:
            raise CredentialError("The API credential is too large for Windows Credential Manager")
        blob_buffer = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
        credential = _CredentialW()
        credential.Type = _CRED_TYPE_GENERIC
        credential.TargetName = target
        credential.CredentialBlobSize = len(blob)
        credential.CredentialBlob = ctypes.cast(
            blob_buffer,
            ctypes.POINTER(ctypes.c_ubyte),
        )
        credential.Persist = _CRED_PERSIST_LOCAL_MACHINE
        credential.UserName = username
        if not self._cred_write(ctypes.byref(credential), 0):
            self._raise_error("write", target)

    def delete(self, target: str) -> None:
        if not self._cred_delete(target, _CRED_TYPE_GENERIC, 0):
            self._raise_error("delete", target)

    @staticmethod
    def _raise_error(operation: str, target: str) -> None:
        error_code = ctypes.get_last_error()
        if error_code == _ERROR_NOT_FOUND:
            raise CredentialError(
                f"Windows Credential Manager credential {target!r} was not found"
            )
        raise CredentialError(
            f"Cannot {operation} Windows Credential Manager credential {target!r} "
            f"(Windows error {error_code})"
        )


class WindowsCredentialStore:
    """Unicode generic credentials stored for the current Windows user."""

    def __init__(self, native: NativeCredentialApi | None = None) -> None:
        self._native = Win32CredentialApi() if native is None else native

    def read(self, target: str) -> str:
        blob = self._native.read_blob(target)
        if len(blob) % 2:
            raise CredentialError(
                f"Windows Credential Manager credential {target!r} has a malformed value"
            )
        try:
            value = blob.decode("utf-16-le").rstrip("\x00").strip()
        except UnicodeDecodeError as error:
            raise CredentialError(
                f"Windows Credential Manager credential {target!r} has a malformed value"
            ) from error
        if not value:
            raise CredentialError(
                f"Windows Credential Manager credential {target!r} is empty"
            )
        return value

    def write(self, target: str, api_key: str) -> None:
        normalized = api_key.strip()
        if not normalized:
            raise CredentialError("The API credential must not be empty")
        self._native.write_blob(target, "OPENAI_API_KEY", normalized.encode("utf-16-le"))

    def delete(self, target: str) -> None:
        self._native.delete(target)


def resolve_api_key(
    settings: CredentialSettings,
    *,
    environ: Mapping[str, str] | None = None,
    store: CredentialStore | None = None,
) -> str:
    """Read one credential from exactly the configured source without fallback."""
    if settings.source == "windows_credential_manager":
        if settings.target is None:
            raise CredentialError("Windows Credential Manager target is not configured")
        selected_store = WindowsCredentialStore() if store is None else store
        return selected_store.read(settings.target)

    environment = os.environ if environ is None else environ
    user_profile = environment.get("USERPROFILE")
    if not user_profile or not user_profile.strip():
        raise CredentialError("USERPROFILE is unavailable; cannot locate the API credential file")
    secret_path = Path(user_profile) / _FILE_RELATIVE_PATH
    try:
        api_key = secret_path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise CredentialError(f"Cannot read the API credential file {secret_path!s}") from error
    if not api_key:
        raise CredentialError(f"The API credential file {secret_path!s} is empty")
    return api_key
