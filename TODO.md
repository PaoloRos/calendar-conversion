# To do list (will be updated at every new task)

**General instructions**:

- If something is unclear, aks me for clarification!
- Whenever you have some suggestions, tell them to me!
- When implemented my instructions, mark them in green and bold as "Status: implemented".

## Programming language

I'll use Python as programming language. 

🟢 **Status: implemented**

## Internal Event Model

Let's start by defining the event model. Write the first definition of a **class** containing the following attributes of the event:

- `id`
- `summary`
- `start_date`
- `start_time`
- `end_date`
- `end_time`
- `location`
- `description`

If you think that there's more, tell it to me.

🟢 **Status: implemented**

Implemented in `src/calendar_conversion/event.py`, with automated tests.

Add to the class the support for the timezone and all-day-event:

- timezone: Europe/Rome
- all-day-event: must be guided by a flag:

```
if(all-day-event) 
  then { set(start_date) and set(end_date); do not set times }
else 
  { set dates and times }
```

For a one-day all-day event, `end_date` is equal to `start_date`.

🟢 **Status: implemented**

Both event types use `start_date` and `end_date`.
`all_day` determines whether the time fields must be omitted or supplied.
Timed events use `Europe/Rome` through Python's timezone-aware `zoneinfo`
support. The Python model uses lowercase `snake_case` attributes; readers and
generators will map external uppercase names at the format boundary.

## CSV Reader

Now implement the CSV reader. According to the event model, the file in this format will be as follows:

```
id,summary,all_date,start_date,start_time,end_date,end_time,location,description
...
```

Annotations:

- location and description can be missing, since they're are set by default as empty strings
- the `all_date` field is a boolean variable: therefore, it could be 0/1, true/false, yes/no, etc... Consider that events will be programmed by humans, so tell me which is the best choice/choices about these boolean values.

I would suggest to create a new source file for the reader, but if you think differently, let me that know!

🟢 **Status: implemented**

Implemented in `src/calendar_conversion/csv_reader.py`, with automated tests.
The reader accepts CSV paths and text streams, uses ISO
`YYYY-MM-DD` dates and 24-hour `HH:MM` or `HH:MM:SS` times, and reports input
errors with their source row number. `location` and `description` columns are
optional and default to empty strings.

For human-entered booleans, `true`/`false` is the recommended canonical form
because it is immediately understandable. The reader also accepts `yes`/`no`,
`y`/`n`, and `1`/`0`, case-insensitively, to make hand-written and
spreadsheet-exported input convenient without treating ambiguous values as
booleans.

## Validator

Now implement the validator code. It's required to check:

- whether the temporal order is correct (ie: it shouldn't be possible that the start_date is after the end_date)
- whether the `ID` and `SUMMARY` field are empty (or maybe it's better to implement this feature already in the reader? Tell me what do you think!)

I reckon that the Validator is a part of the Event code, so I suggest to implement it in the same file, but if you think differently, tell it to me!

🟢 **Status: implemented**

The validator is implemented in its own `validator.py` module because semantic
validation is a separate responsibility from storing an immutable event. It
collects all problems instead of stopping at the first one. Empty or
whitespace-only `id` and `summary` values are checked here rather than in the
reader, so every future input format receives the same validation behavior.
Temporal validation rejects reversed dates and, for same-day timed events,
reversed times. Invalid-event descriptions can be printed in bold red as
`Invalid event [id=event-id]: description` using `print_validation_errors`,
so every reported problem can be traced to its originating event.

## ICS Generator

Now implement the code for the generator. I let you the freedom of all implementation. The only design choice is that the generator allows to collect all the events in one box (such as a compressed .zip file?), if you agree that this would be a good thing.

🟢 **Status: implemented**

Implemented in `src/calendar_conversion/ics_generator.py`, with automated
tests. A single `.ics` file already acts as a standard container for multiple
events, so no ZIP archive is necessary. Avoiding ZIP makes the generated file
directly importable into Apple Calendar, Google Calendar, and other calendar
applications.

The generator validates every event before writing, creates one `VEVENT` per
event inside one `VCALENDAR`, converts timed events from their `Europe/Rome`
timezone to UTC, and converts inclusive all-day end dates to the exclusive
`DTEND` required by iCalendar. It also escapes text, folds long content lines,
and writes the CRLF line endings required by the format.

## XLSX Reader

Implement the reader for .xlsx. Since a .csv reader is already implemented and since the .xlsx files are written by humans in an affordable file (ie: id, summary,...[different rows]), I would suggest to build the code to covert a .xlsx into a .csv, and then the CSV Reader could be called. Is it good idea, in terms of reliability and performance?

🟢 **Status: implemented**

Implemented in `src/calendar_conversion/xlsx_reader.py`, with automated tests.
The reader uses the active worksheet by default or a named worksheet when
requested. It accepts the same columns and values as the CSV reader, while
also understanding native Excel dates, times, and booleans. Completely empty
data rows are ignored, and errors identify their worksheet and original row.

The proposed conversion is reliable and fast for human-sized schedules when
performed in memory: the XLSX reader normalizes spreadsheet values to CSV text
and delegates parsing to the existing CSV reader, so both formats share the
same input rules without creating a temporary file. `openpyxl` is used for
XLSX decoding because the Python standard library does not implement that
file format.
