"""Example showing lifespan with a real SQLite database."""

import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession


class Database:
    """SQLite database wrapper."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row  # Access columns by name

    @classmethod
    async def connect(cls) -> "Database":
        """Connect and initialize database with sample data."""
        conn = sqlite3.connect(":memory:")  # In-memory database
        db = cls(conn)
        db._create_sample_data()
        return db

    def _create_sample_data(self):
        """Create tables and insert sample data."""
        self.conn.executescript("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                role TEXT NOT NULL
            );
            
            INSERT INTO users (name, email, role) VALUES
                ('Alice', 'alice@example.com', 'admin'),
                ('Bob', 'bob@example.com', 'developer'),
                ('Charlie', 'charlie@example.com', 'designer'),
                ('Diana', 'diana@example.com', 'developer');
            
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL
            );
            
            INSERT INTO projects (name, status) VALUES
                ('Website Redesign', 'active'),
                ('Mobile App', 'planning'),
                ('API Integration', 'completed');
        """)
        self.conn.commit()

    async def disconnect(self) -> None:
        """Close the database connection."""
        self.conn.close()

    def query(self, sql: str) -> list[dict]:
        """Execute a SELECT query and return results."""
        cursor = self.conn.execute(sql)
        return [dict(row) for row in cursor.fetchall()]

    def add_user(self, name: str, email: str, role: str) -> int:
        """Insert a new user and return their ID."""
        cursor = self.conn.execute(
            "INSERT INTO users (name, email, role) VALUES (?, ?, ?)",
            (name, email, role),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_users(self) -> list[dict]:
        """Return all users."""
        return self.query("SELECT * FROM users")

    def get_tables(self) -> list[str]:
        """List all tables in the database."""
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        return [row[0] for row in cursor.fetchall()]


@dataclass
class AppContext:
    """Application context with typed dependencies."""
    db: Database


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context."""
    db = await Database.connect()
    try:
        yield AppContext(db=db)
    finally:
        await db.disconnect()


mcp = FastMCP("SQLite Demo", lifespan=app_lifespan)


@mcp.tool()
def list_tables(ctx: Context[ServerSession, AppContext]) -> str:
    """List all tables in the database."""
    db = ctx.request_context.lifespan_context.db
    tables = db.get_tables()
    return f"Tables: {', '.join(tables)}"


@mcp.tool()
def query_db(ctx: Context[ServerSession, AppContext], sql: str) -> str:
    """Execute a SELECT query on the database."""
    db = ctx.request_context.lifespan_context.db
    try:
        results = db.query(sql)
        if not results:
            return "No results found."
        return str(results)
    except sqlite3.Error as e:
        return f"SQL Error: {e}"


@mcp.tool()
def list_users(ctx: Context[ServerSession, AppContext]) -> str:
    """List all users in the database."""
    db = ctx.request_context.lifespan_context.db
    users = db.get_users()
    lines = [f"{u['id']}. {u['name']} ({u['role']}) — {u['email']}" for u in users]
    return "\n".join(lines)


@mcp.tool()
def add_user(ctx: Context[ServerSession, AppContext], name: str, email: str, role: str) -> str:
    """Add a new user to the database. Proves lifespan shares state across tool calls."""
    db = ctx.request_context.lifespan_context.db
    user_id = db.add_user(name, email, role)
    return f"Added user '{name}' with ID {user_id} to the shared DB."


if __name__ == "__main__":
    mcp.run(transport="stdio")
    # mcp.run(transport="streamable-http")
