"""
SQLite MCP Server
-----------------
A FastMCP server that exposes full CRUD operations on a local SQLite database.
Configure the target database via the SQLITE_DB_PATH environment variable.

Transport: stdio (for local use with Claude Desktop / VS Code MCP clients)
"""

import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Load .env from server directory (if present), then fall back to env var
# ---------------------------------------------------------------------------

def _load_dotenv():
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())

_load_dotenv()

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, stream=__import__("sys").stderr)
log = logging.getLogger("sqlite_mcp")

DB_PATH = os.environ.get("SQLITE_DB_PATH", "morning_briefing.db")

mcp = FastMCP("sqlite_mcp")


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

@contextmanager
def get_conn():
    """Open a SQLite connection with row_factory for dict-like rows."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def rows_to_list(rows) -> List[Dict[str, Any]]:
    return [dict(r) for r in rows]


def _safe_identifier(name: str) -> str:
    """Reject identifiers containing dangerous characters."""
    if not name.replace("_", "").replace("-", "").isalnum():
        raise ValueError(
            f"Unsafe identifier '{name}'. Use only letters, digits, underscores and hyphens."
        )
    return name


# ---------------------------------------------------------------------------
# Pydantic input models
# ---------------------------------------------------------------------------

class ListTablesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response_format: str = Field(
        default="markdown",
        description="Output format: 'markdown' or 'json'",
        pattern="^(markdown|json)$",
    )


class DescribeTableInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    table_name: str = Field(..., description="Name of the table to describe", min_length=1, max_length=128)
    response_format: str = Field(
        default="markdown",
        description="Output format: 'markdown' or 'json'",
        pattern="^(markdown|json)$",
    )


class QueryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sql: str = Field(
        ...,
        description="A SELECT statement to run. Only SELECT queries are permitted.",
        min_length=6,
        max_length=4096,
    )
    params: Optional[List[Any]] = Field(
        default_factory=list,
        description="Positional parameters bound to '?' placeholders in the SQL.",
    )
    limit: int = Field(default=50, ge=1, le=500, description="Max rows to return (1–500, default 50)")
    offset: int = Field(default=0, ge=0, description="Row offset for pagination")

    @field_validator("sql")
    @classmethod
    def must_be_select(cls, v: str) -> str:
        if not v.strip().upper().startswith("SELECT"):
            raise ValueError("Only SELECT statements are allowed in sqlite_query. Use sqlite_execute for writes.")
        return v


class InsertRowInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    table_name: str = Field(..., description="Target table name", min_length=1, max_length=128)
    row: Dict[str, Any] = Field(
        ...,
        description="Key-value pairs mapping column names to values to insert.",
        min_length=1,
    )


class UpdateRowsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    table_name: str = Field(..., description="Target table name", min_length=1, max_length=128)
    updates: Dict[str, Any] = Field(
        ...,
        description="Column names → new values to set.",
        min_length=1,
    )
    where: Dict[str, Any] = Field(
        ...,
        description="Column names → values used as WHERE conditions (ANDed together). Must not be empty.",
        min_length=1,
    )


class DeleteRowsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    table_name: str = Field(..., description="Target table name", min_length=1, max_length=128)
    where: Dict[str, Any] = Field(
        ...,
        description="Column names → values used as WHERE conditions (ANDed together). Must not be empty — this prevents accidental full-table deletes.",
        min_length=1,
    )


class CreateTableInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    table_name: str = Field(..., description="Name of the new table", min_length=1, max_length=128)
    columns: List[Dict[str, str]] = Field(
        ...,
        description=(
            "Column definitions. Each item must have 'name' (str) and 'type' (str, e.g. TEXT, INTEGER, REAL, BLOB). "
            "Optionally add 'constraints' (e.g. 'PRIMARY KEY', 'NOT NULL', 'UNIQUE')."
        ),
        min_length=1,
    )
    if_not_exists: bool = Field(
        default=True,
        description="When true, use CREATE TABLE IF NOT EXISTS to avoid errors on duplicate table names.",
    )


class DropTableInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    table_name: str = Field(..., description="Name of the table to drop", min_length=1, max_length=128)
    confirm: bool = Field(
        ...,
        description="Must be explicitly set to true to confirm the destructive drop operation.",
    )


class ExecuteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sql: str = Field(
        ...,
        description="Any valid SQLite statement (INSERT / UPDATE / DELETE / DDL). Use with care.",
        min_length=1,
        max_length=4096,
    )
    params: Optional[List[Any]] = Field(
        default_factory=list,
        description="Positional parameters bound to '?' placeholders.",
    )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(
    name="sqlite_list_tables",
    annotations={
        "title": "List all tables in the SQLite database",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def sqlite_list_tables(params: ListTablesInput) -> str:
    """
    List all user-created tables in the connected SQLite database.

    Returns table names along with the row count for each table.

    Args:
        params (ListTablesInput):
            - response_format (str): 'markdown' (default) or 'json'

    Returns:
        str: Table list as markdown or JSON.
    """
    try:
        with get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in c.fetchall()]

            results = []
            for t in tables:
                c.execute(f'SELECT COUNT(*) FROM "{t}"')
                count = c.fetchone()[0]
                results.append({"table": t, "row_count": count})

        if params.response_format == "json":
            return json.dumps({"tables": results, "total": len(results)}, indent=2)

        if not results:
            return "No tables found in the database."
        lines = ["## Tables\n", f"Database: `{DB_PATH}`\n"]
        lines.append(f"| Table | Rows |")
        lines.append(f"|-------|------|")
        for r in results:
            lines.append(f"| `{r['table']}` | {r['row_count']} |")
        return "\n".join(lines)

    except Exception as e:
        log.error("sqlite_list_tables error: %s", e)
        return json.dumps({"error": str(e), "hint": "Verify SQLITE_DB_PATH points to a valid SQLite file."})


@mcp.tool(
    name="sqlite_describe_table",
    annotations={
        "title": "Describe the schema of a table",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def sqlite_describe_table(params: DescribeTableInput) -> str:
    """
    Return the column schema for a specific table including column names, types,
    nullability, default values, and primary key membership.

    Args:
        params (DescribeTableInput):
            - table_name (str): Name of the table to inspect
            - response_format (str): 'markdown' or 'json'

    Returns:
        str: Column schema as markdown table or JSON array.
    """
    try:
        _safe_identifier(params.table_name)
        with get_conn() as conn:
            c = conn.cursor()
            c.execute(f'PRAGMA table_info("{params.table_name}")')
            cols = rows_to_list(c.fetchall())

        if not cols:
            return json.dumps({"error": f"Table '{params.table_name}' not found or has no columns."})

        if params.response_format == "json":
            return json.dumps({"table": params.table_name, "columns": cols}, indent=2)

        lines = [f"## Schema: `{params.table_name}`\n"]
        lines.append("| # | Column | Type | Not Null | Default | PK |")
        lines.append("|---|--------|------|----------|---------|-----|")
        for col in cols:
            pk = "✓" if col["pk"] else ""
            nn = "✓" if col["notnull"] else ""
            dv = col["dflt_value"] if col["dflt_value"] is not None else ""
            lines.append(f"| {col['cid']} | `{col['name']}` | {col['type']} | {nn} | {dv} | {pk} |")
        return "\n".join(lines)

    except Exception as e:
        log.error("sqlite_describe_table error: %s", e)
        return json.dumps({"error": str(e)})


@mcp.tool(
    name="sqlite_query",
    annotations={
        "title": "Run a SELECT query",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def sqlite_query(params: QueryInput) -> str:
    """
    Execute a read-only SELECT statement and return results as JSON.

    Only SELECT statements are accepted; use sqlite_execute for write operations.
    Supports parameterized queries with '?' placeholders to prevent SQL injection.

    Args:
        params (QueryInput):
            - sql (str): The SELECT statement (e.g., "SELECT * FROM users WHERE active = ?")
            - params (List[Any]): Bound values for '?' placeholders (e.g., [1])
            - limit (int): Max rows to return (default 50, max 500)
            - offset (int): Row offset for pagination (default 0)

    Returns:
        str: JSON object with 'rows', 'count', 'offset', 'has_more'.
    """
    try:
        # Inject pagination wrapper
        paginated_sql = f"SELECT * FROM ({params.sql}) __q LIMIT ? OFFSET ?"
        bound = list(params.params or []) + [params.limit, params.offset]

        with get_conn() as conn:
            c = conn.cursor()
            c.execute(paginated_sql, bound)
            rows = rows_to_list(c.fetchall())

        # Check if more rows exist
        count_sql = f"SELECT COUNT(*) FROM ({params.sql}) __q"
        with get_conn() as conn:
            c = conn.cursor()
            c.execute(count_sql, list(params.params or []))
            total = c.fetchone()[0]

        return json.dumps(
            {
                "rows": rows,
                "count": len(rows),
                "offset": params.offset,
                "total": total,
                "has_more": (params.offset + len(rows)) < total,
                "next_offset": params.offset + len(rows) if (params.offset + len(rows)) < total else None,
            },
            indent=2,
            default=str,
        )

    except Exception as e:
        log.error("sqlite_query error: %s", e)
        return json.dumps({"error": str(e), "hint": "Check your SQL syntax and table/column names."})


@mcp.tool(
    name="sqlite_insert_row",
    annotations={
        "title": "Insert a new row into a table",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def sqlite_insert_row(params: InsertRowInput) -> str:
    """
    Insert a single row into the specified table.

    Args:
        params (InsertRowInput):
            - table_name (str): Target table (e.g., 'users')
            - row (dict): Column-value pairs (e.g., {"name": "Alice", "age": 30})

    Returns:
        str: JSON with 'success', 'last_insert_rowid', and 'rows_affected'.
    """
    try:
        _safe_identifier(params.table_name)
        cols = [_safe_identifier(k) for k in params.row.keys()]
        placeholders = ", ".join(["?"] * len(cols))
        col_list = ", ".join(f'"{c}"' for c in cols)
        sql = f'INSERT INTO "{params.table_name}" ({col_list}) VALUES ({placeholders})'
        values = list(params.row.values())

        with get_conn() as conn:
            c = conn.cursor()
            c.execute(sql, values)
            return json.dumps({
                "success": True,
                "last_insert_rowid": c.lastrowid,
                "rows_affected": c.rowcount,
            })

    except Exception as e:
        log.error("sqlite_insert_row error: %s", e)
        return json.dumps({"error": str(e), "hint": "Check column names match the table schema."})


@mcp.tool(
    name="sqlite_update_rows",
    annotations={
        "title": "Update rows matching WHERE conditions",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def sqlite_update_rows(params: UpdateRowsInput) -> str:
    """
    Update rows in a table that match all given WHERE conditions.

    Both 'updates' and 'where' are required. WHERE conditions are ANDed together.
    This prevents accidental full-table updates.

    Args:
        params (UpdateRowsInput):
            - table_name (str): Target table
            - updates (dict): Columns to set (e.g., {"status": "active"})
            - where (dict): Filter conditions (e.g., {"id": 42})

    Returns:
        str: JSON with 'success' and 'rows_affected'.
    """
    try:
        _safe_identifier(params.table_name)
        set_clauses = ", ".join(f'"{_safe_identifier(k)}" = ?' for k in params.updates)
        where_clauses = " AND ".join(f'"{_safe_identifier(k)}" = ?' for k in params.where)
        sql = f'UPDATE "{params.table_name}" SET {set_clauses} WHERE {where_clauses}'
        values = list(params.updates.values()) + list(params.where.values())

        with get_conn() as conn:
            c = conn.cursor()
            c.execute(sql, values)
            return json.dumps({"success": True, "rows_affected": c.rowcount})

    except Exception as e:
        log.error("sqlite_update_rows error: %s", e)
        return json.dumps({"error": str(e)})


@mcp.tool(
    name="sqlite_delete_rows",
    annotations={
        "title": "Delete rows matching WHERE conditions",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def sqlite_delete_rows(params: DeleteRowsInput) -> str:
    """
    Delete rows from a table that match all given WHERE conditions.

    'where' is mandatory — passing an empty dict is rejected to prevent
    accidental full-table deletion. Use sqlite_execute with extreme care
    for full-table truncation.

    Args:
        params (DeleteRowsInput):
            - table_name (str): Target table
            - where (dict): Filter conditions (e.g., {"id": 42})

    Returns:
        str: JSON with 'success' and 'rows_affected'.
    """
    try:
        _safe_identifier(params.table_name)
        where_clauses = " AND ".join(f'"{_safe_identifier(k)}" = ?' for k in params.where)
        sql = f'DELETE FROM "{params.table_name}" WHERE {where_clauses}'
        values = list(params.where.values())

        with get_conn() as conn:
            c = conn.cursor()
            c.execute(sql, values)
            return json.dumps({"success": True, "rows_affected": c.rowcount})

    except Exception as e:
        log.error("sqlite_delete_rows error: %s", e)
        return json.dumps({"error": str(e)})


@mcp.tool(
    name="sqlite_create_table",
    annotations={
        "title": "Create a new table",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def sqlite_create_table(params: CreateTableInput) -> str:
    """
    Create a new table with the specified columns.

    Args:
        params (CreateTableInput):
            - table_name (str): Name of the table to create
            - columns (list): Each item has 'name', 'type', and optional 'constraints'
              e.g., [{"name":"id","type":"INTEGER","constraints":"PRIMARY KEY AUTOINCREMENT"},
                     {"name":"title","type":"TEXT","constraints":"NOT NULL"}]
            - if_not_exists (bool): Use CREATE TABLE IF NOT EXISTS (default true)

    Returns:
        str: JSON with 'success' and the DDL executed.
    """
    try:
        _safe_identifier(params.table_name)
        col_defs = []
        for col in params.columns:
            name = _safe_identifier(col["name"])
            ctype = col.get("type", "TEXT").upper()
            constraints = col.get("constraints", "")
            col_defs.append(f'"{name}" {ctype} {constraints}'.strip())

        exists_clause = "IF NOT EXISTS " if params.if_not_exists else ""
        ddl = f'CREATE TABLE {exists_clause}"{params.table_name}" ({", ".join(col_defs)})'

        with get_conn() as conn:
            conn.cursor().execute(ddl)
            return json.dumps({"success": True, "ddl": ddl})

    except Exception as e:
        log.error("sqlite_create_table error: %s", e)
        return json.dumps({"error": str(e)})


@mcp.tool(
    name="sqlite_drop_table",
    annotations={
        "title": "Drop (delete) a table permanently",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def sqlite_drop_table(params: DropTableInput) -> str:
    """
    Permanently delete a table and all its data from the database.

    This operation is irreversible. The 'confirm' field must be explicitly set
    to true to prevent accidental drops.

    Args:
        params (DropTableInput):
            - table_name (str): Table to drop
            - confirm (bool): Must be true to proceed

    Returns:
        str: JSON with 'success' or an error if confirm is false.
    """
    if not params.confirm:
        return json.dumps({
            "error": "Drop cancelled. Set confirm=true to permanently delete the table.",
        })
    try:
        _safe_identifier(params.table_name)
        with get_conn() as conn:
            conn.cursor().execute(f'DROP TABLE IF EXISTS "{params.table_name}"')
            return json.dumps({"success": True, "dropped": params.table_name})

    except Exception as e:
        log.error("sqlite_drop_table error: %s", e)
        return json.dumps({"error": str(e)})


@mcp.tool(
    name="sqlite_execute",
    annotations={
        "title": "Execute any SQL statement (advanced)",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def sqlite_execute(params: ExecuteInput) -> str:
    """
    Execute any SQLite statement: INSERT, UPDATE, DELETE, or DDL.

    Use this for complex write operations not covered by the dedicated tools.
    Prefer the focused tools (sqlite_insert_row, sqlite_update_rows, etc.) when possible
    as they provide safer guardrails.

    Args:
        params (ExecuteInput):
            - sql (str): SQL statement to execute
            - params (List[Any]): Bound values for '?' placeholders

    Returns:
        str: JSON with 'success', 'rows_affected', and 'last_insert_rowid'.
    """
    try:
        with get_conn() as conn:
            c = conn.cursor()
            c.execute(params.sql, list(params.params or []))
            return json.dumps({
                "success": True,
                "rows_affected": c.rowcount,
                "last_insert_rowid": c.lastrowid,
            })

    except Exception as e:
        log.error("sqlite_execute error: %s", e)
        return json.dumps({"error": str(e), "hint": "Check your SQL syntax."})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    log.info("Starting sqlite_mcp server — DB: %s", DB_PATH)
    mcp.run(transport="stdio")
