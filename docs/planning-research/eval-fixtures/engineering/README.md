# Customer reports service

The service currently creates reports from requested jobs. The HTTP layer is
not included in this fixture. A job worker calls `render_report`, stores the
result, and marks the job complete. Production persistence is out of scope of
this sample; the in-memory store demonstrates the existing interface.

Older architecture notes proposed a second queue for deduplicated exports.
Use the source and tests to determine the behavior currently available.

Run the fixture tests with `python3 -m unittest -v` from this directory.
