"""Pure provider-neutral logical-request construction."""

import json
from collections.abc import Mapping
from copy import deepcopy
from typing import Final

from proofread_it.config.schemas import Profile, Settings
from proofread_it.models import LogicalRequest

PROOFREADING_RESULT_SCHEMA: Final[dict[str, object]] = {
    "type": "object",
    "properties": {
        "corrections": {"type": "array", "items": {"type": "string"}},
        "final_text": {"type": "string", "minLength": 1},
    },
    "required": ["corrections", "final_text"],
    "additionalProperties": False,
}

_KNOWN_CONTEXT_FIELDS: Final = frozenset(
    ("application_name", "process_name", "window_title")
)


def build_request(
    text: str,
    profile: Profile,
    source_context: Mapping[str, str | None],
    settings: Settings,
) -> LogicalRequest:
    """Build the exact three-part logical request without reading local state or sending it."""
    if not isinstance(text, str) or not text:
        raise ValueError("text must be a non-empty string")

    unknown_fields = sorted(set(source_context) - _KNOWN_CONTEXT_FIELDS)
    if unknown_fields:
        raise ValueError(f"source_context.{unknown_fields[0]} is not supported")
    for field, value in source_context.items():
        if value is not None and not isinstance(value, str):
            raise ValueError(f"source_context.{field} must be a string or None")

    globally_allowed = set(settings.context.fields)
    transmitted_context = {
        field: source_context.get(field)
        for field in profile.context_fields
        if field in globally_allowed
    }
    dynamic_input = {
        "source_context": transmitted_context,
        "selected_text": text,
    }

    return {
        "parts": [
            {"kind": "instructions", "text": profile.instructions},
            {
                "kind": "output_contract",
                "schema": deepcopy(PROOFREADING_RESULT_SCHEMA),
            },
            {
                "kind": "input",
                "media_type": "application/json",
                "text": json.dumps(
                    dynamic_input,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            },
        ]
    }
