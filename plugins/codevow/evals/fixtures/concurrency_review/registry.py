"""Local registration and durable delivery intent share one SQL transaction."""


def find_registration(connection, tenant_id, request_key):
    row = connection.execute(
        "SELECT id FROM registrations WHERE tenant_id = ? AND request_key = ?",
        (tenant_id, request_key)).fetchone()
    return row[0] if row else None


def register(connection, tenant_id, request_key, payload):
    with connection:
        inserted = connection.execute(
            "INSERT INTO registrations (tenant_id, request_key, payload) VALUES (?, ?, ?) "
            "ON CONFLICT (tenant_id, request_key) DO NOTHING",
            (tenant_id, request_key, payload))
        registration_id = find_registration(connection, tenant_id, request_key)
        if inserted.rowcount == 1:
            connection.execute("INSERT INTO outbox (registration_id) VALUES (?)", (registration_id,))
        return registration_id
