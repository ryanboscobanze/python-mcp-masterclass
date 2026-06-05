"""sqlite3 basics — prerequisite for the MCP lifespan/sqlite module.

The lifespan/sqlite example manages a real SQLite database via the server
lifespan hook.  This file covers everything you need to read that code:

  - Connecting (in-memory and file-based)
  - Creating tables and inserting rows
  - Querying with execute() and executescript()
  - Reading results: fetchall(), fetchone(), sqlite3.Row
  - Error handling: sqlite3.Error
  - Closing the connection

Run this file directly to see every section in action:
    python 05_sqlite3_basics.py
"""

import sqlite3


# ── 1. Connect ────────────────────────────────────────────────────────────────
# ":memory:" creates a private, temporary database in RAM.
# Replace with a file path (e.g. "data.db") for a persistent database.

conn = sqlite3.connect(":memory:")
print("Connected:", conn)


# ── 2. Create a table and insert rows ─────────────────────────────────────────
# executescript() runs multiple SQL statements separated by semicolons.
# It is the fastest way to set up a schema and seed data in one call.

conn.executescript("""
    CREATE TABLE users (
        id    INTEGER PRIMARY KEY,
        name  TEXT    NOT NULL,
        email TEXT    NOT NULL,
        role  TEXT    NOT NULL
    );

    INSERT INTO users (name, email, role) VALUES
        ('Alice',   'alice@example.com',   'admin'),
        ('Bob',     'bob@example.com',     'developer'),
        ('Charlie', 'charlie@example.com', 'designer');
""")
conn.commit()   # make the changes permanent (important for file-based DBs)
print("\nTable created and seeded.")


# ── 3. Query — fetchall() returns a list of tuples by default ─────────────────

cursor = conn.execute("SELECT id, name, role FROM users")
rows = cursor.fetchall()

print("\nAll users (raw tuples):")
for row in rows:
    print(" ", row)          # (1, 'Alice', 'admin')
    print("  id  :", row[0]) # access by index
    print("  name:", row[1])


# ── 4. sqlite3.Row — access columns by name ───────────────────────────────────
# Setting row_factory lets you use row["column_name"] instead of row[0].
# The lifespan/sqlite server sets this on every new connection.

conn.row_factory = sqlite3.Row

cursor = conn.execute("SELECT * FROM users WHERE role = 'developer'")
rows = cursor.fetchall()

print("\nDevelopers (sqlite3.Row — column access by name):")
for row in rows:
    print(f"  {row['name']} <{row['email']}>")

# sqlite3.Row also supports dict() conversion, which is what the server does:
first = conn.execute("SELECT * FROM users LIMIT 1").fetchone()
print("\nFirst user as dict:", dict(first))


# ── 5. fetchone() — read a single row ─────────────────────────────────────────

row = conn.execute("SELECT COUNT(*) AS total FROM users").fetchone()
print(f"\nTotal users: {row['total']}")


# ── 6. Parameterised queries — prevent SQL injection ──────────────────────────
# Always use ? placeholders instead of string formatting.

role = "admin"
row = conn.execute("SELECT name FROM users WHERE role = ?", (role,)).fetchone()
print(f"\nFirst admin: {row['name']}")


# ── 7. Error handling — sqlite3.Error ─────────────────────────────────────────
# The lifespan/sqlite server catches this to return a safe error message
# instead of crashing the tool call.

try:
    conn.execute("SELECT * FROM nonexistent_table")
except sqlite3.Error as e:
    print(f"\nCaught sqlite3.Error: {e}")

# OperationalError (bad SQL), IntegrityError (constraint violation), etc.
# are all subclasses of sqlite3.Error, so one except block catches them all.


# ── 8. List all tables ────────────────────────────────────────────────────────
# sqlite_master is a system table that describes the database schema.
# This is how the lifespan/sqlite server implements its list_tables tool.

cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row['name'] for row in cursor.fetchall()]
print(f"\nTables in this database: {tables}")


# ── 9. Close the connection ───────────────────────────────────────────────────
# In the lifespan module this happens in the finally block of the
# @asynccontextmanager, guaranteeing cleanup even if a tool raises.

conn.close()
print("\nConnection closed.")


# ── Quick reference ───────────────────────────────────────────────────────────
#
# | Operation                  | Code                                          |
# |----------------------------|-----------------------------------------------|
# | Open (in-memory)           | conn = sqlite3.connect(":memory:")            |
# | Open (file)                | conn = sqlite3.connect("data.db")             |
# | Run multiple statements    | conn.executescript("CREATE ...; INSERT ...;") |
# | Run one statement          | cursor = conn.execute("SELECT ...")           |
# | All rows as tuples         | cursor.fetchall()                             |
# | One row                    | cursor.fetchone()                             |
# | Column access by name      | conn.row_factory = sqlite3.Row                |
# | Row → dict                 | dict(row)                                     |
# | Parameterised query        | conn.execute("... WHERE x = ?", (value,))    |
# | Catch any SQL error        | except sqlite3.Error as e:                    |
# | Save changes (file DB)     | conn.commit()                                 |
# | Close                      | conn.close()                                  |
