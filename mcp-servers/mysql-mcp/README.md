# MySQL MCP Server

This folder is intended for an MCP server that connects AI clients to a local MySQL database. The server code has not been added yet. This guide explains MySQL and how to prepare a local MySQL Community Server.

## What is MySQL?

MySQL is a relational database management system. It stores structured data in tables and uses SQL for queries and data changes. Applications connect to a running MySQL server, normally over TCP.

InnoDB is the standard storage engine for most MySQL applications. It provides transactions, row-level locking, foreign keys, and crash recovery.

## Technology overview

| Area | MySQL approach |
|---|---|
| Data model | Relational tables and SQL |
| Architecture | Client-server database |
| Transactions | ACID transactions with InnoDB |
| Data integrity | Types, indexes, constraints, and foreign keys |
| Administration | MySQL Shell, `mysql` client, and MySQL Workbench |
| Default local port | `3306` |

## Strengths

- Mature, widely supported, and familiar to many developers.
- Strong performance for common web and business applications.
- Reliable transactions and indexing through InnoDB.
- Excellent support from programming languages, frameworks, and hosting tools.
- Replication and high-availability options for larger deployments.
- MySQL Workbench provides a graphical interface for development and administration.

## Good use cases

- Web applications, content systems, and e-commerce sites.
- Customer, order, inventory, and account data.
- Applications that need transactions and clear relationships.
- Local development that should closely match a MySQL production system.
- Teams already using the MySQL ecosystem or compatible tools.

For embedded, single-file storage, SQLite is simpler. For advanced extensibility or complex analytical SQL, PostgreSQL or DuckDB may be a better fit.

## Install locally

Install MySQL Community Server rather than an Enterprise edition unless you specifically need commercial features.

### Windows

Download MySQL Community Server from the official site. Current releases provide an MSI or ZIP package and MySQL Configurator. MySQL 8.0 also has the all-in-one MySQL Installer, which can install the server, MySQL Shell, and MySQL Workbench.

During setup:

1. Select a development configuration.
2. Keep TCP port `3306` unless it conflicts with another service.
3. Choose a strong root password.
4. Configure MySQL as a Windows service.
5. Create a separate application user after installation.

### macOS

Download the Community Server DMG from the official MySQL downloads page, open it, and run the package installer. The installer can configure the server to start automatically.

### Ubuntu or Debian

The distribution package is suitable for many local development environments:

```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl enable --now mysql
```

Use the official MySQL APT repository when you need a specific MySQL release that is not supplied by your distribution.

### Docker

Create a persistent local server with a named volume:

```bash
docker run -d --name local-mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=change-this-password -e MYSQL_DATABASE=local_mcp -v mysql_data:/var/lib/mysql mysql
```

Do not use the example password for real data.

## Create a local database and user

Connect as the local administrator:

```bash
mysql -u root -p
```

Create a database and a limited local user:

```sql
CREATE DATABASE local_mcp CHARACTER SET utf8mb4;
CREATE USER 'mcp_user'@'localhost' IDENTIFIED BY 'replace-with-a-strong-password';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX
    ON local_mcp.* TO 'mcp_user'@'localhost';
FLUSH PRIVILEGES;
```

Test the new account:

```bash
mysql -u mcp_user -p local_mcp
```

## Future MCP server configuration

A local MySQL MCP server will normally need these settings:

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=local_mcp
MYSQL_USER=mcp_user
MYSQL_PASSWORD=replace-with-a-strong-password
```

Recommended MCP tools include listing tables, describing schemas, parameterized reads, and guarded create/update/delete operations. The server should use a connection pool and should never build SQL by directly joining untrusted text.

## Local safety

- Do not connect the MCP server as `root`.
- Store passwords in environment variables or a secrets manager, not source control.
- Keep the server bound to localhost unless remote access is intentional.
- Grant only the permissions required by the available MCP tools.
- Back up important databases before enabling write or schema-change tools.

## Official resources

- [Getting started with MySQL](https://dev.mysql.com/doc/mysql-getting-started/en/)
- [MySQL Community downloads](https://dev.mysql.com/downloads/)
- [MySQL Installer for Windows](https://dev.mysql.com/downloads/installer/)
- [MySQL Reference Manual](https://dev.mysql.com/doc/refman/en/)
