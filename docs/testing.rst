Testing
=======

Automated unit tests cover the event model, both readers, validation, ICS
generation, and command-line coordination. Run the complete suite from the
project root:

.. code-block:: console

   $ PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v

Visual checks complement the automated suite: inspect the terminal report,
the redirected plain-text report, and an imported ``.ics`` calendar. These
checks confirm presentation and application interoperability that unit tests
cannot fully demonstrate.
