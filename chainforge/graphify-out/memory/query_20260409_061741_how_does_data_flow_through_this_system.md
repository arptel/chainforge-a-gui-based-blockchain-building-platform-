---
type: "query"
date: "2026-04-09T06:17:41.607507+00:00"
question: "How does data flow through this system?"
contributor: "graphify"
source_nodes: ["Blockchain", "P2PNetwork", "DependencyInjector", "ConsensusInterface", "NetworkInterface", "SyncInterface", "VMInterface", "Persistence"]
---

# Q: How does data flow through this system?

## Answer

Data flows through this system in three main stages. First, user and project data enters through the platform backend: auth and project routes call CRUD and schema layers such as register/login in platform-backend/routers/auth.py, project creation in platform-backend/routers/projects.py, and generator endpoints in platform-backend/routers/generate.py. Second, generated blockchain runtime data flows through the chain core: transactions are accepted by Blockchain.add_transaction in templates/chain_core/core/chain.py, validated and staged in the mempool in templates/chain_core/core/mempool.py, executed through a VM implementation like PythonVM, EVMRuntime, WASMRuntime, or VyperRuntime under templates/chain_core/modules/vm/, and then assembled into blocks through consensus modules implementing ConsensusInterface. Third, block and state data propagates outward through networking and sync: P2PNetwork broadcasts transactions and blocks in templates/chain_core/modules/network/p2p.py, sync modules such as FullSync, FastSync, LightSync, RealtimeSync, BatchSync, and SnapshotSync reconcile remote state, and Persistence stores and reloads blocks and state in templates/chain_core/core/persistence.py. The graph also shows DependencyInjector in test_generated_blockchain/di.py as the main wiring point connecting consensus, network, sync, and runtime modules together.

## Source Nodes

- Blockchain
- P2PNetwork
- DependencyInjector
- ConsensusInterface
- NetworkInterface
- SyncInterface
- VMInterface
- Persistence