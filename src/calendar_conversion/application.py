"""Command-line application coordinating schedule conversion."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys
from typing import TextIO

from .service import (
    ConversionError,
    ConversionErrorCode,
    InvalidEvent,
    convert_schedule,
)


DEFAULT_INPUT_PATH = Path("events.xlsx")
DEFAULT_OUTPUT_PATH = Path("schedule.ics")
BOLD_CYAN = "\033[1;36m"
BOLD_RED = "\033[1;31m"
RESET = "\033[0m"


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
        if arguments.input.suffix.casefold() not in {".csv", ".xlsx"}:
            raise ConversionError(
                code=ConversionErrorCode.UNSUPPORTED_FILE_TYPE,
                message="input file must use the .csv or .xlsx extension",
            )
        with arguments.input.open("rb") as input_file:
            result = convert_schedule(
                input_file,
                filename=arguments.input.name,
                calendar_name="Converted schedule",
            )
        arguments.output.write_text(
            result.ics_text,
            encoding="utf-8",
            newline="",
        )
    except (ConversionError, OSError) as error:
        _print_fatal_error(error, error_output)
        return 2

    _print_report(
        input_path=arguments.input,
        output_path=arguments.output,
        valid_count=result.converted_count,
        invalid_events=list(result.invalid_events),
        output=output,
    )
    return 1 if result.invalid_events else 0


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


def _print_report(
    *,
    input_path: Path,
    output_path: Path,
    valid_count: int,
    invalid_events: list[InvalidEvent],
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
