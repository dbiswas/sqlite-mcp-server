# sqlite-mcp — SQLite CRUD MCP Server

A [FastMCP](https://github.com/modelcontextprotocol/python-sdk) server that exposes full **CRUD** operations on any local SQLite database via the Model Context Protocol (stdio transport).

---

## Tools

| Tool | Description |
|------|-------------|
| `sqlite_list_tables` | List all tables and their row counts |
| `sqlite_describe_table` | Show column schema for a table |
| `sqlite_query` | Run a **SELECT** query (paginated, read-only) |
| `sqlite_insert_row` | Insert a row by column-value dict |
| `sqlite_update_rows` | Update rows matching WHERE conditions |
| `sqlite_delete_rows` | Delete rows matching WHERE conditions |
| `sqlite_create_table` | Create a new table with column definitions |
| `sqlite_drop_table` | Drop a table (requires `confirm: true`) |
| `sqlite_execute` | Execute any SQL statement (advanced) |

---

## Setup

```bash
cd mcp-servers/sqlite-mcp
python install_dependencies.py
```

The installer creates `.venv`, tries Microsoft's package-feed proxy before public PyPI, and verifies every artifact against the hashes in `requirements.txt`. This avoids the `files.pythonhosted.org` block on Microsoft-managed networks. Use `--index-url` to supply another organization-approved feed.

Python 3.13.15 is pinned in `.python-version` and `pyproject.toml`. Direct dependencies are declared with exact versions in `pyproject.toml`, and every transitive dependency is pinned with artifact hashes in `requirements.txt`. Do not edit the generated requirements file manually.

---

## Configuration

Set the database path via environment variable:

```bash
# Windows PowerShell
$env:SQLITE_DB_PATH = "C:\path\to\your\database.db"

# Windows CMD
set SQLITE_DB_PATH=C:\path\to\your\database.db
```

Defaults to `morning_briefing.db` in the working directory if unset.

---

## Running

```bash
python server.py
```

The server uses **stdio transport** — it is designed to be launched by an MCP client (Claude Desktop, VS Code Copilot, etc.).

---

## Claude Desktop Integration

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sqlite": {
      "command": "python",
      "args": ["C:\\path\\to\\mcp-servers\\sqlite-mcp\\server.py"],
      "env": {
        "SQLITE_DB_PATH": "C:\\path\\to\\your\\database.db"
      }
    }
  }
}
```

## VS Code Copilot Integration

Add to `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "sqlite": {
      "type": "stdio",
      "command": "python",
      "args": ["${workspaceFolder}/mcp-servers/sqlite-mcp/server.py"],
      "env": {
        "SQLITE_DB_PATH": "${workspaceFolder}/morning_briefing.db"
      }
    }
  }
}
```

---

## Example Usage (via MCP client)

```
sqlite_list_tables()

sqlite_create_table(table_name="users", columns=[
  {"name": "id",    "type": "INTEGER", "constraints": "PRIMARY KEY AUTOINCREMENT"},
  {"name": "name",  "type": "TEXT",    "constraints": "NOT NULL"},
  {"name": "email", "type": "TEXT",    "constraints": "UNIQUE"}
])

sqlite_insert_row(table_name="users", row={"name": "Alice", "email": "alice@example.com"})

sqlite_query(sql="SELECT * FROM users WHERE name = ?", params=["Alice"])

sqlite_update_rows(table_name="users", updates={"email": "new@example.com"}, where={"id": 1})

sqlite_delete_rows(table_name="users", where={"id": 1})
```

---

## Security Notes

- `sqlite_query` only accepts SELECT statements.
- `sqlite_delete_rows` and `sqlite_update_rows` require a non-empty `where` dict — preventing accidental full-table operations.
- `sqlite_drop_table` requires `confirm: true`.
- All table/column identifiers are validated against an allowlist character set.
- Use parameterized queries (the `params` field) to avoid SQL injection.
