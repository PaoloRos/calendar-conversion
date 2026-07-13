"""Tests for semantic event validation."""

from datetime import date, time
from io import StringIO
import unittest

from calendar_conversion import (
    Event,
    print_validation_errors,
    validate_event,
    validate_events,
)


def timed_event(**overrides: object) -> Event:
    values = {
        "id": "shift-1",
        "summary": "Station shift",
        "start_date": date(2026, 7, 10),
        "start_time": time(8, 0),
        "end_date": date(2026, 7, 10),
        "end_time": time(20, 0),
    }
    values.update(overrides)
    return Event(**values)  # type: ignore[arg-type]


class ValidatorTests(unittest.TestCase):
    def test_valid_timed_event_has_no_issues(self) -> None:
        self.assertEqual(validate_event(timed_event()), [])

    def test_valid_all_day_event_has_no_issues(self) -> None:
        event = Event(
            id="training-1",
            summary="Training",
            all_day=True,
            start_date=date(2026, 7, 10),
            end_date=date(2026, 7, 10),
        )

        self.assertEqual(validate_event(event), [])

    def test_rejects_empty_or_whitespace_only_id_and_summary(self) -> None:
        issues = validate_event(timed_event(id="  ", summary=""))

        self.assertEqual([issue.field for issue in issues], ["id", "summary"])
        self.assertEqual(issues[0].message, "id must not be empty")
        self.assertEqual(issues[1].message, "summary must not be empty")

    def test_rejects_end_date_before_start_date(self) -> None:
        issues = validate_event(
            timed_event(
                start_date=date(2026, 7, 11),
                end_date=date(2026, 7, 10),
            )
        )

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].field, "end_date")
        self.assertEqual(issues[0].event_id, "shift-1")

    def test_rejects_end_time_before_start_time_on_same_date(self) -> None:
        issues = validate_event(
            timed_event(start_time=time(20, 0), end_time=time(8, 0))
        )

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].field, "end_time")

    def test_allows_earlier_clock_time_when_event_ends_on_later_date(self) -> None:
        event = timed_event(
            start_date=date(2026, 7, 10),
            start_time=time(20, 0),
            end_date=date(2026, 7, 11),
            end_time=time(8, 0),
        )

        self.assertEqual(validate_event(event), [])

    def test_validate_events_collects_all_issues_with_event_positions(self) -> None:
        events = [timed_event(), timed_event(id="", summary="")]

        issues = validate_events(events)

        self.assertEqual(len(issues), 2)
        self.assertEqual([issue.event_index for issue in issues], [2, 2])

    def test_validate_events_rejects_duplicate_non_empty_ids(self) -> None:
        issues = validate_events([timed_event(), timed_event()])

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].event_index, 2)
        self.assertIn("first used by event 1", issues[0].message)

    def test_prints_each_invalid_event_message_in_bold_red(self) -> None:
        issues = validate_event(timed_event(id="", summary=""))
        output = StringIO()

        print_validation_errors(issues, file=output)

        self.assertEqual(
            output.getvalue(),
            "\033[1;31mInvalid event [id=<empty>]: "
            "id must not be empty\033[0m\n"
            "\033[1;31mInvalid event [id=<empty>]: "
            "summary must not be empty\033[0m\n",
        )

    def test_printed_error_references_event_id(self) -> None:
        output = StringIO()
        issues = validate_event(timed_event(summary=""))

        print_validation_errors(issues, file=output)

        self.assertIn("Invalid event [id=shift-1]", output.getvalue())

    def test_prints_nothing_for_valid_event(self) -> None:
        output = StringIO()

        print_validation_errors(validate_event(timed_event()), file=output)

        self.assertEqual(output.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
