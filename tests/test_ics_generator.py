"""Tests for iCalendar generation."""

from datetime import date, datetime, time, timezone
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from calendar_conversion import (
    Event,
    ICSGenerationError,
    generate_ics,
    write_ics,
)


GENERATED_AT = datetime(2026, 7, 13, 10, 30, tzinfo=timezone.utc)


def timed_event(**overrides: object) -> Event:
    values = {
        "id": "shift-1",
        "summary": "Station shift",
        "start_date": date(2026, 7, 15),
        "start_time": time(8, 0),
        "end_date": date(2026, 7, 15),
        "end_time": time(14, 0),
        "location": "Central station",
        "description": "Morning team",
    }
    values.update(overrides)
    return Event(**values)  # type: ignore[arg-type]


class ICSGeneratorTests(unittest.TestCase):
    def test_puts_multiple_events_in_one_calendar(self) -> None:
        events = [
            timed_event(),
            Event(
                id="training-1",
                summary="Training",
                all_day=True,
                start_date=date(2026, 7, 18),
                end_date=date(2026, 7, 18),
            ),
        ]

        calendar = generate_ics(events, generated_at=GENERATED_AT)

        self.assertTrue(calendar.startswith("BEGIN:VCALENDAR\r\n"))
        self.assertTrue(calendar.endswith("END:VCALENDAR\r\n"))
        self.assertEqual(calendar.count("BEGIN:VEVENT"), 2)
        self.assertEqual(calendar.count("END:VEVENT"), 2)

    def test_converts_rome_times_to_utc(self) -> None:
        calendar = generate_ics([timed_event()], generated_at=GENERATED_AT)

        # Rome observes UTC+2 in July.
        self.assertIn("DTSTART:20260715T060000Z\r\n", calendar)
        self.assertIn("DTEND:20260715T120000Z\r\n", calendar)
        self.assertIn("DTSTAMP:20260713T103000Z\r\n", calendar)

    def test_all_day_end_date_becomes_exclusive(self) -> None:
        event = Event(
            id="conference-1",
            summary="Conference",
            all_day=True,
            start_date=date(2026, 7, 25),
            end_date=date(2026, 7, 26),
        )

        calendar = generate_ics([event], generated_at=GENERATED_AT)

        self.assertIn("DTSTART;VALUE=DATE:20260725\r\n", calendar)
        self.assertIn("DTEND;VALUE=DATE:20260727\r\n", calendar)

    def test_escapes_text_and_omits_empty_optional_fields(self) -> None:
        event = timed_event(
            summary="Alarm, drill; phase 1",
            location="",
            description="First line\nSecond \\ line",
        )

        calendar = generate_ics([event], generated_at=GENERATED_AT)

        self.assertIn("SUMMARY:Alarm\\, drill\\; phase 1\r\n", calendar)
        self.assertIn("DESCRIPTION:First line\\nSecond \\\\ line\r\n", calendar)
        self.assertNotIn("LOCATION:", calendar)

    def test_adds_optional_calendar_name(self) -> None:
        calendar = generate_ics(
            [timed_event()],
            calendar_name="Brigade calendar",
            generated_at=GENERATED_AT,
        )

        self.assertIn("X-WR-CALNAME:Brigade calendar\r\n", calendar)

    def test_rejects_invalid_events_before_generation(self) -> None:
        event = timed_event(summary="")

        with self.assertRaises(ICSGenerationError) as raised:
            generate_ics([event], generated_at=GENERATED_AT)

        self.assertEqual(raised.exception.issues[0].event_id, "shift-1")

    def test_rejects_duplicate_event_ids(self) -> None:
        events = [timed_event(), timed_event(summary="Another shift")]

        with self.assertRaises(ICSGenerationError) as raised:
            generate_ics(events, generated_at=GENERATED_AT)

        self.assertIn("must be unique", raised.exception.issues[0].message)

    def test_folds_long_utf8_content_lines_to_75_octets(self) -> None:
        calendar = generate_ics(
            [timed_event(summary="Firefighter 🚒 " * 12)],
            generated_at=GENERATED_AT,
        )

        for line in calendar.split("\r\n"):
            self.assertLessEqual(len(line.encode("utf-8")), 75)

    def test_writes_to_path_and_text_stream(self) -> None:
        stream = StringIO()
        write_ics([timed_event()], stream, generated_at=GENERATED_AT)
        self.assertIn("BEGIN:VCALENDAR", stream.getvalue())

        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory, "calendar.ics")
            write_ics([timed_event()], path, generated_at=GENERATED_AT)
            contents = path.read_text(encoding="utf-8")

        self.assertIn("UID:shift-1", contents)

    def test_rejects_naive_generation_timestamp(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone information"):
            generate_ics(
                [timed_event()],
                generated_at=datetime(2026, 7, 13, 10, 30),
            )


if __name__ == "__main__":
    unittest.main()
