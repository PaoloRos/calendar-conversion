"""Command-line application coordinating schedule conversion."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys
from typing import TextIO

from .csv_reader import CSVReadError, read_events_csv
from .event import Event
from .ics_generator import write_ics
from .validator import validate_events
from .xlsx_reader import XLSXReadError, read_events_xlsx


DEFAULT_INPUT_PATH = Path("events.xlsx")
DEFAULT_OUTPUT_PATH = Path("schedule.ics")
BOLD_CYAN = "\033[1;36m"
BOLD_RED = "\033[1;31m"
RESET = "\033[0m"


class ApplicationError(ValueError):
    """A fatal error that prevents schedule conversion."""


def run(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run the command-line conversion and return its process exit code."""
    output = sys.stdout if stdout is None else stdout
    error_output = sys.stderr if stderr is None else stderr
    arguments = _argument_parser().parse_args(argv)

    try:
        events = _read_events(arguments.input)
        issues = validate_events(events)
        invalid_positions = {
            issue.event_index
            for issue in issues
            if issue.event_index is not None
        }
        valid_events = [
            event
            for event_index, event in enumerate(events, start=1)
            if event_index not in invalid_positions
        ]
        write_ics(
            valid_events,
            arguments.output,
            calendar_name="Converted schedule",
        )
    except (ApplicationError, CSVReadError, XLSXReadError, OSError) as error:
        _print_fatal_error(error, error_output)
        return 2

    invalid_events = [
        event
        for event_index, event in enumerate(events, start=1)
        if event_index in invalid_positions
    ]
    _print_report(
        input_path=arguments.input,
        output_path=arguments.output,
        valid_count=len(valid_events),
        invalid_events=invalid_events,
        output=output,
    )
    return 1 if invalid_events else 0


def main() -> int:
    """Run the application with process arguments and standard streams."""
    return run()


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert CSV or XLSX events into an ICS calendar."
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help="events input path (default: events.xlsx)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="ICS output path (default: schedule.ics)",
    )
    return parser


def _read_events(input_path: Path) -> list[Event]:
    suffix = input_path.suffix.casefold()
    if suffix == ".csv":
        return read_events_csv(input_path)
    if suffix == ".xlsx":
        return read_events_xlsx(input_path)
    raise ApplicationError("input file must use the .csv or .xlsx extension")


def _print_report(
    *,
    input_path: Path,
    output_path: Path,
    valid_count: int,
    invalid_events: list[Event],
    output: TextIO,
) -> None:
    use_color = _supports_color(output)
    print(_styled("=== CONVERSION REPORT ===", BOLD_CYAN, use_color), file=output)
    print(f"Input: {input_path}", file=output)
    print(f"Output: {output_path}", file=output)
    print(f"Valid and converted events: {valid_count}", file=output)

    invalid_count_text = (
        f"Invalid and not converted events: {len(invalid_events)}"
    )
    print(_styled(invalid_count_text, BOLD_RED, use_color), file=output)
    if invalid_events:
        print(_styled("Invalid events:", BOLD_RED, use_color), file=output)
        for event in invalid_events:
            event_id = event.id or "<empty>"
            summary = event.summary or "<empty>"
            description = f"  - ID: {event_id} | Summary: {summary}"
            print(_styled(description, BOLD_RED, use_color), file=output)


def _print_fatal_error(error: Exception, output: TextIO) -> None:
    message = f"Conversion failed: {error}"
    print(_styled(message, BOLD_RED, _supports_color(output)), file=output)


def _supports_color(output: TextIO) -> bool:
    return bool(getattr(output, "isatty", lambda: False)())


def _styled(text: str, style: str, use_color: bool) -> str:
    return f"{style}{text}{RESET}" if use_color else text
