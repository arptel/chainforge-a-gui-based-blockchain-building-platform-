# ChainForge — Learning Topic Tracker

Mark topics as you complete them: [ ] = pending, [/] = in progress, [x] = done

---

## Core Blockchain Engine (chain_core)

- [ ] **Topic 1: What is ChainForge?** *(The Big Picture)*
  - What problem does it solve?
  - Two halves: the platform that builds chains vs. the chain that gets built
  - Overall architecture overview

- [ ] **Topic 2: The Blockchain Data Structures** *(core/block.py, core/chain.py)*
  - Block fields (index, transactions, timestamp, previous_hash, nonce, hash)
  - `compute_hash()` — SHA-256 via Python's built-in `hashlib`
  - Genesis block
  - How blocks are linked (chain of hashes)

- [ ] **Topic 3: Cryptographic Security** *(core/crypto.py)*
  - ECDSA + secp256k1 curve (same as Bitcoin)
  - Used the **`ecdsa` Python library** — no manual math
  - Public/private keypairs, signing, and verification

- [ ] **Topic 4: The Mempool** *(core/mempool.py)*
  - What is a mempool and why it exists
  - Nonce tracking — replay attack prevention
  - Gas price priority ordering
  - Thread-safety with `threading.Lock`

- [ ] **Topic 5: Consensus Mechanisms** *(modules/consensus/)*
  - 9 algorithms supported: PoW, PoA, PoS, PBFT, Raft, HotStuff, Tendermint, Paxos, None
  - **PoW** — mining loop written from scratch (`hashlib` + `while True`), no library
  - **PoA** — checks `auth_role_` keys in chain state, instant sealing
  - Common `ConsensusInterface` that all modules implement

- [ ] **Topic 6: The Merkle Tree** *(core/merkle.py)*
  - Purpose: tamper-proof transaction fingerprint per block
  - Written entirely from scratch using only `hashlib`
  - Build process: leaf → parent → root
  - Merkle proofs and `verify_merkle_proof`
  - Bitcoin-style odd-leaf duplication

- [ ] **Topic 7: The State Machine & VM** *(modules/vm/python_vm.py)*
  - What "state" means in a blockchain (key-value dict)
  - State transitions via transactions
  - Smart contract sandboxing: AST inspection (`ast` module) + restricted builtins
  - Gas metering using `sys.settrace()`
  - Two execution modes: pre-deployed contracts vs. raw dynamic code

- [ ] **Topic 8: The P2P Network** *(modules/network/p2p.py)*
  - WebSockets via `websockets` library + FastAPI
  - Gossip protocol
  - Message types: `NEW_BLOCK`, `NEW_TRANSACTION`, `PEER_DISCOVERY`, `SYNC_REQUEST`, `SYNC_RESPONSE`
  - Outbound connections in background daemon threads

- [ ] **Topic 9: Chain Synchronization** *(modules/sync/full.py)*
  - How a new node catches up
  - Gap detection
  - Chain reorganization (reorg)
  - Fork resolution: finding the common ancestor, replacing invalid suffix
  - State replay from scratch after reorg

- [ ] **Topic 10: Persistence** *(core/persistence.py)*
  - Blocks stored on disk via SQLite (Python built-in `sqlite3`)
  - `load_from_disk()` / `save_block()` on node restart

- [ ] **Topic 11: Node Startup & Dependency Injection** *(main.py, di.py)*
  - How everything wires together at startup
  - `DependencyInjector` reads `genesis.json` → instantiates the right Consensus, VM, Network, Sync
  - Mining loop, API server, and network server run in separate threads

---

## The ChainForge Platform

- [ ] **Topic 12: Platform Backend** *(platform-backend/)*
  - FastAPI backend: user auth (JWT), project CRUD (SQLAlchemy + SQLite)
  - `ChainBuilder.build_package()` — filters modules, injects genesis.json, bundles contracts, generates ZIP

- [ ] **Topic 13: Smart Contracts System** *(modules/smart_contracts/ + Contract_registry.py)*
  - 20 pre-built system contracts (NativeToken, CertificateAuthority, MultiSig, etc.)
  - `Contract_registry.py` maps config choices to the right contracts
  - Solidity transpiler (LLM-assisted)
  - Auto-generated HTTP API routes per contract

- [ ] **Topic 14: The Generated SDK** *(sdk/client.py, sdk/base_client.js)*
  - Python `Client` class auto-wraps each contract
  - JS `ChainForgeClient` uses SPV light client + JavaScript `Proxy` objects
  - What is SPV (Simplified Payment Verification)?

- [ ] **Topic 15: The Frontend** *(platform-frontend/)*
  - Next.js UI: blockchain configurator wizard, Monaco code editor
  - Smart contract management panel
  - Download button → triggers the full build pipeline
