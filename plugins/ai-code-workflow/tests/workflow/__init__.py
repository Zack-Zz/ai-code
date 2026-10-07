"""Python unit/integration tests for the ai-code-workflow tools.

Package init makes scripts/ importable so tests can import the workflow
modules directly; the unified gate runs these via unittest discovery.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
