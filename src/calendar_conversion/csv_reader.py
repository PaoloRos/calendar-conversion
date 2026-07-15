"""Read normalized calendar events from CSV files."""

from __future__ import annotations

import csv
from collections.abc import Iterator
from datetime import date, datetime, time
from os import PathLike
from pathlib import Path
from typing import TextIO

from .event import Event


REQUIRED_COLUMNS = frozenset(
    {
        "id",
        "summary",
        "all_date",
        "start_date",
        "start_time",
        "end_date",
        "end_time",
    }
)
TRUE_VALUES = frozenset({"1", "true", "yes", "y"})
FALSE_VALUES = frozenset({"0", "false", "no", "n"})


class CSVReadError(ValueError):
    """An error in the structure or contents of an events CSV file."""

    def __init__(self, message: str, *, row_number: int | None = None) -> None:
        self.message = message
        self.row_number = row_number
        prefix = f"row {row_number}: " if row_number is not None else ""
        super().__init__(prefix + message)


def read_events_csv(source: str | PathLike[str] | TextIO) -> list[Event]:
    """Read events from a path or an open text stream.

    Dates must use ISO ``YYYY-MM-DD`` format. Times accept ``HH:MM`` or
    ``HH:MM:SS``. Boolean values are case-insensitive and may be represented
    by true/false, yes/no, y/n, or 1/0.
    """
    if hasattr(source, "read"):
        return list(_read_events(source))  # type: ignore[arg-type]

    path = Path(source)
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        return list(_read_events(csv_file))


def _read_events(csv_file: TextIO) -> Iterator[Event]:
    reader = csv.DictReader(csv_file)
    if reader.fieldnames is None:
        raise CSVReadError("CSV file must contain a header row")

    # A UTF-8 byte-order mark is harmless and common in spreadsheet exports.
    reader.fieldnames[0] = reader.fieldnames[0].lstrip("\ufeff")
    fieldnames = [name.strip() for name in reader.fieldnames]
    reader.fieldnames = fieldnames

    duplicate_columns = sorted(
        {name for name in fieldnames if fieldnames.count(name) > 1}
    )
    if duplicate_columns:
        raise CSVReadError(
            "duplicate column(s): " + ", ".join(duplicate_columns)
        )

    missing_columns = sorted(REQUIRED_COLUMNS.difference(fieldnames))
    if missing_columns:
        raise CSVReadError(
            "missing required column(s): " + ", ".join(missing_columns)
        )

    for row_number, row in enumerate(reader, start=2):
        if None in row:
            raise CSVReadError(
                "contains more values than the header defines",
                row_number=row_number,
            )

        yield _event_from_row(row, row_number)


def _event_from_row(row: dict[str, str | None], row_number: int) -> Event:
    def value(column: str) -> str:
        raw_value = row.get(column)
        return "" if raw_value is None else raw_value.strip()

    all_day = _parse_boolean(value("all_date"), row_number)
    start_date = _parse_date(value("start_date"), "start_date", row_number)
    end_date = _parse_date(value("end_date"), "end_date", row_number)

    start_time_text = value("start_time")
    end_time_text = value("end_time")
    if all_day:
        if start_time_text or end_time_text:
            raise CSVReadError(
                "all-day events must leave start_time and end_time empty",
                row_number=row_number,
            )
        start_time = None
        end_time = None
    else:
        start_time = _parse_time(start_time_text, "start_time", row_number)
        end_time = _parse_time(end_time_text, "end_time", row_number)

    try:
        return Event(
            id=value("id"),
            summary=value("summary"),
            all_day=all_day,
            start_date=start_date,
            start_time=start_time,
            end_date=end_date,
            end_time=end_time,
            location=value("location"),
            description=value("description"),
        )
    except ValueError as error:
        raise CSVReadError(str(error), row_number=row_number) from error


def _parse_boolean(value: str, row_number: int) -> bool:
    normalized_value = value.casefold()
    if normalized_value in TRUE_VALUES:
        return True
    if normalized_value in FALSE_VALUES:
        return False
    raise CSVReadError(
        "all_date must be one of true/false, yes/no, y/n, or 1/0",
        row_number=row_number,
    )


def _parse_date(value: str, column: str, row_number: int) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise CSVReadError(
            f"{column} must use YYYY-MM-DD format",
            row_number=row_number,
        ) from error


def _parse_time(value: str, column: str, row_number: int) -> time:
    for time_format in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value, time_format).time()
        except ValueError:
            pass

    raise CSVReadError(
        f"{column} must use HH:MM or HH:MM:SS format",
        row_number=row_number,
    )
