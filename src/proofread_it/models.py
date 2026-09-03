"""Provider-neutral logical request models."""

from typing import Literal, TypedDict


class InstructionsPart(TypedDict):
    """Stable profile instructions with the highest request authority."""

    kind: Literal["instructions"]
    text: str


class OutputContractPart(TypedDict):
    """Canonical structured-output contract."""

    kind: Literal["output_contract"]
    schema: dict[str, object]


class InputPart(TypedDict):
    """Serialized, untrusted per-request input."""

    kind: Literal["input"]
    media_type: Literal["application/json"]
    text: str


type RequestPart = InstructionsPart | OutputContractPart | InputPart


class LogicalRequest(TypedDict):
    """Ordered logical request before provider-specific adaptation."""

    parts: list[RequestPart]
