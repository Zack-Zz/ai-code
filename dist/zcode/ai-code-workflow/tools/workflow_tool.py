#!/usr/bin/env python3
"""Single management entry for ai-code-workflow.

Dispatches only the controlled file/validation operations implemented in
scripts/workflow/. Disables bytecode writing before importing its own modules
so packaged copies are not polluted with __pycache__ during normal calls.
"""

import os
import sys

sys.dont_write_bytecode = True

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from workflow.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
