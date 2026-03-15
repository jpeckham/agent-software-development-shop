from asd_shop.config import Settings


def test_settings_no_longer_require_provider_selection() -> None:
    settings = Settings()
    assert hasattr(settings, "runs_dir")
