"""Disposable acceptance fixture, not business code.

Migrated from zcode-workflow/examples/acceptance/labels.py (BEL history);
kept byte-equivalent in intent as the one-shot v1 fixture.
"""


def label(code):
    return {0: "idle", 1: "running"}.get(code, "unknown")
