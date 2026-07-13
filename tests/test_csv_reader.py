"""Tests for the normalized events CSV reader."""

from datetime import date, time
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from calendar_conversion import CSVReadError, read_events_csv


HEADER = (
    "id,summary,all_date,start_date,start_time,end_date,end_time,"
    "location,description\n"
)


class CSVReaderTests(unittest.TestCase):
    def test_reads_timed_and_all_day_events(self) -> None:
        source = StringIO(
            HEADER
            + "shift-1,Station shift,false,2026-07-10,08:00,"
            "2026-07-10,20:00,Central station,Day team\n"
            + "training-1,Training day,YES,2026-07-11,,"
            "2026-07-11,,,\n"
        )

        events = read_events_csv(source)

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].start_date, date(2026, 7, 10))
        self.assertEqual(events[0].start_time, time(8, 0))
        self.assertEqual(events[0].location, "Central station")
        self.assertTrue(events[1].all_day)
        self.assertIsNone(events[1].start_time)
        self.assertEqual(events[1].description, "")

    def test_reads_path_and_optional_columns_may_be_absent(self) -> None:
        contents = (
            "id,summary,all_date,start_date,start_time,end_date,end_time\n"
            "shift-1,Station shift,0,2026-07-10,08:00:30,"
            "2026-07-10,20:00:30\n"
        )
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory, "events.csv")
            path.write_text(contents, encoding="utf-8")

            event = read_events_csv(path)[0]

        self.assertEqual(event.location, "")
        self.assertEqual(event.description, "")
        self.assertEqual(event.start_time, time(8, 0, 30))

    def test_accepts_supported_boolean_spellings_case_insensitively(self) -> None:
        for boolean_value in ("true", "TRUE", "yes", "Y", "1"):
            with self.subTest(boolean_value=boolean_value):
                source = StringIO(
                    HEADER
                    + f"event-1,Event,{boolean_value},2026-07-10,,"
                    "2026-07-10,,,\n"
                )
                self.assertTrue(read_events_csv(source)[0].all_day)

        for boolean_value in ("false", "FALSE", "no", "N", "0"):
            with self.subTest(boolean_value=boolean_value):
                source = StringIO(
                    HEADER
                    + f"event-1,Event,{boolean_value},2026-07-10,08:00,"
                    "2026-07-10,09:00,,\n"
                )
                self.assertFalse(read_events_csv(source)[0].all_day)

    def test_rejects_unknown_boolean_with_row_number(self) -> None:
        source = StringIO(
            HEADER
            + "event-1,Event,perhaps,2026-07-10,,2026-07-10,,,\n"
        )

        with self.assertRaisesRegex(CSVReadError, r"row 2: all_date") as raised:
            read_events_csv(source)

        self.assertEqual(raised.exception.row_number, 2)

    def test_rejects_missing_required_columns(self) -> None:
        source = StringIO("id,summary\nevent-1,Event\n")

        with self.assertRaisesRegex(CSVReadError, "missing required column"):
            read_events_csv(source)

    def test_rejects_invalid_date_and_time_formats(self) -> None:
        invalid_rows = (
            (
                "event-1,Event,0,10/07/2026,08:00,2026-07-10,09:00,,\n",
                "start_date must use YYYY-MM-DD",
            ),
            (
                "event-1,Event,0,2026-07-10,8 AM,2026-07-10,09:00,,\n",
                "start_time must use HH:MM",
            ),
        )
        for row, error_message in invalid_rows:
            with self.subTest(row=row):
                with self.assertRaisesRegex(CSVReadError, error_message):
                    read_events_csv(StringIO(HEADER + row))

    def test_rejects_times_for_all_day_event(self) -> None:
        source = StringIO(
            HEADER
            + "event-1,Event,1,2026-07-10,08:00,2026-07-10,09:00,,\n"
        )

        with self.assertRaisesRegex(CSVReadError, "must leave start_time"):
            read_events_csv(source)


if __name__ == "__main__":
    unittest.main()
