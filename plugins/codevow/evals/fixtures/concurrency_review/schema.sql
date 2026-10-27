PRAGMA foreign_keys = ON;
CREATE TABLE registrations (
    id INTEGER PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    request_key TEXT NOT NULL,
    payload TEXT NOT NULL,
    UNIQUE (tenant_id, request_key)
);
CREATE TABLE outbox (
    registration_id INTEGER PRIMARY KEY REFERENCES registrations(id),
    state TEXT NOT NULL DEFAULT 'pending' CHECK (state IN ('pending', 'delivered'))
);
CREATE TABLE counters (
    name TEXT PRIMARY KEY,
    value INTEGER NOT NULL
);
INSERT INTO counters (name, value) VALUES ('accepted', 10);
