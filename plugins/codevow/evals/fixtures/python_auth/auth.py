"""Intentionally incomplete authorization fixture. Never use in production.

Migrated from zcode-workflow/examples/acceptance/auth.py (BEL history):
the tenant check is deliberately missing so acceptance can reproduce and fix
a cross-tenant read as a one-shot scenario.
"""


def can_read(actor, document):
    # Defect: only compares user_id; tenant isolation is not enforced.
    return actor["user_id"] == document["owner_id"]
