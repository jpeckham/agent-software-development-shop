from asd_shop.prompts import build_prompt
from asd_shop.roles import ROLE_BY_NAME


def test_build_prompt_includes_expected_artifact_file_for_stage(tmp_path) -> None:
    role = ROLE_BY_NAME["developer"]
    prompt = build_prompt(role=role.name, workspace=tmp_path, prior_artifacts={})
    assert role.artifact_filename in prompt
