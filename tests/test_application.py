"""Tests for the calendar conversion command-line application."""

from contextlib import chdir
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from openpyxl import Workbook

from calendar_conversion.application import run


CSV_HEADER = (
    "id,summary,all_date,start_date,start_time,end_date,end_time,"
    "location,description\n"
)


class TerminalOutput(StringIO):
    def isatty(self) -> bool:
        return True


class ApplicationTests(unittest.TestCase):
    def test_converts_valid_events_and_reports_invalid_events_once(self) -> None:
        contents = (
            CSV_HEADER
            + "valid-1,Valid event,false,2026-07-15,08:00,"
            "2026-07-15,09:00,,\n"
            + "invalid-1,,false,2026-07-16,18:00,"
            "2026-07-16,08:00,,Two validation issues\n"
        )
        with TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory, "events.csv")
            output_path = Path(temporary_directory, "calendar.ics")
            input_path.write_text(contents, encoding="utf-8")
            report = StringIO()

            exit_code = run(
                [str(input_path), "--output", str(output_path)],
                stdout=report,
            )
            calendar = output_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 1)
        self.assertIn("Valid and converted events: 1", report.getvalue())
        self.assertIn("Invalid and not converted events: 1", report.getvalue())
        self.assertEqual(report.getvalue().count("ID: invalid-1"), 1)
        self.assertIn("Summary: <empty>", report.getvalue())
        self.assertNotIn("\033[", report.getvalue())
        self.assertIn("UID:valid-1", calendar)
        self.assertNotIn("UID:invalid-1", calendar)

    def test_uses_default_xlsx_input_and_ics_output_paths(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            workbook = Workbook()
            worksheet = workbook.active
            worksheet.append(
                [
                    "id",
                    "summary",
                    "all_date",
                    "start_date",
                    "start_time",
                    "end_date",
                    "end_time",
                ]
            )
            worksheet.append(
                [
                    "event-1",
                    "Event",
                    True,
                    "2026-07-15",
                    None,
                    "2026-07-15",
                    None,
                ]
            )
            workbook.save(directory / "events.xlsx")
            workbook.close()

            with chdir(directory):
                exit_code = run([], stdout=StringIO())

            calendar = (directory / "schedule.ics").read_text(
                encoding="utf-8"
            )

        self.assertEqual(exit_code, 0)
        self.assertIn("UID:event-1", calendar)

    def test_colors_invalid_report_when_stdout_is_a_terminal(self) -> None:
        contents = (
            CSV_HEADER
            + "event-1,,true,2026-07-15,,2026-07-15,,,\n"
        )
        with TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory, "events.csv")
            output_path = Path(temporary_directory, "schedule.ics")
            input_path.write_text(contents, encoding="utf-8")
            report = TerminalOutput()

            exit_code = run(
                [str(input_path), "-o", str(output_path)],
                stdout=report,
            )

        self.assertEqual(exit_code, 1)
        self.assertIn(
            "\033[1;31mInvalid and not converted events: 1",
            report.getvalue(),
        )
        self.assertIn(
            "\033[1;31m  - ID: event-1 | Summary: <empty>",
            report.getvalue(),
        )

    def test_rejects_unsupported_input_extension_without_output(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory, "schedule.ics")
            errors = StringIO()

            exit_code = run(
                ["events.txt", "-o", str(output_path)],
                stdout=StringIO(),
                stderr=errors,
            )

            self.assertFalse(output_path.exists())

        self.assertEqual(exit_code, 2)
        self.assertIn("must use the .csv or .xlsx extension", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
