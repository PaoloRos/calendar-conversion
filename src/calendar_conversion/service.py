"""Public service for converting uploaded schedule streams into calendars."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from io import BytesIO, StringIO
from pathlib import Path
from typing import BinaryIO

from .csv_reader import CSVReadError, _read_events_csv_with_source_rows
from .event import Event
from .ics_generator import generate_ics
from .validator import IssueCode, validate_events
from .xlsx_reader import XLSXReadError, _read_events_xlsx_with_source_rows


class ConversionErrorCode(StrEnum):
    """Stable codes for fatal input errors raised by ``convert_schedule``."""

    UNSUPPORTED_FILE_TYPE = "unsupported_file_type"
    MALFORMED_CSV = "malformed_csv"
    MALFORMED_XLSX = "malformed_xlsx"
    INPUT_READ_ERROR = "input_read_error"


@dataclass(frozen=True, slots=True)
class SourcePosition:
    """Location of an event in the input schedule."""

    event_index: int
    row: int
    worksheet: str | None = None


@dataclass(frozen=True, slots=True)
class InvalidEvent:
    """An input event skipped because semantic validation failed."""

    source_position: SourcePosition
    id: str
    summary: str
    issue_codes: tuple[IssueCode, ...]


@dataclass(frozen=True, slots=True)
class ConversionResult:
    """Structured outcome of a schedule conversion."""

    ics_text: str
    total_count: int
    converted_count: int
    skipped_count: int
    invalid_events: tuple[InvalidEvent, ...]


class ConversionError(ValueError):
    """Fatal schedule error with a stable code and optional source location."""

    def __init__(
        self,
        code: ConversionErrorCode,
        message: str,
        *,
        row: int | None = None,
        worksheet: str | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.row = row
        self.worksheet = worksheet
        super().__init__(message)


def convert_schedule(
    source: BinaryIO,
    *,
    filename: str,
    calendar_name: str,
) -> ConversionResult:
    """Convert a CSV or XLSX binary stream into a structured result.

    Structurally malformed input raises :class:`ConversionError`. Semantic
    event problems are returned in ``invalid_events`` while valid events are
    included in ``ics_text``.
    """
    suffix = Path(filename).suffix.casefold()
    if suffix not in {".csv", ".xlsx"}:
        raise ConversionError(
            ConversionErrorCode.UNSUPPORTED_FILE_TYPE,
            "input file must use the .csv or .xlsx extension",
        )

    try:
        contents = source.read()
    except (OSError, ValueError) as error:
        raise ConversionError(
            ConversionErrorCode.INPUT_READ_ERROR,
            str(error),
        ) from error

    if not isinstance(contents, bytes):
        raise ConversionError(
            ConversionErrorCode.INPUT_READ_ERROR,
            "source must be an open binary stream",
        )

    if suffix == ".csv":
        events, rows, worksheet = _read_csv(contents)
    elif suffix == ".xlsx":
        events, rows, worksheet = _read_xlsx(contents)
    else:  # pragma: no cover - guarded by the extension check above
        raise AssertionError("unreachable supported extension")

    issues = validate_events(events)
    issue_codes_by_index: dict[int, list[IssueCode]] = {}
    for issue in issues:
        if issue.event_index is not None:
            issue_codes_by_index.setdefault(issue.event_index, []).append(
                issue.code
            )

    valid_events: list[Event] = []
    invalid_events: list[InvalidEvent] = []
    for event_index, (event, row) in enumerate(zip(events, rows), start=1):
        issue_codes = issue_codes_by_index.get(event_index)
        if issue_codes is None:
            valid_events.append(event)
            continue
        invalid_events.append(
            InvalidEvent(
                source_position=SourcePosition(
                    event_index=event_index,
                    row=row,
                    worksheet=worksheet,
                ),
                id=event.id,
                summary=event.summary,
                issue_codes=tuple(issue_codes),
            )
        )

    return ConversionResult(
        ics_text=generate_ics(valid_events, calendar_name=calendar_name),
        total_count=len(events),
        converted_count=len(valid_events),
        skipped_count=len(invalid_events),
        invalid_events=tuple(invalid_events),
    )


def _read_csv(contents: bytes) -> tuple[list[Event], list[int], None]:
    try:
        text = contents.decode("utf-8-sig")
        events, rows = _read_events_csv_with_source_rows(
            StringIO(text, newline="")
        )
    except UnicodeDecodeError as error:
        raise ConversionError(
            ConversionErrorCode.MALFORMED_CSV,
            "CSV input must use UTF-8 encoding",
        ) from error
    except CSVReadError as error:
        raise ConversionError(
            ConversionErrorCode.MALFORMED_CSV,
            error.message,
            row=error.row_number,
        ) from error
    return events, rows, None


def _read_xlsx(contents: bytes) -> tuple[list[Event], list[int], str]:
    try:
        return _read_events_xlsx_with_source_rows(BytesIO(contents))
    except XLSXReadError as error:
        raise ConversionError(
            ConversionErrorCode.MALFORMED_XLSX,
            str(error),
            row=error.row_number,
            worksheet=error.sheet_name,
        ) from error
