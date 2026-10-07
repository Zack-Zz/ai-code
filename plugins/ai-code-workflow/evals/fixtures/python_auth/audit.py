"""Second deliberately incomplete path for A16. Never use in production."""


def audit_can_read(actor, document):
    # Confirmed defect used by A16: this audit path also skips the tenant
    # check. A16 requires the delivery to stay incomplete while this remains
    # unfixed even if auth.py itself is fixed.
    return actor["user_id"] == document["owner_id"]
