# MongoDB MCP Server

This folder is intended for an MCP server that connects AI clients to a local MongoDB deployment. The server code has not been added yet. This guide explains MongoDB and how to prepare a local Community Edition database.

## What is MongoDB?

MongoDB is a document database. Instead of storing every record as a row with a fixed set of columns, it stores BSON documents in collections. BSON is a binary representation of JSON-like data and supports types such as dates, decimals, and binary values.

MongoDB runs as a database service. Local applications and a future MCP server connect to it over the MongoDB protocol, normally through `mongodb://localhost:27017`.

## Technology overview

| Area | MongoDB approach |
|---|---|
| Data model | BSON documents grouped into collections |
| Architecture | Client-server document database |
| Query tools | MongoDB Query API and aggregation pipelines |
| Schema | Flexible, with optional schema validation |
| Scaling | Replica sets and horizontal sharding |
| Default local port | `27017` |

## Strengths

- Flexible documents work well when records do not all have identical fields.
- Nested objects and arrays can be stored naturally.
- Rich indexes, text search, geospatial queries, and aggregation pipelines.
- Good language-driver support and a large developer ecosystem.
- Replica sets provide high availability when moving beyond a single local node.
- Horizontal scaling is available for large distributed workloads.

## Good use cases

- Product catalogs with different attributes by product type.
- Content management, user profiles, and application settings.
- Event data, device data, and JSON-heavy APIs.
- Rapid prototypes where the data model changes frequently.
- Local development for applications that use MongoDB in production.

MongoDB is not always the best choice when the data depends on many relational joins or strict cross-table constraints. PostgreSQL or MySQL may make those relationships easier to model and enforce.

## Install locally

Use MongoDB Community Edition for local development.

### Windows

1. Download the Community Edition MSI from the MongoDB Download Center.
2. Run the installation wizard and choose **Complete** for a normal development setup.
3. Select **Install MongoD as a Service** so the database starts automatically.
4. Install `mongosh` separately if the selected package does not include it.

The official Windows guide lists supported Windows versions and explains both service and manual installation.

### macOS

MongoDB provides an official Homebrew tap. The following example installs MongoDB Community 8.0, the version used by the linked installation guide:

```bash
brew tap mongodb/brew
brew update
brew install mongodb-community@8.0
brew services start mongodb-community@8.0
```

Choose a different versioned formula if your application targets another supported MongoDB release.

### Ubuntu or Debian

MongoDB publishes its own `mongodb-org` packages. Follow the official instructions for your exact operating-system release to add the signing key and repository, then install:

```bash
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
```

Do not substitute Ubuntu's similarly named `mongodb` package; MongoDB states that it is not the official package and can conflict with `mongodb-org`.

### Docker

For a simple local instance without authentication:

```bash
docker run -d --name local-mongodb -p 27017:27017 -v mongodb_data:/data/db mongo
```

This is convenient for local experiments only. Configure authentication before using MongoDB with sensitive data or exposing it outside the local machine.

## Create a local database

Connect with the MongoDB shell:

```bash
mongosh mongodb://localhost:27017
```

Then create data. MongoDB creates the database and collection when the first document is inserted:

```javascript
use local_mcp

db.products.insertOne({
  name: "Keyboard",
  price: 49.99,
  active: true
})

db.products.find({ active: true })
```

## Future MCP server configuration

A local MongoDB MCP server will normally use a connection URI and database name:

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=local_mcp
```

Recommended MCP tools include listing collections, inspecting sample document shapes, finding documents, running safe aggregations, and guarded insert/update/delete operations.

## Local safety

- Bind a development server to localhost unless remote access is required.
- Enable authentication before storing sensitive information.
- Use a dedicated application user instead of an unrestricted administrator.
- Back up important collections before enabling MCP write tools.
- Validate collection names, filters, projections, and update operators in server code.

## Official resources

- [MongoDB installation guide](https://www.mongodb.com/docs/manual/installation/)
- [Install MongoDB Community Edition on Windows](https://www.mongodb.com/docs/v8.0/tutorial/install-mongodb-on-windows/)
- [Install MongoDB Community Edition on macOS](https://www.mongodb.com/docs/v8.0/tutorial/install-mongodb-on-os-x/)
- [Install MongoDB Community Edition on Ubuntu](https://www.mongodb.com/docs/v8.0/tutorial/install-mongodb-on-ubuntu/)
- [MongoDB manual](https://www.mongodb.com/docs/manual/)
