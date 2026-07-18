"""Tests for the public structured conversion service."""

from io import BytesIO
import unittest

from openpyxl import Workbook

from calendar_conversion import (
    ConversionError,
    ConversionErrorCode,
    IssueCode,
    convert_schedule,
)


CSV_HEADER = (
    "id,summary,all_date,start_date,start_time,end_date,end_time,"
    "location,description\n"
)


class ConversionServiceTests(unittest.TestCase):
    def test_converts_valid_csv_to_a_structured_result(self) -> None:
        contents = (
            CSV_HEADER
            + "event-1,Übung,false,2026-07-18,08:00,"
            "2026-07-18,09:00,,\n"
        ).encode()

        result = convert_schedule(
            BytesIO(contents),
            filename="schedule.CSV",
            calendar_name="Feuerwehr",
        )

        self.assertEqual(result.total_count, 1)
        self.assertEqual(result.converted_count, 1)
        self.assertEqual(result.skipped_count, 0)
        self.assertEqual(result.invalid_events, ())
        self.assertIn("X-WR-CALNAME:Feuerwehr", result.ics_text)
        self.assertIn("SUMMARY:Übung", result.ics_text)

    def test_returns_each_invalid_event_once_with_stable_issue_codes(self) -> None:
        contents = (
            CSV_HEADER
            + "event-1,Valid,true,2026-07-18,,2026-07-18,,,\n"
            + ",,false,2026-07-19,10:00,2026-07-19,09:00,,\n"
        ).encode()

        result = convert_schedule(
            BytesIO(contents),
            filename="schedule.csv",
            calendar_name="Calendar",
        )

        self.assertEqual(result.total_count, 2)
        self.assertEqual(result.converted_count, 1)
        self.assertEqual(result.skipped_count, 1)
        invalid = result.invalid_events[0]
        self.assertEqual(invalid.source_position.event_index, 2)
        self.assertEqual(invalid.source_position.row, 3)
        self.assertIsNone(invalid.source_position.worksheet)
        self.assertEqual(
            invalid.issue_codes,
            (
                IssueCode.EMPTY_ID,
                IssueCode.EMPTY_SUMMARY,
                IssueCode.END_TIME_BEFORE_START_TIME,
            ),
        )
        self.assertIn("UID:event-1", result.ics_text)

    def test_reports_duplicate_id_as_an_invalid_later_event(self) -> None:
        rows = (
            "same,First,true,2026-07-18,,2026-07-18,,,\n"
            "same,Second,true,2026-07-19,,2026-07-19,,,\n"
        )

        result = convert_schedule(
            BytesIO((CSV_HEADER + rows).encode()),
            filename="schedule.csv",
            calendar_name="Calendar",
        )

        self.assertEqual(result.converted_count, 1)
        self.assertEqual(
            result.invalid_events[0].issue_codes,
            (IssueCode.DUPLICATE_ID,),
        )

    def test_retains_physical_csv_row_after_an_empty_line(self) -> None:
        contents = (
            CSV_HEADER
            + "\n"
            + "event-1,,true,2026-07-18,,2026-07-18,,,\n"
        ).encode()

        result = convert_schedule(
            BytesIO(contents),
            filename="schedule.csv",
            calendar_name="Calendar",
        )

        self.assertEqual(result.invalid_events[0].source_position.row, 3)

    def test_retains_xlsx_worksheet_and_original_row_after_empty_rows(self) -> None:
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Turni"
        worksheet.append(CSV_HEADER.strip().split(","))
        worksheet.append([None] * 9)
        worksheet.append(
            ["event-1", "", True, "2026-07-18", None, "2026-07-18"]
        )
        source = BytesIO()
        workbook.save(source)
        workbook.close()
        source.seek(0)

        result = convert_schedule(
            source,
            filename="schedule.xlsx",
            calendar_name="Calendar",
        )

        position = result.invalid_events[0].source_position
        self.assertEqual(position.event_index, 1)
        self.assertEqual(position.row, 3)
        self.assertEqual(position.worksheet, "Turni")
        self.assertEqual(result.converted_count, 0)
        self.assertIn("BEGIN:VCALENDAR", result.ics_text)

    def test_exposes_stable_fatal_codes_and_locations(self) -> None:
        malformed = (CSV_HEADER + "event-1,Too,few\n").encode()

        with self.assertRaises(ConversionError) as raised:
            convert_schedule(
                BytesIO(malformed),
                filename="schedule.csv",
                calendar_name="Calendar",
            )

        self.assertEqual(raised.exception.code, ConversionErrorCode.MALFORMED_CSV)
        self.assertEqual(raised.exception.row, 2)
        self.assertIsNone(raised.exception.worksheet)

    def test_exposes_worksheet_for_fatal_xlsx_error(self) -> None:
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Schedule"
        worksheet.append(["id", "summary"])
        source = BytesIO()
        workbook.save(source)
        workbook.close()
        source.seek(0)

        with self.assertRaises(ConversionError) as raised:
            convert_schedule(
                source,
                filename="schedule.xlsx",
                calendar_name="Calendar",
            )

        self.assertEqual(
            raised.exception.code,
            ConversionErrorCode.MALFORMED_XLSX,
        )
        self.assertEqual(raised.exception.worksheet, "Schedule")

    def test_rejects_unsupported_extension_before_reading_source(self) -> None:
        class UnreadableSource(BytesIO):
            def read(self, size: int = -1) -> bytes:
                raise AssertionError("source should not be read")

        with self.assertRaises(ConversionError) as raised:
            convert_schedule(
                UnreadableSource(),
                filename="schedule.txt",
                calendar_name="Calendar",
            )

        self.assertEqual(
            raised.exception.code,
            ConversionErrorCode.UNSUPPORTED_FILE_TYPE,
        )


if __name__ == "__main__":
    unittest.main()
