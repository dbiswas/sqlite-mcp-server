# DuckDB MCP Server

This folder is intended for an MCP server that connects AI clients to a local DuckDB database. The server code has not been added yet. This guide explains DuckDB and how to prepare a local database for future MCP integration.

## What is DuckDB?

DuckDB is an embedded SQL database designed for analytics. It runs inside an application or command-line process, so it does not need a separate database service. A persistent database can be stored in one local `.duckdb` file.

DuckDB is often described as the analytical counterpart to SQLite: SQLite is commonly used for application transactions, while DuckDB is optimized for scanning and summarizing large datasets.

## Technology overview

| Area | DuckDB approach |
|---|---|
| Data model | Relational tables and SQL |
| Architecture | Embedded, in-process database |
| Storage | In-memory or a single local file |
| Main workload | OLAP and analytical queries |
| Data access | Native tables, CSV, JSON, Parquet, and extensions |
| Common local port | None; no server is required |

## Strengths

- Fast analytical queries using a column-oriented, vectorized engine.
- No service to install, configure, or keep running.
- Reads formats such as Parquet and CSV directly.
- Works well with Python, pandas, Polars, R, Java, Node.js, and other tools.
- Easy to move or back up when the database is stored in one file.
- Supports familiar SQL, including joins, aggregations, and window functions.

## Good use cases

- Exploring local CSV, JSON, or Parquet files.
- Building local reporting and analytics tools.
- Preparing and transforming datasets for AI or machine-learning work.
- Running data-quality checks and repeatable analysis.
- Creating a lightweight local data warehouse.

DuckDB is less suitable for a high-traffic application with many processes writing at the same time. A client-server database such as PostgreSQL or MySQL is usually a better fit for that workload.

## Install locally

### Windows

Install the command-line client with Windows Package Manager:

```powershell
winget install DuckDB.cli
```

DuckDB on Windows may require the Microsoft Visual C++ Redistributable. A ZIP download is also available from the official installation page.

### macOS

```bash
brew install duckdb
```

### Linux

Review the installation script, and then run the official installer:

```bash
curl https://install.duckdb.org | bash
```

### Python

The Python package includes the database engine:

```bash
python -m pip install duckdb
```

### Docker

DuckDB normally does not need Docker, but an official image is useful for an isolated CLI:

```bash
docker run --rm -it -v "${PWD}:/workspace" -w /workspace duckdb/duckdb
```

## Create a local database

From this folder, create or open a persistent database file:

```bash
mkdir data
duckdb data/local.duckdb
```

At the DuckDB prompt, try:

```sql
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name VARCHAR NOT NULL,
    price DECIMAL(10, 2)
);

INSERT INTO products VALUES (1, 'Keyboard', 49.99);
SELECT * FROM products;
```

Enter `.quit` to close the CLI. Opening `data/local.duckdb` again restores the same database.

## Future MCP server configuration

A DuckDB MCP server will normally need only the database file path:

```env
DUCKDB_PATH=/absolute/path/to/mcp-servers/DuckDB/data/local.duckdb
```

Recommended MCP tools include listing tables, describing schemas, running read-only queries, importing local data files, and guarded create/update/delete operations.

## Local safety

- Keep private database files out of source control.
- Back up the `.duckdb` file before allowing write operations.
- Prefer read-only MCP tools for analytical workflows.
- Do not let untrusted users supply unrestricted file paths or SQL.

## Official resources

- [DuckDB installation](https://duckdb.org/docs/installation)
- [DuckDB command-line client](https://duckdb.org/docs/api/cli)
- [DuckDB Python client](https://duckdb.org/docs/current/guides/python/install)
- [DuckDB documentation](https://duckdb.org/docs/)
