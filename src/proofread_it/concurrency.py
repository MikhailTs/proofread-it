"""Non-blocking process lock for the single-request boundary."""

import errno
import msvcrt
from pathlib import Path
from types import TracebackType
from typing import BinaryIO, Self

CONCURRENT_EXIT_CODE = 11
CONCURRENT_MESSAGE = "Proofreading is already in progress."


class ConcurrencyError(RuntimeError):
    """Raised when the application cannot establish its concurrency boundary."""


class ConcurrentInvocationError(ConcurrencyError):
    """Raised when another proofreading invocation owns the request lock."""


class SingleRequestLock:
    """Hold an operating-system byte-range lock for one backend invocation."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._stream: BinaryIO | None = None

    def __enter__(self) -> Self:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            stream = self._path.open("a+b")
        except OSError as error:
            raise ConcurrencyError(
                f"Cannot open the proofreading concurrency lock at {self._path}."
            ) from error

        try:
            stream.seek(0, 2)
            if stream.tell() == 0:
                stream.write(b"\0")
                stream.flush()
            stream.seek(0)
        except OSError as error:
            stream.close()
            raise ConcurrencyError(
                f"Cannot prepare the proofreading concurrency lock at {self._path}."
            ) from error

        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            stream.close()
            if error.errno in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                raise ConcurrentInvocationError(CONCURRENT_MESSAGE) from error
            raise ConcurrencyError(
                f"Cannot acquire the proofreading concurrency lock at {self._path}."
            ) from error

        self._stream = stream
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        stream = self._stream
        self._stream = None
        if stream is None:
            return
        try:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            stream.close()
