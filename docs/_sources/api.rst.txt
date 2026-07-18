Python API reference
====================

Structured conversion service
-----------------------------

Use this API when integrating the converter into another Python application.
It accepts an open binary stream and returns calendar text and structured
validation details without creating temporary files.

.. code-block:: python

   from calendar_conversion import ConversionError, convert_schedule

   with open("events.xlsx", "rb") as source:
       try:
           result = convert_schedule(
               source,
               filename="events.xlsx",
               calendar_name="Fire brigade schedule",
           )
       except ConversionError as error:
           print(error.code, error.row, error.worksheet)
       else:
           print(result.converted_count, result.skipped_count)

``ConversionResult`` and its nested objects are immutable. Stable enum values
in ``IssueCode`` and ``ConversionErrorCode`` are intended for application
logic and translation; diagnostic messages are intended for developers.

.. automodule:: calendar_conversion.service
   :members: convert_schedule, ConversionResult, InvalidEvent, SourcePosition, IssueCode, ConversionError, ConversionErrorCode
   :show-inheritance:

Event model
-----------

.. automodule:: calendar_conversion.event
   :members:
   :show-inheritance:

Readers
-------

.. automodule:: calendar_conversion.csv_reader
   :members: CSVReadError, read_events_csv

.. automodule:: calendar_conversion.xlsx_reader
   :members: XLSXReadError, read_events_xlsx

Validation
----------

.. automodule:: calendar_conversion.validator
   :members: ValidationIssue, validate_event, validate_events, print_validation_errors

ICS generation
--------------

.. automodule:: calendar_conversion.ics_generator
   :members: ICSGenerationError, generate_ics, write_ics

Application
-----------

.. automodule:: calendar_conversion.application
   :members: run, main
