from asd_shop.providers.mock import MockProvider


def test_mock_provider_returns_role_specific_payload() -> None:
    provider = MockProvider()
    result = provider.generate(role="product_manager", prompt="ignored")
    assert result["title"] == "CLI MVP feature proposal"
    assert "acceptance_criteria" in result
