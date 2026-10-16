"""Single-process durable weekly poll state (atomic JSON writes)."""
import json
import os
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import settings


@dataclass
class PollState:
    week: str
    date: str
    time: str
    place: str
    status: str = "draft"  # draft, publishing, published, cancelled, uncertain
    message_id: int | None = None
    poll_id: str | None = None


def next_monday(now: datetime | None = None) -> date:
    now = now or datetime.now(ZoneInfo(settings.timezone))
    days = (7 - now.weekday()) % 7 or 7
    return (now + timedelta(days=days)).date()


def current_week_key(now: datetime | None = None) -> str:
    return next_monday(now).isoformat()


class StateStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.state = self._load()

    def _load(self) -> PollState | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        state = PollState(**data)
        if state.status not in {"draft", "publishing", "published", "cancelled", "uncertain"}:
            raise ValueError("Invalid poll status")
        return state

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_name(self.path.name + ".tmp")
        with temp.open("w", encoding="utf-8") as handle:
            json.dump(asdict(self.state), handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, self.path)

    def get_or_create(self) -> PollState:
        key = current_week_key()
        if self.state is None or self.state.week != key:
            self.state = PollState(week=key, date=key, time=settings.default_time, place=settings.default_place)
            self.save()
        return self.state

    def set_status(self, status: str) -> None:
        self.get_or_create().status = status
        self.save()


store = StateStore(settings.state_path)
