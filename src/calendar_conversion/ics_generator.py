"""Generate interoperable iCalendar files from normalized events."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from os import PathLike
from pathlib import Path
from typing import TextIO

from .event import Event
from .validator import ValidationIssue, validate_events


PRODID = "-//calendar-conversion//EN"


class ICSGenerationError(ValueError):
    """Raised when invalid events cannot safely be written to iCalendar."""

    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues
        super().__init__(
            f"cannot generate calendar: {len(issues)} validation issue(s)"
        )


def generate_ics(
    events: Iterable[Event],
    *,
    calendar_name: str | None = None,
    generated_at: datetime | None = None,
) -> str:
    """Return one RFC 5545 calendar containing all supplied events."""
    event_list = list(events)
    issues = validate_events(event_list)
    if issues:
        raise ICSGenerationError(issues)

    timestamp = _format_utc_datetime(
        datetime.now(timezone.utc) if generated_at is None else generated_at
    )
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
    ]
    if calendar_name is not None:
        lines.append(f"X-WR-CALNAME:{_escape_text(calendar_name)}")

    for event in event_list:
        lines.extend(_event_lines(event, timestamp))

    lines.append("END:VCALENDAR")
    return "".join(f"{_fold_line(line)}\r\n" for line in lines)


def write_ics(
    events: Iterable[Event],
    destination: str | PathLike[str] | TextIO,
    *,
    calendar_name: str | None = None,
    generated_at: datetime | None = None,
) -> None:
    """Generate a calendar and write it to a path or open text stream."""
    calendar = generate_ics(
        events,
        calendar_name=calendar_name,
        generated_at=generated_at,
    )
    if hasattr(destination, "write"):
        destination.write(calendar)  # type: ignore[union-attr]
        return

    path = Path(destination)
    with path.open("w", encoding="utf-8", newline="") as ics_file:
        ics_file.write(calendar)


def _event_lines(event: Event, timestamp: str) -> list[str]:
    lines = [
        "BEGIN:VEVENT",
        f"UID:{_escape_text(event.id)}",
        f"DTSTAMP:{timestamp}",
    ]

    assert event.start_date is not None
    assert event.end_date is not None
    if event.all_day:
        exclusive_end_date = event.end_date + timedelta(days=1)
        lines.extend(
            (
                f"DTSTART;VALUE=DATE:{event.start_date:%Y%m%d}",
                f"DTEND;VALUE=DATE:{exclusive_end_date:%Y%m%d}",
            )
        )
    else:
        assert event.start_time is not None
        assert event.end_time is not None
        start = datetime.combine(
            event.start_date, event.start_time, tzinfo=event.timezone
        )
        end = datetime.combine(
            event.end_date, event.end_time, tzinfo=event.timezone
        )
        lines.extend(
            (
                f"DTSTART:{_format_utc_datetime(start)}",
                f"DTEND:{_format_utc_datetime(end)}",
            )
        )

    lines.append(f"SUMMARY:{_escape_text(event.summary)}")
    if event.location:
        lines.append(f"LOCATION:{_escape_text(event.location)}")
    if event.description:
        lines.append(f"DESCRIPTION:{_escape_text(event.description)}")
    lines.append("END:VEVENT")
    return lines


def _format_utc_datetime(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("generated_at must include timezone information")
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _escape_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def _fold_line(line: str) -> str:
    """Fold one content line without exceeding RFC 5545's 75-octet limit."""
    segments: list[str] = []
    current = ""
    byte_limit = 75

    for character in line:
        if current and len((current + character).encode("utf-8")) > byte_limit:
            segments.append(current)
            current = character
            # Continuation lines begin with one space, leaving 74 octets.
            byte_limit = 74
        else:
            current += character

    segments.append(current)
    return "\r\n ".join(segments)
