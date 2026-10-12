"""Explicit native Windows Credential Manager round-trip verification."""

from uuid import uuid4

import pytest

from proofread_it.providers.credentials import WindowsCredentialStore


@pytest.mark.credential_store
def test_generic_credential_round_trip_uses_a_temporary_target() -> None:
    target = f"ProofreadIt/Test/{uuid4()}"
    sentinel = f"credential-store-sentinel-{uuid4()}"
    store = WindowsCredentialStore()
    created = False
    try:
        store.write(target, sentinel)
        created = True

        assert store.read(target) == sentinel
    finally:
        if created:
            store.delete(target)
