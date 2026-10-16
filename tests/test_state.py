from datetime import datetime
from zoneinfo import ZoneInfo
from app.state import PollState, StateStore, next_monday


def test_next_monday():
    assert next_monday(datetime(2026, 10, 18, 12, tzinfo=ZoneInfo("Europe/Moscow"))).isoformat() == "2026-10-19"


def test_persistence(tmp_path):
    path = tmp_path / "state.json"
    store = StateStore(path)
    store.state = PollState("2026-10-19", "2026-10-19", "19:30", "Шторм", "published")
    store.save()
    assert StateStore(path).state.status == "published"
