"""Scaffold-level package smoke test."""


def test_package_is_importable() -> None:
    import proofread_it

    assert proofread_it.__name__ == "proofread_it"
