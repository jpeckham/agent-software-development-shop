from asd_shop.backend_registry import get_backend


def test_get_backend_returns_codex_backend() -> None:
    backend = get_backend("codex")
    assert backend.__class__.__name__ == "CodexCliBackend"
