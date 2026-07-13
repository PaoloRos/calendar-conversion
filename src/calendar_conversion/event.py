"""Internal event representation shared by all conversion components."""

from dataclasses import dataclass, field
from datetime import date, time
from zoneinfo import ZoneInfo


ROME_TIMEZONE = ZoneInfo("Europe/Rome")


@dataclass(frozen=True, slots=True)
class Event:
    """A calendar event in the application's normalized internal format.

    Business-rule validation (for example, ensuring the end occurs after the
    start) belongs to the validator rather than this data container.
    """

    id: str
    summary: str
    all_day: bool = False
    start_date: date | None = None
    start_time: time | None = None
    end_date: date | None = None
    end_time: time | None = None
    location: str = ""
    description: str = ""
    timezone: ZoneInfo = field(default=ROME_TIMEZONE)

    def __post_init__(self) -> None:
        """Ensure the fields match the selected event shape."""
        if self.start_date is None or self.end_date is None:
            raise ValueError("events require both start_date and end_date")

        if self.all_day:
            if self.start_time is not None or self.end_time is not None:
                raise ValueError(
                    "all-day events cannot define start_time or end_time"
                )
        else:
            if self.start_time is None or self.end_time is None:
                raise ValueError(
                    "timed events require both start_time and end_time"
                )
