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


def test_architect_prompt_includes_observability_contract_guidance(tmp_path) -> None:
    prompt = build_prompt(
        role="architect",
        workspace=tmp_path,
        prior_artifacts={"FeatureSpec.md": "# spec"},
    )
    assert "observability" in prompt.lower()
    assert "structured event" in prompt.lower()


def test_business_analyst_prompt_includes_behavior_contract_guidance(tmp_path) -> None:
    prompt = build_prompt(
        role="business_analyst",
        workspace=tmp_path,
        prior_artifacts={"FeatureProposal.md": "# proposal"},
    )
    assert "observable outcomes" in prompt.lower()
    assert "acceptance criteria" in prompt.lower()
