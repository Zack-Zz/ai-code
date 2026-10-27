"""Build events for newly created jobs."""


def make_event(job_id):
    return {"job_id": job_id, "status": "ready"}
