"""Unit tests for the non-blocking single-request lock."""

import subprocess
import sys
from pathlib import Path

import pytest

from proofread_it.concurrency import (
    CONCURRENT_MESSAGE,
    ConcurrentInvocationError,
    SingleRequestLock,
)


def test_second_lock_is_rejected_without_waiting(tmp_path: Path) -> None:
    lock_path = tmp_path / "nested" / "request.lock"

    with SingleRequestLock(lock_path):
        with pytest.raises(ConcurrentInvocationError, match=CONCURRENT_MESSAGE):
            with SingleRequestLock(lock_path):
                pytest.fail("the second lock must not be acquired")

    assert lock_path.is_file()


def test_lock_is_released_after_failure(tmp_path: Path) -> None:
    lock_path = tmp_path / "request.lock"

    with pytest.raises(RuntimeError, match="sentinel"):
        with SingleRequestLock(lock_path):
            raise RuntimeError("sentinel")

    with SingleRequestLock(lock_path):
        pass


def test_lock_excludes_another_backend_process(tmp_path: Path) -> None:
    lock_path = tmp_path / "request.lock"
    holder_code = """
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from proofread_it.concurrency import SingleRequestLock

with SingleRequestLock(Path(sys.argv[2])):
    print("locked", flush=True)
    sys.stdin.readline()
"""
    holder = subprocess.Popen(
        [
            sys.executable,
            "-c",
            holder_code,
            str(Path.cwd() / "src"),
            str(lock_path),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout is not None
        assert holder.stdout.readline().strip() == "locked"
        with pytest.raises(ConcurrentInvocationError, match=CONCURRENT_MESSAGE):
            with SingleRequestLock(lock_path):
                pytest.fail("the competing process lock must not be acquired")
    finally:
        holder.communicate("\n", timeout=5)

    assert holder.returncode == 0
