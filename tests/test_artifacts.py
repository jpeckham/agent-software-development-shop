from asd_shop.artifacts import append_event, write_markdown_artifact
from asd_shop.models import TelemetryEvent


def test_write_markdown_artifact_creates_named_file(tmp_path) -> None:
    path = write_markdown_artifact(tmp_path, "FeatureProposal.md", "# Proposal")
    assert path.name == "FeatureProposal.md"
    assert path.read_text() == "# Proposal"


def test_append_event_writes_jsonl_line(tmp_path) -> None:
    event = TelemetryEvent(actor="qa", event_type="stage_completed", metadata={"status": "ok"})
    events_path = append_event(tmp_path, event)
    lines = events_path.read_text().splitlines()
    assert len(lines) == 1
    assert '"event_type":"stage_completed"' in lines[0]
