# Calendar Conversion Application

Convert a human-authored XLSX or CSV schedule into one standard iCalendar
(`.ics`) file. The application validates each event, converts the valid ones,
skips invalid entries, and prints a conversion report.

See the [full documentation](docs/_build/html/index.html) for input rules, architecture, API
details, testing, and the AI-assisted development workflow.

## Why this project exists

The idea came from a practical need in my firefighter brigade: importing the
organization's human-written schedule into personal calendar applications. A
future upgrade may provide a UI where colleagues can download a calendar based
on their role in the brigade.

## Requirements and setup

- Python 3.11 or newer
- `openpyxl` for XLSX support, installed with the project

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Use the application

By default, the program reads `events.xlsx` and writes `schedule.ics`:

```bash
python main.py
```

Choose another input or output file when needed:

```bash
python main.py events.csv
python main.py another_schedule.xlsx --output calendar.ics
python main.py events.xlsx > report.txt
```

The input header is:

```text
id,summary,all_date,start_date,start_time,end_date,end_time,location,description
```

Use ISO dates (`YYYY-MM-DD`), 24-hour times (`HH:MM` or `HH:MM:SS`),
and preferably `true` or `false` for `all_date`. All-day events must leave both
time fields empty. See the included `events.csv` and `events.xlsx` examples.

Exit status `0` means complete success, `1` means invalid events were skipped,
and `2` means a fatal read or write error.

## Architecture

![Conversion workflow](docs/_static/architecture-v4.svg)

XLSX rows are normalized in memory and delegated to the CSV reader. Both input
formats therefore share the same event model and validation rules before the
ICS generator produces one importable calendar file.

## Tests and documentation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v
python -m pip install -e '.[docs]'
python -m sphinx -b html docs docs/_build/html
```

Open `docs/_build/html/index.html` after building the documentation.

## AI usage

**OpenAI Codex GPT 5.6 Sol** assisted with brainstorming, implementation, and
automated tests. The project owner supplied the requirements and decisions in
`TODO.md`, recorded the agreed choices in `IMPLEMENTATION_DECISIONS.md`, and
verified the program's behavior.

## Author

Developed by [Paolo Rossi](https://github.com/PaoloRos).
