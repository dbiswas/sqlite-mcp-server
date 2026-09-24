# Local SQLite MCP Server

Use natural-language requests to create tables and create, read, update, or delete records in a local SQLite database. The MCP client translates your request into a call to one of this server's tools, so you do not need to write SQL for normal CRUD work.

For example, you can ask your agent:

> Create a customers table with an ID, name, email, and created date.

> Add a customer named Ada Lovelace with the email ada@example.com.

> Show me all customers whose name starts with A.

> Change Ada's email to ada.lovelace@example.com.

> Delete the customer whose ID is 3.

## How it works

```text
Your natural-language request
          ↓
An MCP-compatible AI client
          ↓
This local FastMCP server
          ↓
Your local SQLite database file
```

The client starts the server when it is needed. The server uses `stdio`, so it does not open a network port and does not need to run as a separate web service.

## What you need

- Python 3.13.15
- SQLite (the command-line program is useful for checking the database)
- An MCP-compatible client, such as Claude Desktop or VS Code with GitHub Copilot
- Git, if you want to clone this repository

Python already includes the `sqlite3` library used by this server. Installing the SQLite command-line program is still recommended because it lets you inspect the database yourself.

## Step 1: Download this project

Clone the repository, or download it as a ZIP file from GitHub and extract it.

```bash
git clone dbiswas/sqlite-mcp-server
cd sqlite-mcp-server/mcp-servers/sqlite-mcp
```

Replace `<repository-url>` with this repository's GitHub URL.

All remaining terminal commands should be run from the `mcp-servers/sqlite-mcp` directory unless a step says otherwise.

## Step 2: Install the locked Python version

Download and install Python 3.13.15 from [python.org](https://www.python.org/downloads/). On Windows, select **Add Python to PATH** during installation.

Check the installation:

```bash
python --version
```

The result must be `Python 3.13.15`. The same version is recorded in `.python-version` and required by `pyproject.toml`. Using the same Python patch release removes another source of differences between machines.

## Step 3: Install SQLite

Choose the instructions for your operating system.

### Windows

1. Open the official [SQLite download page](https://www.sqlite.org/download.html).
2. Under **Precompiled Binaries for Windows**, download the `sqlite-tools-win-x64-*.zip` file. Use the ARM64 file instead if your computer has an ARM processor.
3. Extract the ZIP file to a simple location such as `C:\sqlite`.
4. Add `C:\sqlite` to your Windows `Path` environment variable:
   1. Search Windows for **Environment Variables**.
   2. Open **Edit the system environment variables**.
   3. Select **Environment Variables**.
   4. Under your user variables, select **Path**, select **Edit**, and then select **New**.
   5. Enter `C:\sqlite`, and save each open window.
5. Close and reopen your terminal.

### macOS

If you use [Homebrew](https://brew.sh/), run:

```bash
brew install sqlite
```

### Ubuntu or Debian Linux

```bash
sudo apt update
sudo apt install sqlite3
```

### Fedora or Red Hat Linux

```bash
sudo dnf install sqlite
```

Check the installation:

```bash
sqlite3 --version
```

If this command is not found, reopen the terminal and try again. The MCP server can still work through Python's built-in `sqlite3` library even when the SQLite command-line program is not installed.

## Step 4: Create the virtual environment and install dependencies

Run the included bootstrap installer:

```bash
python install_dependencies.py
```

The installer creates `.venv`, enforces every package hash in `requirements.txt`, and chooses a reachable package source without changing the lock:

1. It first uses Microsoft's package-feed proxy, avoiding the `files.pythonhosted.org` domain blocked on Microsoft-managed networks.
2. If that proxy is unavailable, it falls back to public PyPI for users on other networks.

It also ignores a globally set `PIP_NO_INDEX` value for this installation because it supplies an explicit package index. To force a specific approved index instead of automatic selection, run:

```bash
python install_dependencies.py --index-url https://your-approved-index.example/simple/
```

## Step 5: Verify the locked environment

The two direct dependencies are:

- `mcp[cli]`, which provides the FastMCP server framework and development tools
- `pydantic`, which validates every tool input before a database operation runs

Their exact versions and all transitive dependencies are pinned with artifact hashes in `requirements.txt`. Activate the environment created in Step 4:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS or Linux
source .venv/bin/activate
```

Verify the environment:

```bash
python --version
python -c "from importlib.metadata import version; print('mcp:', version('mcp')); print('pydantic:', version('pydantic'))"
```

Do not run `pip freeze` to update this project. Follow the maintenance instructions below so `pyproject.toml` and `requirements.txt` remain synchronized.

## Step 6: Understand the server file

The implementation is in `mcp-servers/sqlite-mcp/server.py`. It:

1. Reads the database location from `SQLITE_DB_PATH`.
2. Opens the database with Python's built-in `sqlite3` library.
3. Uses Pydantic models to validate inputs.
4. Exposes database operations as FastMCP tools.
5. Runs locally with the `stdio` transport expected by desktop MCP clients.

The server provides these tools:

| Tool | What it does |
| --- | --- |
| `sqlite_list_tables` | Lists tables and their row counts |
| `sqlite_describe_table` | Shows the columns in one table |
| `sqlite_query` | Reads records with a `SELECT` query and pagination |
| `sqlite_create_table` | Creates a table |
| `sqlite_insert_row` | Creates one record |
| `sqlite_update_rows` | Updates records that match required conditions |
| `sqlite_delete_rows` | Deletes records that match required conditions |
| `sqlite_drop_table` | Deletes a table after explicit confirmation |
| `sqlite_execute` | Runs advanced SQL when a focused tool is not enough |

For normal natural-language requests, your agent chooses and calls these tools for you.

## Step 7: Choose the database file

SQLite stores the whole database in one local file. You do not need to create the file first; SQLite creates it the first time the server writes to it.

Create a folder for the database:

### Windows PowerShell

```powershell
New-Item -ItemType Directory -Force data
```

### macOS or Linux

```bash
mkdir -p data
```

Get the full path of the current directory:

```powershell
# Windows PowerShell
(Get-Location).Path
```

```bash
# macOS or Linux
pwd
```

Append `data/local.db` to that path. The repository's database now lives at `mcp-servers/sqlite-mcp/data/local.db`. You will use this absolute database path in the client configuration. If `SQLITE_DB_PATH` is not set, the server uses that same location, resolved relative to `server.py`.

## Step 8: Test the server

Start it from the `mcp-servers/sqlite-mcp` directory:

```bash
python server.py
```

The terminal should show a message similar to:

```text
Starting sqlite_mcp server — DB: ...\mcp-servers\sqlite-mcp\data\local.db
```

The command then waits silently for an MCP client. This is normal. Press `Ctrl+C` to stop this manual test.

Optional: use the MCP Inspector for an interactive test. This requires Node.js and `npx`:

```bash
mcp dev server.py
```

## Step 9: Find the absolute Python and server paths

An MCP client may not use the same `PATH` as your terminal. Using absolute paths makes startup more reliable.

### Windows PowerShell

Run these commands inside `mcp-servers/sqlite-mcp`:

```powershell
(Resolve-Path .\.venv\Scripts\python.exe).Path
(Resolve-Path .\server.py).Path
(Resolve-Path .\data).Path
```

Your database path is the last result followed by `\local.db`.

Example values:

```text
C:\Projects\building-local-sqlite-mcp\mcp-servers\sqlite-mcp\.venv\Scripts\python.exe
C:\Projects\building-local-sqlite-mcp\mcp-servers\sqlite-mcp\server.py
C:\Projects\building-local-sqlite-mcp\mcp-servers\sqlite-mcp\data\local.db
```

### macOS or Linux

Run these commands inside `mcp-servers/sqlite-mcp`:

```bash
realpath .venv/bin/python
realpath server.py
realpath data
```

Your database path is the last result followed by `/local.db`.

## Step 10: Configure your MCP client

The client and this server must run on the same computer because this setup uses local `stdio` communication and a local database file.

Choose one client below. Replace every example path with the absolute paths from Step 9.

### Option A: Claude Desktop

1. Open Claude Desktop.
2. Open **Settings** and then **Developer**.
3. Select **Edit Config**.
4. Put the following JSON in `claude_desktop_config.json`.

Windows example:

```json
{
  "mcpServers": {
    "localSqlite": {
      "command": "C:\\Projects\\building-local-sqlite-mcp\\mcp-servers\\sqlite-mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Projects\\building-local-sqlite-mcp\\mcp-servers\\sqlite-mcp\\server.py"
      ],
      "env": {
        "SQLITE_DB_PATH": "C:\\Projects\\building-local-sqlite-mcp\\mcp-servers\\sqlite-mcp\\data\\local.db"
      }
    }
  }
}
```

macOS example:

```json
{
  "mcpServers": {
    "localSqlite": {
      "command": "/Users/your-name/Projects/building-local-sqlite-mcp/mcp-servers/sqlite-mcp/.venv/bin/python",
      "args": [
        "/Users/your-name/Projects/building-local-sqlite-mcp/mcp-servers/sqlite-mcp/server.py"
      ],
      "env": {
        "SQLITE_DB_PATH": "/Users/your-name/Projects/building-local-sqlite-mcp/mcp-servers/sqlite-mcp/data/local.db"
      }
    }
  }
}
```

5. Save the file.
6. Fully quit and reopen Claude Desktop.
7. Open the Developer settings and confirm that `localSqlite` is running.

The usual config file locations are:

- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

See the official [MCP guide for connecting local servers](https://modelcontextprotocol.io/docs/2026-07-28/develop/connect-local-servers) if the Claude Desktop menus have changed.

### Option B: VS Code with GitHub Copilot

1. Open the repository folder in VS Code.
2. Create `.vscode/mcp.json` in the repository root.
3. Add this configuration.

Windows example:

```json
{
  "servers": {
    "localSqlite": {
      "type": "stdio",
      "command": "${workspaceFolder}\\mcp-servers\\sqlite-mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "${workspaceFolder}\\mcp-servers\\sqlite-mcp\\server.py"
      ],
      "env": {
        "SQLITE_DB_PATH": "${workspaceFolder}\\mcp-servers\\sqlite-mcp\\data\\local.db"
      }
    }
  }
}
```

macOS or Linux example:

```json
{
  "servers": {
    "localSqlite": {
      "type": "stdio",
      "command": "${workspaceFolder}/mcp-servers/sqlite-mcp/.venv/bin/python",
      "args": [
        "${workspaceFolder}/mcp-servers/sqlite-mcp/server.py"
      ],
      "env": {
        "SQLITE_DB_PATH": "${workspaceFolder}/mcp-servers/sqlite-mcp/data/local.db"
      }
    }
  }
}
```

4. Save the file.
5. Open the Command Palette with `Ctrl+Shift+P` on Windows/Linux or `Cmd+Shift+P` on macOS.
6. Run **MCP: List Servers**.
7. Select `localSqlite`, start it if needed, and confirm that its tools are available.
8. Open Copilot Chat in Agent mode. Make sure MCP tools are enabled for the conversation.

See the official [VS Code MCP configuration reference](https://code.visualstudio.com/docs/agents/reference/mcp-configuration) for user-level and portable configuration options.

## Step 11: Try natural-language CRUD operations

Open your client's chat or agent window and try these requests in order.

### 11.1 Create a table

> Create a products table in my SQLite database. Add an auto-incrementing integer ID, a required name, a real-number price, and an integer stock quantity.

Then ask:

> Show me the structure of the products table.

### 11.2 Create records

> Add a product named Keyboard with a price of 49.99 and a stock quantity of 10.

> Add a product named Mouse with a price of 19.99 and a stock quantity of 25.

### 11.3 Read records

> List all products.

> Show products that cost less than 25.

### 11.4 Update a record

> Change the stock quantity of the product named Keyboard to 8.

### 11.5 Delete a record

> Delete the product named Mouse.

### 11.6 Check the final result

> List all products and show their ID, name, price, and stock quantity.

Your client may ask for approval before it calls a tool, especially for update or delete operations. Review the proposed action before approving it.

## Step 12: Inspect the database directly (optional)

You can open the database with the SQLite command-line program:

```bash
sqlite3 data/local.db
```

At the `sqlite>` prompt, run:

```text
.tables
.schema products
SELECT * FROM products;
.quit
```

This direct SQL step is only for checking the result. Normal users can perform the same work through natural-language requests in the MCP client.

## Safety notes

- Back up an important database file before allowing an AI agent to change it.
- Use a separate test database while learning.
- `sqlite_query` accepts only `SELECT` statements.
- Update and delete tools require at least one filter condition. This helps prevent accidental changes to every row.
- Dropping a table requires explicit confirmation.
- `sqlite_execute` can run arbitrary SQL and is intentionally marked as an advanced, destructive tool. Only approve it when you understand the request.
- The server can access only the database file set by `SQLITE_DB_PATH`, but anyone who can use the configured MCP client may be able to change that database.

## Troubleshooting

### The client says the server failed to start

- Confirm that `command` points to the virtual environment's real Python executable.
- Confirm that `args` contains the absolute path to `server.py`.
- Run the exact Python command from a terminal and read the error.
- In VS Code, run **MCP: List Servers**, select the server, and open its output.
- In Claude Desktop, fully quit the application before reopening it.

### `ModuleNotFoundError: No module named 'mcp'`

The client is probably using a different Python installation. Point `command` to `.venv` as shown in Step 10, and rerun the installer:

```bash
python install_dependencies.py
```

### pip reports a hash or dependency error

Restore `pyproject.toml` and `requirements.txt` from the same repository revision, confirm that Python 3.13.15 is active, and retry. Do not remove `--require-hashes`, because doing so weakens the reproducibility and integrity checks.

### Windows Security blocks `files.pythonhosted.org`

Use the included installer instead of a plain `pip install` command:

```bash
python install_dependencies.py
```

It uses `https://packagefeedproxy.microsoft.io/pypi/simple/` first, so package downloads stay on the Microsoft-approved route. Hash verification remains enabled. If your organization provides a different approved Python feed, pass it with `--index-url`.

### The server uses the wrong database

Check the `SQLITE_DB_PATH` value in the client configuration. Use an absolute path, save the file, and restart the MCP server or client.

### The database is locked

Close other programs that may be editing the same database, including an open `sqlite3` session, and try again.

### The tool is not visible to the agent

- Confirm that the server is running in the client's MCP settings.
- Enable tools in the current chat or Agent session.
- Restart the server after changing `server.py`.
- In VS Code, run **MCP: Reset Cached Tools** if an old tool list is still shown.

## Maintaining dependency locks

Normal users should not modify dependency files. When a maintainer intentionally upgrades a dependency:

1. Edit the requested version in `pyproject.toml`.
2. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and regenerate the complete cross-platform lock:

   ```bash
   uv pip compile pyproject.toml --universal --generate-hashes --output-file requirements.txt
   ```

3. Run the verification commands from Step 5 and test the server.
4. Commit `pyproject.toml` and `requirements.txt` together.

The lock makes installs reproducible for the supported Python version and platforms for which the packages publish compatible artifacts. It cannot compensate for unsupported operating systems or unavailable platform-specific package builds.

## Project structure

```text
building-local-sqlite-mcp/
├── README.md
└── mcp-servers/
    └── sqlite-mcp/
        ├── .python-version
        ├── README.md
        ├── install_dependencies.py
        ├── pyproject.toml
        ├── requirements.txt
        ├── server.py
        └── data/
            └── local.db        # Created after the first database write
```

The database file and virtual environment are local machine artifacts. Do not commit database files that contain private or sensitive data.
