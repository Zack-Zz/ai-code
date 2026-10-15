"""Format job events for display."""


def render_event(event):
    return f"{event['job_id']}: {event['state']}"
