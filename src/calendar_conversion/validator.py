"""Semantic validation for normalized calendar events."""

from collections.abc import Iterable
from dataclasses import dataclass
import sys
from typing import TextIO

from .event import Event


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One validation problem found in an event.

    ``event_index`` is the one-based position supplied by ``validate_events``.
    It is ``None`` when ``validate_event`` is called directly.
    """

    field: str
    message: str
    event_id: str
    event_index: int | None = None


def validate_event(
    event: Event, *, event_index: int | None = None
) -> list[ValidationIssue]:
    """Return every semantic validation issue found in one event."""
    issues: list[ValidationIssue] = []

    if not event.id.strip():
        issues.append(
            ValidationIssue(
                field="id",
                message="id must not be empty",
                event_id=event.id,
                event_index=event_index,
            )
        )

    if not event.summary.strip():
        issues.append(
            ValidationIssue(
                field="summary",
                message="summary must not be empty",
                event_id=event.id,
                event_index=event_index,
            )
        )

    # Event's structural validation guarantees that both dates are present.
    assert event.start_date is not None
    assert event.end_date is not None

    if event.start_date > event.end_date:
        issues.append(
            ValidationIssue(
                field="end_date",
                message="end_date must not be before start_date",
                event_id=event.id,
                event_index=event_index,
            )
        )
    elif not event.all_day and event.start_date == event.end_date:
        # A timed event on one date must also be ordered by its clock times.
        assert event.start_time is not None
        assert event.end_time is not None
        if event.start_time > event.end_time:
            issues.append(
                ValidationIssue(
                    field="end_time",
                    message="end_time must not be before start_time",
                    event_id=event.id,
                    event_index=event_index,
                )
            )

    return issues


def validate_events(events: Iterable[Event]) -> list[ValidationIssue]:
    """Return all issues, annotated with each event's one-based position."""
    issues: list[ValidationIssue] = []
    for event_index, event in enumerate(events, start=1):
        issues.extend(validate_event(event, event_index=event_index))
    return issues


def print_validation_errors(
    issues: Iterable[ValidationIssue], *, file: TextIO | None = None
) -> None:
    """Print validation issues as bold red terminal error messages."""
    output = sys.stdout if file is None else file
    for issue in issues:
        event_id = issue.event_id or "<empty>"
        print(
            f"\033[1;31mInvalid event [id={event_id}]: "
            f"{issue.message}\033[0m",
            file=output,
        )
