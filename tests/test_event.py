"""Tests for the internal event model."""

from datetime import date, time
import unittest

from calendar_conversion import Event, ROME_TIMEZONE


class EventTests(unittest.TestCase):
    def test_stores_normalized_event_data(self) -> None:
        event = Event(
            id="shift-2026-07-10",
            summary="Station shift",
            start_date=date(2026, 7, 10),
            start_time=time(8, 0),
            end_date=date(2026, 7, 10),
            end_time=time(20, 0),
            location="Central station",
            description="Day team",
        )

        self.assertEqual(event.id, "shift-2026-07-10")
        self.assertEqual(event.start_date, date(2026, 7, 10))
        self.assertEqual(event.end_time, time(20, 0))
        self.assertFalse(event.all_day)
        self.assertEqual(event.timezone, ROME_TIMEZONE)

    def test_location_and_description_default_to_empty_strings(self) -> None:
        event = Event(
            id="shift-1",
            summary="Station shift",
            start_date=date(2026, 7, 10),
            start_time=time(8, 0),
            end_date=date(2026, 7, 10),
            end_time=time(20, 0),
        )

        self.assertEqual(event.location, "")
        self.assertEqual(event.description, "")

    def test_stores_all_day_event_data(self) -> None:
        event = Event(
            id="training-1",
            summary="Training day",
            all_day=True,
            start_date=date(2026, 7, 10),
            end_date=date(2026, 7, 10),
        )

        self.assertTrue(event.all_day)
        self.assertEqual(event.start_date, date(2026, 7, 10))
        self.assertEqual(event.end_date, event.start_date)
        self.assertIsNone(event.start_time)

    def test_all_day_event_rejects_timed_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "all-day events cannot define"):
            Event(
                id="training-1",
                summary="Training day",
                all_day=True,
                start_date=date(2026, 7, 10),
                end_date=date(2026, 7, 10),
                start_time=time(8, 0),
            )

    def test_event_requires_both_dates(self) -> None:
        with self.assertRaisesRegex(ValueError, "require both start_date"):
            Event(
                id="training-1",
                summary="Training day",
                all_day=True,
                start_date=date(2026, 7, 10),
            )

    def test_timed_event_requires_both_times(self) -> None:
        with self.assertRaisesRegex(ValueError, "timed events require"):
            Event(
                id="shift-1",
                summary="Station shift",
                start_date=date(2026, 7, 10),
                end_date=date(2026, 7, 10),
            )

    def test_event_is_immutable(self) -> None:
        event = Event(
            id="shift-1",
            summary="Station shift",
            start_date=date(2026, 7, 10),
            start_time=time(8, 0),
            end_date=date(2026, 7, 10),
            end_time=time(20, 0),
        )

        with self.assertRaises(AttributeError):
            event.summary = "Changed"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
