from asd_shop.models import RunConfig, RunStatus, TelemetryEvent


def test_run_config_defaults_status_and_paths(tmp_path) -> None:
    config = RunConfig(workspace=tmp_path)
    assert config.workspace == tmp_path
    assert config.status == RunStatus.PENDING


def test_telemetry_event_serializes_metadata() -> None:
    event = TelemetryEvent(
        actor="repository_analyst",
        event_type="stage_started",
        metadata={"stage": "repository_analyst"},
    )
    payload = event.model_dump()
    assert payload["actor"] == "repository_analyst"
    assert payload["metadata"]["stage"] == "repository_analyst"
