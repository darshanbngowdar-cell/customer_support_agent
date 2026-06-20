import os

from support_agent.config.settings import Settings, get_settings


def test_settings_loads_environment_variables(monkeypatch) -> None:
    monkeypatch.setenv("SUPPORT_AGENT_APP_ENV", "production")
    monkeypatch.setenv("SUPPORT_AGENT_LOG_LEVEL", "DEBUG")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.app_env == "production"
    assert settings.log_level == "DEBUG"
    assert settings.cache_enabled is True
    assert settings.rate_limit_max_requests == 10


def test_settings_secret_field_is_hidden() -> None:
    settings = Settings(openai_api_key="supersecret")

    assert settings.openai_api_key.get_secret_value() == "supersecret"
    assert "supersecret" not in repr(settings)
