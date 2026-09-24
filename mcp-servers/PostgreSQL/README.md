# PostgreSQL MCP Server

This folder is intended for an MCP server that connects AI clients to a local PostgreSQL database. The server code has not been added yet. This guide explains PostgreSQL and how to prepare a local database for future MCP integration.

## What is PostgreSQL?

PostgreSQL, often called Postgres, is an open-source relational database. It uses SQL, supports reliable ACID transactions, and is known for correctness, extensibility, and advanced query features.

PostgreSQL runs as a database service. Local tools and an MCP server connect to it over TCP or a local socket.

## Technology overview

| Area | PostgreSQL approach |
|---|---|
| Data model | Relational tables, SQL, JSONB, arrays, and custom types |
| Architecture | Client-server database |
| Transactions | ACID transactions with multi-version concurrency control |
| Extensibility | Extensions, functions, operators, and custom types |
| Administration | `psql`, pgAdmin, and other database clients |
| Default local port | `5432` |

## Strengths

- Strong data integrity, transactions, and standards-oriented SQL.
- Advanced joins, common table expressions, window functions, and indexing.
- JSONB supports document-style data alongside relational tables.
- Extensions add capabilities such as PostGIS for geographic data.
- Handles concurrent readers and writers well.
- Large open-source ecosystem with drivers for most programming languages.

## Good use cases

- Business systems with connected data and important constraints.
- APIs, web applications, and software-as-a-service products.
- Financial, customer, order, and inventory systems.
- Geographic applications using PostGIS.
- Applications that combine structured tables with JSON documents.
- Local development that may later grow into a larger production service.

PostgreSQL requires more setup than an embedded database such as SQLite or DuckDB. For a tiny application that only needs one local file, an embedded database may be simpler.

## Install locally

### Windows

Use the installer linked from the official PostgreSQL Windows download page. The standard installer includes:

- PostgreSQL Server
- `psql`
- pgAdmin
- StackBuilder for optional tools and drivers

During setup, remember the password selected for the `postgres` administrator account and keep the default port `5432` unless it is already in use.

### macOS

The official download page lists the graphical installer, Postgres.app, and Homebrew. A Homebrew installation can be started with:

```bash
brew install postgresql
brew services start postgresql
```

Homebrew may expose a versioned formula such as `postgresql@18`. Use the formula shown by `brew search postgresql` for the version you want.

### Ubuntu or Debian

PostgreSQL is available through the operating system package manager:

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl enable --now postgresql
```

The PostgreSQL project also provides its own APT repository when a different supported version is required.

### Docker

Create a persistent local server with a named volume:

```bash
docker run -d --name local-postgres -p 5432:5432 -e POSTGRES_PASSWORD=change-this-password -e POSTGRES_DB=local_mcp -v postgres_data:/var/lib/postgresql/data postgres
```

Do not use the example password for real data.

## Create a local database and user

Open `psql` as the PostgreSQL administrator. On many Linux systems:

```bash
sudo -u postgres psql
```

Create a login and database:

```sql
CREATE ROLE mcp_user WITH LOGIN PASSWORD 'replace-with-a-strong-password';
CREATE DATABASE local_mcp OWNER mcp_user;
```

Test the connection:

```bash
psql "postgresql://mcp_user@localhost:5432/local_mcp"
```

## Future MCP server configuration

A PostgreSQL MCP server can use one connection URL:

```env
POSTGRES_URL=postgresql://mcp_user:replace-with-a-strong-password@127.0.0.1:5432/local_mcp
```

Alternatively, keep the host, port, database, user, and password in separate environment variables. Recommended MCP tools include schema discovery, parameterized read queries, and carefully permissioned data or schema changes.

## Local safety

- Do not run the MCP server as the `postgres` superuser.
- Use a dedicated role with only the permissions its tools require.
- Store credentials outside source control.
- Keep the database listening on localhost for local-only work.
- Consider a read-only role when the MCP server only needs to inspect data.
- Back up important databases before enabling destructive tools.

## Official resources

- [PostgreSQL downloads](https://www.postgresql.org/download/)
- [PostgreSQL Windows installer](https://www.postgresql.org/download/windows/)
- [PostgreSQL macOS packages](https://www.postgresql.org/download/macosx/)
- [PostgreSQL documentation](https://www.postgresql.org/docs/)
