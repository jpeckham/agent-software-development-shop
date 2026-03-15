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
