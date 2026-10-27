#!/usr/bin/env python3
"""Replay request steps on independent SQLite connections, without timing races."""

import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

import counter_after
import counter_before
import registry


def replay(database):
    with closing(sqlite3.connect(database)) as first, closing(sqlite3.connect(database)) as second:
        for connection in (first, second):
            connection.execute("PRAGMA foreign_keys = ON")
        first.executescript(Path(__file__).with_name("schema.sql").read_text())
        # Both request preflights finish before either request inserts.
        lookups = [registry.find_registration(connection, "tenant-a", "request-7")
                   for connection in (first, second)]
        ids = [registry.register(first, "tenant-a", "request-7", "first payload"),
               registry.register(second, "tenant-a", "request-7", "second payload")]
        registration = {
            "initial_lookups": lookups, "request_ids": ids,
            "registration_rows": first.execute("SELECT count(*) FROM registrations").fetchone()[0],
            "outbox_rows": first.execute("SELECT count(*) FROM outbox").fetchone()[0],
            "first_payload": first.execute("SELECT payload FROM registrations WHERE id = ?", (ids[0],)).fetchone()[0],
            "other_tenant_id": registry.register(second, "tenant-b", "request-7", "other tenant"),
        }
        # The scheduler pauses each increment after its read, then resumes writes.
        reads = [counter_after.read_value(connection, "accepted") for connection in (first, second)]
        writes = [value + 1 for value in reads]
        for connection, value in zip((first, second), writes):
            counter_after.write_value(connection, "accepted", value)
        after = {"connections": 2, "reads": reads, "writes": writes,
                 "final": first.execute("SELECT value FROM counters WHERE name = 'accepted'").fetchone()[0],
                 "schedule": ["A.read", "B.read", "A.write+commit", "B.write+commit"]}
        with first:
            first.execute("UPDATE counters SET value = 10 WHERE name = 'accepted'")
        for connection in (first, second):
            counter_before.increment(connection, "accepted")
        before = {"connections": 2,
                  "final": first.execute("SELECT value FROM counters WHERE name = 'accepted'").fetchone()[0]}
        return {"registration": registration, "counter_before": before, "counter_after": after}


def main():
    with tempfile.TemporaryDirectory(prefix="codevow-concurrency-") as directory:
        print(json.dumps(replay(Path(directory) / "fixture.sqlite"), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
