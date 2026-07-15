Input formats
=============

CSV files and XLSX worksheets use the same header:

.. code-block:: text

   id,summary,all_date,start_date,start_time,end_date,end_time,location,description

``id`` and ``summary`` must contain non-whitespace text. IDs must be unique.
``location`` and ``description`` are optional and default to empty strings.

Dates use ``YYYY-MM-DD``. Times use 24-hour ``HH:MM`` or ``HH:MM:SS``.
``true`` and ``false`` are the recommended values for ``all_date``; the reader
also accepts ``yes``/``no``, ``y``/``n``, and ``1``/``0`` without regard to
case.

Timed event
-----------

.. code-block:: text

   meeting-1,Planning,false,2026-07-20,09:30,2026-07-20,10:30,Office,Weekly planning

Timed values are interpreted in ``Europe/Rome`` and written to ICS in UTC.

All-day event
-------------

.. code-block:: text

   holiday-1,Holiday,true,2026-08-15,,2026-08-15,,,

All-day events leave both time fields empty. Their input ``end_date`` is
inclusive, so a one-day event has matching start and end dates.

XLSX notes
----------

The active worksheet is read by default. Native spreadsheet dates, times,
and booleans are accepted, and empty data rows are ignored. Formulas must have
a saved result because workbooks are opened in data-only mode.
