"""Validation and normalization for structured proofreading results."""

import json
from dataclasses import dataclass

from proofread_it.errors import MalformedResponseError


@dataclass(frozen=True, slots=True)
class ProofreadingResult:
    """Validated result safe for presentation and clipboard consumers."""

    corrections: tuple[str, ...]
    final_text: str


def parse_response(output_text: str) -> ProofreadingResult:
    """Parse one strict JSON result without exposing partial or malformed output."""
    try:
        payload: object = json.loads(output_text)
    except (TypeError, json.JSONDecodeError) as error:
        raise MalformedResponseError("The model returned a malformed response.") from error

    if not isinstance(payload, dict) or set(payload) != {"corrections", "final_text"}:
        raise MalformedResponseError("The model returned a malformed response.")

    corrections = payload["corrections"]
    final_text = payload["final_text"]
    if not isinstance(corrections, list) or not all(
        isinstance(correction, str) for correction in corrections
    ):
        raise MalformedResponseError("The model returned a malformed response.")
    if not isinstance(final_text, str) or not final_text:
        raise MalformedResponseError("The model returned a malformed response.")

    return ProofreadingResult(corrections=tuple(corrections), final_text=final_text)
