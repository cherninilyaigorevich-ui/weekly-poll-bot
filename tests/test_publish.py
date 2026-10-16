import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app import poll_service
from app.state import PollState, StateStore


@pytest.mark.asyncio
async def test_no_duplicate_poll(tmp_path, monkeypatch):
    store = StateStore(tmp_path / "state.json")
    store.state = PollState(
        week="2032-01-05",
        date="2032-01-05",
        time="19:30",
        place="Training venue",
    )
    store.save()

    monkeypatch.setattr(poll_service, "store", store)
    monkeypatch.setattr(
        poll_service,
        "get_preview",
        AsyncMock(return_value="Training"),
    )

    bot = SimpleNamespace(
        send_message=AsyncMock(
            return_value=SimpleNamespace(message_id=101)
        ),
        send_poll=AsyncMock(
            return_value=SimpleNamespace(
                poll=SimpleNamespace(id="poll-123")
            )
        ),
    )

    assert await poll_service.publish_poll(bot) is True
    assert await poll_service.publish_poll(bot) is False

    assert bot.send_message.await_count == 1
    assert bot.send_poll.await_count == 1
    assert store.state.status == "published"
    assert store.state.poll_id == "poll-123"
