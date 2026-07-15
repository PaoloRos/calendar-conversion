Python API
==========

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
   :members: ApplicationError, run, main
