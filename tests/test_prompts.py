from asd_shop.prompts import build_prompt


def test_build_prompt_includes_role_and_workspace_context(tmp_path) -> None:
    prompt = build_prompt(
        role="repository_analyst",
        workspace=tmp_path,
        prior_artifacts={"ProjectSnapshot.md": "# snapshot"},
    )
    assert "repository_analyst" in prompt
    assert str(tmp_path) in prompt
    assert "# snapshot" in prompt
