Getting started
===============

Requirements
------------

The application requires Python 3.11 or newer. ``openpyxl`` is the only
third-party runtime package and provides XLSX support.

Create an isolated environment and install the project:

.. code-block:: console

   $ python3 -m venv .venv
   $ source .venv/bin/activate
   $ python -m pip install --upgrade pip
   $ python -m pip install -e .

Run a conversion
----------------

With no arguments, the application reads ``events.xlsx`` and writes
``schedule.ics``:

.. code-block:: console

   $ python main.py

Select another CSV or XLSX file, or change the output path:

.. code-block:: console

   $ python main.py another_name.csv
   $ python main.py another_name.xlsx --output another_schedule.ics

Use ``python main.py --help`` for the command summary.

Call from Python
----------------

Use ``calendar_conversion.convert_schedule`` to integrate the conversion
pipeline into a Python application. Pass an open binary stream plus its
original filename and the calendar name. The returned result contains ICS
text, counts, and structured invalid-event details. See :doc:`api` for the
complete contract and error types.

Save the report
---------------

The report is written to standard output. Redirecting it produces clean text
without terminal color codes:

.. code-block:: console

   $ python main.py events.xlsx > report.txt

Use ``>>`` instead of ``>`` to append. Exit status 0 means complete success,
1 means invalid events were skipped, and 2 means a fatal read or write error.

Build this documentation
------------------------

Sphinx is needed only by documentation authors:

.. code-block:: console

   $ python -m pip install -e '.[docs]'
   $ python -m sphinx -b html docs-source docs

Then open ``docs/index.html`` in a browser. The same committed HTML is served
by GitHub Pages when the repository's Pages source is set to ``/docs``.
