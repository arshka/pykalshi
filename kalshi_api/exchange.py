from __future__ import annotations
from typing import TYPE_CHECKING
from .models import ExchangeStatus, ExchangeSchedule, Announcement, ScheduleEntry

if TYPE_CHECKING:
    from .client import KalshiClient


class Exchange:
    """Exchange status, schedule, and announcements."""

    def __init__(self, client: KalshiClient) -> None:
        self._client = client

    @property
    def status(self) -> ExchangeStatus:
        """Get current exchange operational status."""
        data = self._client.get("/exchange/status")
        return ExchangeStatus.model_validate(data)

    @property
    def is_trading(self) -> bool:
        """Quick check if trading is currently active."""
        return self.status.trading_active

    def get_schedule(self) -> ExchangeSchedule:
        """Get exchange trading schedule."""
        data = self._client.get("/exchange/schedule")
        entries = [ScheduleEntry.model_validate(s) for s in data.get("schedule", [])]
        return ExchangeSchedule(schedule=entries)

    def get_announcements(self) -> list[Announcement]:
        """Get exchange-wide announcements."""
        data = self._client.get("/exchange/announcements")
        return [Announcement.model_validate(a) for a in data.get("announcements", [])]

    def get_user_data_timestamp(self) -> int:
        """Get timestamp of last user data validation (Unix ms)."""
        data = self._client.get("/exchange/user_data_timestamp")
        return data.get("user_data_timestamp", 0)
