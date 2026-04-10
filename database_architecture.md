# Database Architecture Overview

This document details the database technology used across the three main sections of the project, including schemas and the architectural reasoning behind these choices.

---

## 1. ChainForge Platform (Backend)

**Database Used:** `SQLite` (managed via `SQLAlchemy` ORM)
**File Location:** `chainforge/platform-backend/chainforge.db`

### Tables and Schema

**Table: `users`**
- `id` (Integer, Primary Key) - Auto-incrementing unique identifier.
- `username` (String, Unique) - The user's chosen display name.
- `email` (String, Unique) - The user's email address.
- `hashed_password` (String) - Bcrypt hashed password for security.
- `created_at` (DateTime) - Timestamp of when the account was created.

**Table: `projects`**
- `id` (Integer, Primary Key) - Auto-incrementing unique identifier.
- `name` (String) - Name of the project.
- `description` (String, nullable) - Optional description of the smart contract/project.
- `owner_id` (Integer, Foreign Key) - Links back to `users.id`.
- `created_at` (DateTime) - Timestamp of project creation.
- `updated_at` (DateTime) - Timestamp of last modification.
- `config` (JSON) - Stores blockchain compilation configurations.

### Why this database was chosen
ChainForge functions like a local IDE (Integrated Development Environment) for building and compiling smart contracts. We chose **SQLite** because it is a **zero-configuration** database. 
If we used a heavier database like MySQL or PostgreSQL, any developer or user who downloads ChainForge would have to install a database server, configure a username, set up a password, and make sure the database is running in the background before they could even boot up the platform. 
By using SQLite, the entire database is self-contained in a single lightweight `.db` file. We paired this with **SQLAlchemy (an ORM)** so that if production demands a heavier database in the future, we only need to change one line of connection code rather than rewriting all SQL queries.

---

## 2. Certificate Verification System (Certi Verifi Sys)

**Database Used:** `SQLite` (Native driver)
**File Location:** `certificate_verification_system/data/users.sqlite`

### Tables and Schema

**Table: `users`**
- `username` (Text, Primary Key) - The name of the college or university (e.g., "MIT").
- `password` (Text) - Login credential.
- `blockchain_address` (Text) - The elliptic curve public address matching the issuer.
- `private_key` (Text) - Hex string of the private key used to sign certificates.
- `role` (Text) - E.g., "ISSUER".
- `node_url` (Text) - The local HTTP port/URL where this college's blockchain node is hosted.
- `db_path` (Text) - Path pointing to where this particular node saves its ledger.

### Why this database was chosen
The Certificate Verification System acts as a bridge between users (colleges, employers) and the underlying peer-to-peer blockchain network. It needs to keep track of which college controls which blockchain node. 
We chose **SQLite** here for its **portability during demonstrations**. A major goal of this module is to easily present its capabilities (e.g., in a viva or physical tech demo). Because SQLite is bundled directly with Python, the entire verification system (complete with registered colleges and cryptographic keys) can be launched on any Windows or Linux machine instantly via a single `start_services.ps1` script without worrying about external database dependencies or firewall permission issues.

---

## 3. Simulation & Blockchain Nodes

**Database Used:** `SQLite` (Native driver)
**File Location:** Dynamically generated for each node (e.g., `Simulator/data/node_8000/chainforge.db`)

### Tables and Schema

**Table: `blocks`**
- `idx` (Integer, Primary Key) - The block height/index in the chain.
- `hash` (Text) - The cryptographic SHA-256 hash of the block.
- `data` (Text) - A heavily nested JSON payload containing the transactions, miner data, nonce, and previous hash.

**Table: `state`**
- `key` (Text, Primary Key) - The identifier, either a wallet address or a smart contract variable (e.g., `cert_CERT-1234`).
- `value` (Text) - The actual JSON serialized data (e.g., representing a balance of 100, or a revoked certificate status).

### Why this database was chosen
In the real world, blockchain clients like Ethereum or Bitcoin use localized key-value stores (like LevelDB or RocksDB). Initially, our simulation relied on simple `blocks.json` and `state.json` text files. However, those files became notoriously "fragile".

If you are simulating a network and a "power outage" occurs (the user suddenly kills the script or node), raw JSON files tend to corrupt easily, destroying the entire ledger. We upgraded to **SQLite** here because it provides **ACID (Atomicity, Consistency, Isolation, Durability) guarantees**. 
With SQLite:
1. **Durability:** Changes are committed transactionally. If a node is shut down mid-write, SQLite rolls back to a safe ledger state upon restarting.
2. **Independent Ledgers:** We simulate 5 to 10 nodes on a single laptop. Instead of setting up 10 massive Dockerized databases, we simply generate 10 separate `.db` files on disk. Each node queries its own isolated ledger rapidly without locking up the other nodes.
