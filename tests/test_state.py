from datetime import datetime
from zoneinfo import ZoneInfo
from app.state import PollState, StateStore, next_monday


def test_next_monday():
    assert next_monday(datetime(2032, 1, 4, 12, tzinfo=ZoneInfo("UTC"))).isoformat() == "2032-01-05"


def test_persistence(tmp_path):
    path = tmp_path / "state.json"
    store = StateStore(path)
    store.state = PollState("2032-01-05", "2032-01-05", "18:00", "Training venue", "published")
    store.save()
    assert StateStore(path).state.status == "published"
