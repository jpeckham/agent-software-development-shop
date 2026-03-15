from asd_shop.roles import ROLE_BY_NAME


def test_developer_stage_routes_to_codex() -> None:
    assert ROLE_BY_NAME["developer"].backends == ["codex", "claude"]


def test_repository_analyst_routes_to_claude() -> None:
    assert ROLE_BY_NAME["repository_analyst"].backends == ["claude"]
