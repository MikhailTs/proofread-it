"""Integration checks for the shipped configuration files."""

from pathlib import Path

from proofread_it.config.loader import load_default_profile, load_settings


def test_shipped_default_profile_loads_with_the_accepted_contract() -> None:
    repository_root = Path(__file__).parents[2]

    settings = load_settings(repository_root / "config" / "settings.json")
    profile = load_default_profile(repository_root / "config" / "profiles.json", settings)

    assert settings.api.model == "gpt-5.6-luna"
    assert settings.api.api_key_env == "OPENAI_API_KEY"
    assert settings.api.timeout_seconds == 30
    assert settings.api.max_output_tokens == 2048
    assert settings.api.retry_count == 2
    assert settings.context.exclusions.process_names == ("KeePass.exe",)
    assert settings.context.exclusions.window_title_words == ("password",)
    assert profile.name == "proofread"
    assert profile.task == "proofread_english"
    assert profile.context_fields == (
        "application_name",
        "process_name",
        "window_title",
    )
    assert profile.instructions.startswith(
        "You are a precise proofreading engine for short English text."
    )
    assert '"corrections"' in profile.instructions
    assert '"final_text"' in profile.instructions
