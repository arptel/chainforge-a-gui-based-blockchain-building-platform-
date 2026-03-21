# LOGICAL VERIFICATION AUDIT

## 1. PERMISSION ENFORCEMENT
**FINDINGS:** 
- **Check `POST /nodes`**: The `add_node` endpoint in `main.py` contains comments explicitly mentioning `# Check max_nodes limit`, `# permissioned network rules`, and `# Validate role against config.node_roles`. However, this check is **not actually implemented**; it is entirely a stub (`pass`).
- **Check `POST /transaction`**: The `submit_transaction` endpoint has a stub comment `# - Check permissions at backend` and `# - Permission matrix checks` but lacks any actual code to check governance type or reject unauthorized roles with a 403.
**SEVERITY:** CRITICAL

---

## 2. REAL PROCESS SPAWNING
**FINDINGS:**
- **In `process_manager/`**: The `ManagedProcess` dataclass is defined and type-hints `subprocess: subprocess.Popen`.
- However, the `spawn_node_process` method does **not** actually execute `subprocess`, `spawn`, or any system-level command. There is a `TODO: Implement process spawning with ... subprocess.Popen() call`. 
- It does not assign a real port dynamically (just accepts a `port` int argument).
- It does not actually wait for a ready signal, though it mentions it in comments (`# - Ready signal wait logic`).
- The `monitor_process` stub mentions detecting unexpected exit codes and triggering `NODE_OFFLINE`, but this logic does not exist.
**SEVERITY:** CRITICAL

---

## 3. WEBSOCKET EVENT BRIDGE
**FINDINGS:**
- **Subscribe to events:** The `EventBridge.subscribe_to_adapter_events` method is an empty stub. It does not actually ingest real feeds.
- **Reconnect Mechanism:** The frontend `WebSocketClient` has a `_attemptReconnect` method referencing exponential backoff, but it's just a `# TODO` stub. 
- **Event Normalization:** The `ChainEvent` dataclass expects `{ type, timestamp, nodeId, payload }`, but the loop to process these (`on_chain_event`) is fully stubbed.
**SEVERITY:** CRITICAL

---

## 4. CONSENSUS LOGIC CORRECTNESS
**FINDINGS:**
- **PBFT adapter:** `f` is calculated as `floor((n-1)/3)` in comments. The 3 phases (Pre-Prepare, Prepare, Commit) are correct. **Missing:** It does *not* explicitly mention requiring 2f+1 votes to commit.
- **Raft adapter:** The term number is explicitly referenced (`current_round: 7, // Raft term`). Leader election is mentioned. Majority quorum (n/2+1) is referenced (`# Display: "Quorum: majority ({N} of {total}) required"`).
- **Tendermint adapter:** 4 phases are correctly identified (Propose, Prevote, Precommit, Commit). The 2/3+ quorum is accurately referenced.
- **HotStuff adapter:** QC (Quorum Certificate) is mentioned successfully. The pipelined round structure is referenced.
- **None adapter:** Mentions skipping all voting/consensus and explicitly calls for the yellow warning banner.
**SEVERITY:** OK (For the theoretical knowledge inside comments) / MAJOR (For missing PBFT 2f+1 vote check and total lack of execution logic).

---

## 5. SYNC MODE HANDLING
**FINDINGS:**
- **Backend:** `config_parser.py` loads `sync_mode`, but `spawn_node` stubs do not pass this flag to a process. `SYNC_PROGRESS` and `SYNC_COMPLETE` emitting is stubbed out.
- **Frontend (`sync-events.js`):** The code mentions `# - Animate sync streams based on sync_mode`. However, it completely **misses** specifying the exact visual requirements (Full: streaming blocks, Light: headers + proof verification, Snapshot: counter jump, Batch: wave animation) requested by the spec.
**SEVERITY:** MAJOR

---

## 6. METRICS DASHBOARD
**FINDINGS:**
- **Spec Requirements:** TPS, Block time (avg), Consensus latency, Node count, Fault tolerance.
- **Frontend State:** `app.js` initializes `metrics` holding `totalNodes`, `totalBlocks`, `totalTransactions`, `currentTPS`, and `consensusType`.
- **Missing Metrics:** It entirely **misses** `average_block_time`, `consensus_latency` (TX broadcast to Commits), and `fault_tolerance` in its state initialization!
- **Calculation Mechanism:** The entire calculation process is a stub. TPS is not actually calculated from real `BLOCK_COMMITTED` events, and consensus latency is completely absent from the logical scaffold.
**SEVERITY:** CRITICAL (Missing required metric fields natively from the application state)
