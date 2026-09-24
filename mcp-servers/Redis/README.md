# Redis MCP Server

This folder is intended for an MCP server that connects AI clients to a local Redis deployment. The server code has not been added yet. This guide explains Redis and how to prepare a local Redis instance.

## What is Redis?

Redis is an in-memory data store. It keeps working data in memory for very fast access and provides data structures such as strings, hashes, lists, sets, sorted sets, streams, and JSON-capable structures in current Redis Open Source releases.

Redis is commonly used beside a primary database rather than instead of one. It can persist data to disk, but its memory-first design and operational behavior are different from a relational database.

## Technology overview

| Area | Redis approach |
|---|---|
| Data model | Keys mapped to specialized data structures |
| Architecture | Client-server, primarily in memory |
| Query style | Redis commands rather than SQL |
| Persistence | Optional snapshots and append-only files |
| Messaging | Pub/Sub and durable streams |
| Default local port | `6379` |

## Strengths

- Very low-latency reads and writes.
- Built-in expiration makes temporary data easy to manage.
- Useful structures for counters, rankings, queues, streams, and sets.
- Atomic commands simplify many concurrency problems.
- Pub/Sub supports real-time notifications.
- Broad client-library support across programming languages.

## Good use cases

- Application caches and API response caches.
- Login sessions, temporary tokens, and rate limiting.
- Counters, leaderboards, and real-time statistics.
- Background job queues and event streams.
- Pub/Sub messaging and live notifications.
- Fast retrieval of short-lived context for local AI applications.

Redis is not a direct replacement for a relational database when data needs joins, foreign keys, or complex durable transactions. Always choose and test a persistence policy if Redis will hold data that cannot be recreated.

## Install locally

### Windows

The current official Redis Open Source guidance supports Windows through Docker. Install Docker Desktop, configure it to use Linux containers, and run:

```powershell
docker run -d --name local-redis -p 6379:6379 -v redis_data:/data redis redis-server --appendonly yes
```

Native Windows-compatible alternatives exist, but confirm their licensing and compatibility before choosing one. Redis also documents Memurai as its Windows compatibility partner.

### macOS

```bash
brew install redis
brew services start redis
```

### Ubuntu or Debian

For a basic distribution-provided installation:

```bash
sudo apt update
sudo apt install redis-server redis-tools
sudo systemctl enable --now redis-server
```

The Redis documentation also explains how to add the official Redis APT repository when the latest supported release is required.

### Docker on any supported platform

```bash
docker run -d --name local-redis -p 6379:6379 -v redis_data:/data redis redis-server --appendonly yes
```

The named volume and append-only mode retain local data across container replacement. Persistence behavior should still be reviewed before relying on Redis as a system of record.

## Test the local server

Open the Redis command-line client:

```bash
redis-cli
```

Test the connection and add a small record:

```text
PING
HSET customer:1 name "Olivia Miller" city "Seattle" status "active"
HGETALL customer:1
EXPIRE customer:1 3600
```

`PING` should return `PONG`. The example customer expires after one hour because of the `EXPIRE` command.

## Future MCP server configuration

A local Redis MCP server will normally use a connection URL:

```env
REDIS_URL=redis://127.0.0.1:6379/0
```

Recommended MCP tools include reading a key, inspecting its type and time-to-live, scanning keys with strict limits, and guarded operations for common data structures. Avoid exposing unrestricted `KEYS`, `FLUSHDB`, `FLUSHALL`, or arbitrary command execution.

## Local safety

- Keep Redis bound to localhost unless remote access is intentionally secured.
- Add authentication and TLS before allowing access from other machines.
- Never expose port `6379` directly to the public internet.
- Use key prefixes so the MCP server operates only on its intended data.
- Limit scans and response sizes; one Redis value can be very large.
- Back up persistent data before enabling delete or expiry-changing tools.

## Official resources

- [Install Redis Open Source](https://redis.io/docs/latest/operate/oss_and_stack/install/)
- [Redis installation options and Docker quick start](https://redis.io/docs/latest/operate/oss_and_stack/install/install-stack/)
- [Install Redis CLI](https://redis.io/docs/latest/operate/oss_and_stack/install/install-stack/install-redis-cli/)
- [Redis documentation](https://redis.io/docs/latest/)
