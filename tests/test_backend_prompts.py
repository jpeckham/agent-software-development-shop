from asd_shop.prompts import build_prompt
from asd_shop.roles import ROLE_BY_NAME


def test_build_prompt_includes_expected_artifact_file_for_stage(tmp_path) -> None:
    role = ROLE_BY_NAME["developer"]
    prompt = build_prompt(role=role.name, workspace=tmp_path, prior_artifacts={})
    assert role.artifact_filename in prompt


def test_developer_prompt_forbids_asking_for_task_again(tmp_path) -> None:
    prompt = build_prompt(
        role="developer",
        workspace=tmp_path,
        prior_artifacts={"FeatureSpec.md": "# spec"},
    )
    assert "Do not ask for the task again" in prompt


def test_product_manager_prompt_prefers_user_visible_features(tmp_path) -> None:
    prompt = build_prompt(
        role="product_manager",
        workspace=tmp_path,
        prior_artifacts={"ProjectSnapshot.md": "# snapshot"},
    )
    assert "Prefer player-visible or user-visible functionality" in prompt


def test_codex_developer_prompt_is_imperative_not_role_framed(tmp_path) -> None:
    plans_dir = tmp_path / "docs" / "plans"
    plans_dir.mkdir(parents=True)
    plan_path = plans_dir / "2026-03-15-home-decomposition-implementation.md"
    plan_path.write_text("# plan", encoding="utf-8")
    prompt = build_prompt(
        role="developer",
        workspace=tmp_path,
        prior_artifacts={"FeatureSpec.md": "# spec", "ArchitectureDecision.md": "# adr"},
        backend_name="codex",
    )
    assert prompt.startswith("Implement the feature now")
    assert "Role: developer" not in prompt
    assert "Do not create or ask for a worktree" in prompt
    assert str(plan_path) in prompt
    assert "Execute Task 1 immediately" in prompt
    assert "FeatureSpec.md" in prompt
    assert "# spec" not in prompt


def test_codex_qa_prompt_references_artifact_files_instead_of_embedding_contents(tmp_path) -> None:
    prompt = build_prompt(
        role="qa",
        workspace=tmp_path,
        prior_artifacts={"TechnicalDesign.md": "# detailed design\n" * 1000},
        backend_name="codex",
    )
    assert "TechnicalDesign.md" in prompt
    assert "# detailed design" not in prompt
