from asd_shop.config import Settings


def test_settings_uses_mock_provider_by_default() -> None:
    settings = Settings()
    assert settings.provider == "mock"
