"""A04 scenario mutation: simulate the line-3 regression described by the turn.

Applied by evals/prepare.py only inside the one-shot copy for case A04.
"""

import re
from pathlib import Path


def apply(root: Path) -> None:
    labels = root / "labels.py"
    text = labels.read_text(encoding="utf-8")
    broken = re.sub(
        r'return \{0: "idle", 1: "running"\}\.get\(code, "unknown"\)',
        'raise RuntimeError("regression at line 3")',
        text,
        count=1,
    )
    if broken == text:  # pragma: no cover - fixture drifted
        raise SystemExit("A04 mutation target not found in labels.py")
    labels.write_text(broken, encoding="utf-8")
