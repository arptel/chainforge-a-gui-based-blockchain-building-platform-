# Presentation 2: Implementation Progress Review
**Group – IBC04**  
**ChainForge: A GUI-Based Blockchain Building Platform**

> **Target:** 20–25 March 2026 | Objective: *"Are you creating something real?"*

---

## SLIDE 1 — Title Slide

**Title:** ChainForge – Implementation Progress Review  
**Subtitle:** A GUI-Based Platform for Rapid Blockchain Creation  
**Team:** Arth Patel · Akshat Patel · Jay Shah · Jainik Patel  
**Course:** CSE542 – Introduction to Blockchain  

---

## SLIDE 2 — Brief Recap of Project Goal

**One-line goal:**  
Build a platform that lets any developer configure, generate, and deploy a production-grade blockchain network — without writing low-level distributed-systems code.

**Problem it solves:**
- Building a blockchain from scratch requires expertise in cryptography, networking, consensus theory, and distributed systems
- Existing platforms (Ethereum, Hyperledger) are opinionated and hard to customise
- ChainForge lowers this barrier to a GUI + download

**What we promised in Presentation 1:**
- A web-based configuration dashboard
- A code-generation backend that injects user choices into generic node templates
- A downloadable, runnable blockchain node package
- Smart contract support with a sandboxed execution environment

**Status heading into Presentation 2:**  
→ All core modules are implemented and running end-to-end

---

## SLIDE 3 — Finalized Architecture

*(Include updated Architecture Diagram)*

**Three-tier layout:**

```
[USER BROWSER]
      |
      | HTTPS / REST
      ↓
[PLATFORM FRONTEND]          ← Next.js / TypeScript / Tailwind CSS
      |
      | REST API calls
      ↓
[PLATFORM BACKEND]           ← Python / FastAPI + SQLite (chainforge.db)
  ├─ Auth Module             ← JWT-based user authentication
  ├─ CRUD (Projects/Users)   ← SQLAlchemy ORM
  ├─ Config Validator        ← validates genesis.json shape
  ├─ Code Generator          ← builder.py (templates → ZIP)
  └─ Solidity Transpiler     ← optional: Solidity → PythonVM contract
      |
      | User downloads ZIP → runs locally
      ↓
[GENERATED BLOCKCHAIN NETWORK]
  Node A (port 5000)  ←P2P→  Node B (port 5001)  ←P2P→  Node C (port 5002)
  ├─ P2P Network Layer (asyncio WebSockets)
  ├─ Consensus Module (pluggable: PoW / PoA / PoS / PBFT / Raft …)
  ├─ Mempool (gas-prioritised, nonce-tracked)
  ├─ VM / Runtime (Python VM / EVM-stub / WASM-stub)
  ├─ Blockchain Core (Block, Chain, Merkle Tree)
  └─ Persistence (SQLite via persistence.py)
```

**Key design decisions:**
- Platform Backend and Generated Nodes are **fully decoupled** — the platform only generates code; it does not run or control nodes
- Dependency Injection (`di.py`) wires all pluggable modules at node startup so the same binary supports any configuration

---

## SLIDE 4 — Logical Design (Refined)

*(Include a Sequence / Flow Diagram)*

**A. Platform "Forge" Workflow (user-facing)**

1. User registers / logs in → JWT issued by platform backend
2. User opens the **ChainForge Dashboard** → fills blockchain configuration (network type, consensus, sync mode, VM runtime, gas settings, smart contracts)
3. Frontend sends `POST /api/generate` with a `genesis.json` payload
4. **Config Validator** (`validator.py`) checks all required fields
5. **Builder** (`builder.py`) copies and patches template files, embeds the user's smart contract code, writes a `genesis.json` inside the package
6. ZIP file returned → user downloads and unzips

**B. Generated Node Lifecycle**

1. `python main.py --port 5000 --role full --peers <peer-ip>:5001`
2. Node reads `genesis.json` → maps config keys to concrete module classes via `DependencyInjector`
3. Consensus, Network, Sync, VM are wired together
4. API server starts (FastAPI, separate thread) → accepts external transactions
5. Network server starts (asyncio) → listens for P2P peers
6. Mining loop begins: every 5 s, if `pending_transactions` non-empty → `mine_pending_transactions()` → broadcast new block

**C. Transaction Processing Flow**

```
User/API → validate tx → Mempool.add() → P2P broadcast
                            ↓
                   Mining loop picks up
                            ↓
                   VM executes transactions
                            ↓
                   Block assembled (Merkle root, state root, SHA-256 hash)
                            ↓
                   Consensus validates (PoW: difficulty check, etc.)
                            ↓
                   Chain.add_block() → persist to SQLite
                            ↓
                   Broadcast new block to all peers
```

---

## SLIDE 5 — Blockchain Structure (Implemented)

**Block fields (from `core/block.py`):**

| Field | Type | Purpose |
|---|---|---|
| `index` | int | Sequential block number |
| `timestamp` | float | UNIX time of creation |
| `previous_hash` | str | Links to parent block (chain integrity) |
| `validator` | str | Miner / validator address |
| `nonce` | int | PoW solution / PoS slot number |
| `merkle_root` | str | SHA-256 Merkle root of all transactions |
| `state_root` | str | Root hash of VM state after execution |
| `hash` | str | SHA-256 over all fields above |

**Cryptographic guarantees:**
- `compute_hash()` → SHA-256 over `json.dumps(block_dict, sort_keys=True)` — tamper-evident
- Any change to any field invalidates the block hash and breaks the chain

**Merkle Tree (from `core/merkle.py`):**
- Binary Merkle tree built over all transactions in a block
- Bitcoin-style: odd leaf count → duplicate last leaf
- Supports `generate_merkle_proof()` and `verify_merkle_proof()` — enables **light-client SPV proofs**
- Proof path: leaf hash → sibling hashes → reconstructed root == block's `merkle_root`

**Persistence (`core/persistence.py`):**
- Blocks serialised to SQLite via `persistence.py`
- On node restart, `chain.load_from_disk()` rehydrates full chain state

---

## SLIDE 6 — Mempool: Transaction Queue (Implemented Detail)

*(This is a key technical slide — shows the depth of implementation)*

**What is the Mempool?**  
A thread-safe, in-memory transaction staging area between transaction submission and block mining.

**Implemented features (`core/mempool.py`):**

| Feature | How it works |
|---|---|
| **Nonce Tracking** | Each sender's last confirmed nonce is tracked; incoming nonce must be `> confirmed_nonce` |
| **Replay Attack Prevention** | Duplicate `(sender, nonce)` pairs are rejected outright |
| **Future Nonce Gating** | Nonces more than 10 ahead of expected are also rejected |
| **Gas Priority Ordering** | Transactions sorted by `gas_price` descending — higher-fee txs mined first |
| **Gas Floor** | Configurable `min_gas_price`; txs below floor are rejected |
| **Post-finality Cleanup** | After a block is mined, `mempool.remove(confirmed_txs)` prunes confirmed txs and updates nonce state |
| **Chain Reorg Support** | `set_confirmed_nonces()` bulk-resets state and prunes stale pending txs |

**Why this matters:** Without a proper mempool, nodes are vulnerable to double-spends, replay attacks, and mining loops that process the same transaction twice.

---

## SLIDE 7 — Smart Contracts Developed

**Two layers of smart contracts in ChainForge:**

### Layer 1 — System Contracts (Platform-Injected)
Automatically deployed based on configuration. Defined in `modules/smart_contracts/Contract_registry.py`:

| Category | Contract | Key Methods |
|---|---|---|
| Base (all networks) | `DataStore` | `add`, `get`, `exists` |
| Base | `Validation` | `validate`, `validateSignature` |
| Base | `AccessControl` | `grantRole`, `revokeRole`, `hasRole` |
| Base | `AuditLog` | `logAction`, `getLogs` |
| PoW | `MiningReward` | `claimReward`, `getReward` |
| PoA | `AuthorityManagement` | `addAuthority`, `removeAuthority` |
| PoS | `Staking` + `ValidatorElection` | `stake`, `unstake`, `electValidator` |
| Consortium | `ValidatorCouncil` + `MultiSig` + `CertificateAuthority` | `propose`, `approve`, `execute`, `issueCert`, `revokeCert` |
| Centralized | `AdminControl` + `Whitelist` | `approveNode`, `rotateLeader`, `isWhitelisted` |

### Layer 2 — User-Defined Contracts (Python VM Sandbox)
- Users write Python smart contract code in the ChainForge GUI editor
- Code is embedded into the generated node at build time
- Execution is sandboxed via **AST-based security** at runtime:
  - Forbidden imports blocked (`os`, `sys`, `subprocess`, etc.)
  - Forbidden builtins blocked (`exec`, `eval`, `open`, `__import__`)
  - Only whitelisted operations permitted → prevents arbitrary code execution on node hosts

---

## SLIDE 8 — Dependency Injection & Pluggability

*(Optional/bonus slide – shows architectural sophistication)*

**The `DependencyInjector` (`di.py`) wires the entire node at startup based on `genesis.json`:**

| Dimension | Supported Options |
|---|---|
| **Consensus** | `pow`, `pos`, `poa`, `pbft`, `raft`, `hotstuff`, `tendermint`, `paxos`, `none` |
| **Sync Mode** | `full`, `fast`, `light`, `snapshot`, `realtime`, `batch` |
| **VM Runtime** | `python` (PythonVM), `evm` (EVM-stub), `wasm` (WASM-stub) |
| **Network** | `p2p` (asyncio WebSocket) |

**Result:** The exact same generated node binary can run as a PoW public chain, a PBFT consortium, or a Raft-based centralised ledger — the user's GUI choice determines everything.

**Node roles also supported:** `full` (mine + validate), `miner` (mine only), `light` (passive, no mining)

---

## SLIDE 9 — Technology Stack Used

| Layer | Technology | Purpose |
|---|---|---|
| **Platform Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS | GUI dashboard for blockchain configuration |
| **Platform Backend** | Python 3.11+, FastAPI, SQLAlchemy, SQLite | REST API, user auth (JWT), code generation |
| **Code Generator** | Python (`builder.py`, `validator.py`) | Templates → ZIP packaging |
| **Solidity Bridge** | `solidity_transpiler.py` | Converts basic Solidity to PythonVM contracts |
| **Blockchain Core** | Python (stdlib only) | Block, Chain, Merkle tree, Mempool, Persistence |
| **Networking** | Python asyncio + WebSockets | P2P node-to-node communication |
| **Consensus** | Python modules (PoW, PoA, PoS, PBFT, Raft, HotStuff, Tendermint, Paxos) | Pluggable consensus algorithms |
| **VM Runtimes** | PythonVM (AST sandbox), EVM-stub, WASM-stub | Smart contract execution |
| **Storage** | SQLite (`chainforge.db`, per-node DB) | Platform state + block persistence |
| **Containerisation** | Dockerfile (per generated node) | Optional containerised deployment |

---

## SLIDE 10 — Code Overview & Implementation Highlights

**What is actually implemented and working:**

1. **`core/block.py`** — Full block structure with SHA-256, Merkle root, state root
2. **`core/chain.py`** — `Blockchain` class with `mine_pending_transactions()`, `add_block()`, `is_chain_valid()`
3. **`core/mempool.py`** — Gas-prioritised, nonce-tracked, replay-safe transaction pool
4. **`core/merkle.py`** — Full binary Merkle tree with proof generation and verification
5. **`core/persistence.py`** — SQLite load/save for blocks and chain state
6. **`modules/consensus/`** — 9 consensus algorithm stubs (PoW fully functional with difficulty/nonce iteration)
7. **`modules/network/p2p.py`** — asyncio-based P2P layer with `broadcast_block()`, `broadcast_transaction()`, peer discovery
8. **`modules/sync/`** — 6 sync strategies (FullSync operational: gap detection, block request, fork resolution)
9. **`modules/vm/python_vm.py`** — AST-sandboxed Python VM for smart contract execution
10. **`modules/smart_contracts/`** — 20 system Smart contracts across all network types
11. **`platform-backend/generator/builder.py`** — Template-injection code generator producing runnable ZIP packages
12. **`platform-frontend/`** — Full Next.js GUI with config wizard, smart contract editor, blockchain download

**Sync architecture (recent refactor):**
- Sync logic fully decoupled from P2P layer via `SyncInterface`
- Network calls `sync.sync_chain()` for gap fill; `sync.handle_new_block()` for live updates
- Fork resolution handled within the sync module itself — P2P layer stays transport-only

---

## SLIDE 11 — Test Results / Sample Inputs & Outputs

**Scenario tested: Multi-node PoW network with custom smart contract**

**Setup:**
- 3 nodes: Node A (miner, port 5000), Node B (full, port 5001), Node C (light, port 5002)
- Consensus: PoW | Sync: Full | VM: PythonVM | Signatures: required

**Flow verified:**

| Step | Result |
|---|---|
| POST `/transaction` to Node A API | `{"status": "queued", "tx_id": "..."}` |
| Mempool validates nonce + gas | `ok` — transaction added |
| 5-second mining loop fires | `[MINER NODE] Mining pending transactions...` |
| PoW solve (nonce iteration) | Block hash meets difficulty target |
| Block broadcast to peers B and C | Received and validated by both |
| Node B adds block to its chain | Chain height incremented |
| Node C (light) receives block header | Logged without mining |

**Smart contract execution verified:**
- Deployed custom `issue_certificate` contract via PythonVM
- Contract state (`certificates` dict) updated in block's state root
- AST sandbox correctly blocked `import os` attempt → `SecurityError` raised

**Transaction signature verification:**
- `requireSignature=true` in genesis.json → unsigned transactions rejected at mempool level

---

## SLIDE 12 — Challenges Faced

**1. Transaction Mining Pipeline Debugging**  
- *Issue:* "Transaction queued but not mined within 15 seconds" — valid transactions were being rejected during mining
- *Root cause:* Signature verification logic was re-running with wrong key format after mempool acceptance; mempool nonce state was not being reset correctly after chain reorg
- *Resolution:* Fixed signature check to only run at mempool entry; added `set_confirmed_nonces()` to handle post-reorg state cleanup

**2. Smart Contract Sandboxing**  
- *Issue:* Python's `exec()` gives full interpreter access — a contract could `import os` and destroy the host
- *Solution:* Pre-execution AST walk (`ast.parse()` → check all `Import` / `ImportFrom` nodes against allowlist); forbidden built-ins replaced with no-ops or removed from the sandbox `globals` dict
- *Added UX:* Warning banner in the smart contract editor listing restricted APIs

**3. Sync / Fork Resolution Coupling**  
- *Issue:* P2P layer was directly calling Blockchain methods to resolve forks — tight coupling made it impossible to swap sync strategies
- *Solution:* Introduced `SyncInterface` abstraction; P2P only calls `sync.handle_new_block()` and `sync.sync_chain()`; each sync module owns its own fork resolution logic (longest-chain rule for FullSync, header validation for LightSync)

**4. Config Mismatch Between Frontend and Backend**  
- *Issue:* `400 Bad Request` on ZIP download — frontend sending `publicConsensus` key; backend `ConfigValidator` expected flat `consensus`
- *Solution:* Backend now reads nested network-type keys (`publicConsensus`, `centralizedConsensus`, `consortiumConsensus`) and maps them to a single internal `consensus` key before template injection

---

## SLIDE 13 — What's Working vs. What's Remaining

**✅ Fully Working:**
- Platform Login / Register (JWT auth)
- Blockchain Configuration GUI (network type, consensus, sync mode, VM, gas settings)
- Smart Contract editor with AST security warning
- Code generation + ZIP download pipeline
- Generated node: block mining, mempool, Merkle tree, persistence, P2P broadcast
- Multi-node synchronisation (FullSync, BatchSync)
- PoW consensus (difficulty-based nonce search)

**🔄 In Progress / Partially Working:**
- PoS / PoA full implementation (stubs exist; election logic needs completion)
- EVM runtime (stub structure in place; full opcode execution not yet wired)
- Light-node SPV proof verification (Merkle proof code complete; light-node integration partial)

**📋 Remaining for Final Submission:**
- End-to-end stress test (10+ node network)
- Final UI polish (status dashboard showing live node info)
- Documentation / README for the generated node package

---

## SLIDE 14 — Conclusion & Next Steps

**Conclusion:**  
ChainForge is no longer a design — it's a running system. A user can open the web dashboard, configure a blockchain, download a ZIP, run three nodes, submit a transaction, and watch it get mined and broadcast across the network. The platform correctly separates the **control plane** (ChainForge backend) from the **data plane** (the generated nodes), and the pluggable DI architecture means the same codebase supports 9 consensus algorithms, 6 sync modes, and 3 VM runtimes without a single `if` branching on consensus type in the core business logic.

**Next Steps:**
- Complete PoS / PoA validator election logic
- Integrate EVM runtime for Solidity-compatible contracts
- End-to-end load testing with 10-node network
- UI dashboard: live node status, mempool size, block explorer
- Finalise project report and submit

---

*End of Presentation 2 — ChainForge | IBC04 | March 2026*
