"""Each accepted request adds one to a shared persistent counter."""


def increment(connection, name):
    with connection:
        connection.execute("UPDATE counters SET value = value + 1 WHERE name = ?", (name,))
