"""Unit tests for strict proofreading-response normalization."""

import pytest

from proofread_it.errors import MalformedResponseError
from proofread_it.responses.parser import ProofreadingResult, parse_response


def test_parses_populated_and_empty_correction_lists() -> None:
    assert parse_response(
        '{"corrections":["Fix agreement."],"final_text":"She goes."}'
    ) == ProofreadingResult(corrections=("Fix agreement.",), final_text="She goes.")
    assert parse_response('{"corrections":[],"final_text":"Already correct."}') == (
        ProofreadingResult(corrections=(), final_text="Already correct.")
    )


@pytest.mark.parametrize(
    "output_text",
    [
        "not-json",
        "[]",
        '{"corrections":[]}',
        '{"corrections":[],"final_text":"Text","extra":true}',
        '{"corrections":"none","final_text":"Text"}',
        '{"corrections":[3],"final_text":"Text"}',
        '{"corrections":[],"final_text":3}',
        '{"corrections":[],"final_text":""}',
    ],
)
def test_rejects_output_outside_the_canonical_shape(output_text: str) -> None:
    with pytest.raises(MalformedResponseError, match="malformed response"):
        parse_response(output_text)
