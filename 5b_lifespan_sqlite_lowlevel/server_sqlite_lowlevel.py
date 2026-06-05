"""Low-level server example showing lifespan with a real SQLite database.




1. Tool parameter (sql) handling
FastMCP (server_sqlite.py:101):
def query_db(ctx: Context[ServerSession, AppContext], sql: str) -> str:
The sql parameter is declared on the function — FastMCP generates the schema from the type hint automatically.
Low-level (server_sqlite_lowlevel.py:105-110):
"sql": {"type": "string", "description": "SQL SELECT query to execute"}
You write the JSON Schema by hand. Then access it via arguments["sql"] — a plain dict, no type safety.
2. Lifespan context type
FastMCP yields a typed AppContext(db=db) → accessed as .lifespan_context.db (attribute, IDE autocomplete works).
Low-level yields {"db": db} → accessed as lifespan_context["db"] (string key, no type safety, typo = runtime error).
3. Everything else is identical to the counter comparison — split list_tools/call_tool handlers, manual transport wiring, manual InitializationOptions.
Bottom line
This example reinforces the same conclusion. The SQLite use case doesn't exercise anything that requires low-level. The only added nuance here: with a tool that takes a parameter (sql), FastMCP's type-hint-to-schema derivation saves more boilerplate than in the no-parameter counter example — and the low-level dict access for both context and arguments removes type safety.

"""

import asyncio
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions


class Database:
    """SQLite database wrapper."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row

    @classmethod
    async def connect(cls) -> "Database":
        """Connect and initialize database with sample data."""
        conn = sqlite3.connect(":memory:")
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

    def get_tables(self) -> list[str]:
        """List all tables in the database."""
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        return [row[0] for row in cursor.fetchall()]


@asynccontextmanager
async def server_lifespan(_server: Server) -> AsyncIterator[dict[str, Any]]:
    """Manage server startup and shutdown lifecycle."""
    db = await Database.connect()
    try:
        yield {"db": db}
    finally:
        await db.disconnect()


server = Server("sqlite-server", lifespan=server_lifespan)


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="list_tables",
            description="List all tables in the database.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="query_db",
            description="Execute a SELECT query on the database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "SQL SELECT query to execute"}
                },
                "required": ["sql"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle tool calls."""
    ctx = server.request_context
    db = ctx.lifespan_context["db"]

    if name == "list_tables":
        tables = db.get_tables()
        return [types.TextContent(type="text", text=f"Tables: {', '.join(tables)}")]

    elif name == "query_db":
        try:
            results = db.query(arguments["sql"])
            if not results:
                return [types.TextContent(type="text", text="No results found.")]
            return [types.TextContent(type="text", text=str(results))]
        except sqlite3.Error as e:
            return [types.TextContent(type="text", text=f"SQL Error: {e}")]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def run():
    """Run the server with lifespan management."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="sqlite-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(run())
