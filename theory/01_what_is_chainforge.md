# Topic 1: What is ChainForge?

**Status:** [ ] Done

---

## The Problem It Solves

Building a blockchain from scratch is hard. You need to know:
- How hashing works
- How consensus algorithms work (PoW, PoA, PBFT…)
- How P2P networking works
- How smart contracts are executed
- How nodes sync with each other
- …and 10 more things

Most developers who want **their own blockchain** (e.g. for a university, a supply chain, a certificate system) don't want to learn all of that. They just want to **configure** what they need and get running code.

**ChainForge solves this** — it's a GUI platform where you pick your settings (consensus algorithm, sync mode, smart contracts, etc.) and it generates a fully working blockchain layer as a downloadable ZIP file.

---

## The Two Halves of ChainForge

The project has **two separate things** that often get confused:

```
ChainForge/
├── chainforge/                  ← THE PLATFORM (builds blockchains)
│   ├── platform-frontend/       │   Next.js GUI — the website you interact with
│   ├── platform-backend/        │   FastAPI server — generates the ZIP
│   └── templates/chain_core/    │   The master blockchain template code
│
└── certificate_verification_system/   ← A DEMO APP (uses a generated blockchain)
```

### Half 1: The Platform (`chainforge/`)
This is the "factory". You open the website, configure your blockchain, click Download, and get a ZIP file with working Python code.

### Half 2: The Generated Blockchain (`chain_core/` template)
This is the "product". Every ZIP file downloaded from the platform is a copy of this template, with:
- Only the chosen modules included (e.g. `pow.py` if you picked PoW)
- A `genesis.json` config file baked in
- Your smart contracts bundled in
- An auto-generated SDK (Python + JS) to interact with it

---

## What a Generated Blockchain Looks Like

When you download and unzip your blockchain, you get this structure:

```
my_blockchain/
├── main.py                  ← Entry point. Run this to start a node.
├── config/genesis.json      ← Your settings (consensus, gas, etc.)
├── core/
│   ├── block.py             ← Block data structure + hashing
│   ├── chain.py             ← The Blockchain class (add blocks, validate, etc.)
│   ├── mempool.py           ← Pending transaction pool
│   ├── merkle.py            ← Merkle tree for transaction integrity
│   ├── crypto.py            ← ECDSA signing/verification
│   └── persistence.py       ← SQLite storage
├── modules/
│   ├── consensus/pow.py     ← Only YOUR chosen consensus is included
│   ├── sync/full.py         ← Only YOUR chosen sync mode is included
│   ├── vm/python_vm.py      ← Smart contract execution engine
│   ├── network/p2p.py       ← WebSocket P2P networking
│   └── smart_contracts/     ← Your contracts + system contracts
├── interfaces/              ← Abstract base classes (ConsensusInterface, etc.)
├── api/server.py            ← FastAPI REST API for the node
├── di.py                    ← Dependency Injector — wires everything together
└── sdk/
    ├── client.py            ← Auto-generated Python SDK
    └── client.js            ← Auto-generated JavaScript SDK
```

---

## How the Platform Builds the ZIP

The platform's `ChainBuilder.build_package()` works like this:

1. **Walk** through all files in `templates/chain_core/`
2. **Filter** — only include the consensus/sync/vm files matching your config
   - e.g. if you picked PoW, only `pow.py` is included, not `poa.py`, `raft.py`, etc.
3. **Inject** your settings as `config/genesis.json`
4. **Bundle** your smart contracts (transpiling Solidity → Python if needed)
5. **Generate** `api/server.py`, `api/contract_routes.py`, `sdk/client.py`, `sdk/client.js` on the fly
6. **Return** the whole thing as a ZIP file in memory

---

## Runtime: How a Node Starts

When you run `python main.py` on your generated blockchain:

1. Parse CLI args (`--port`, `--peers`, `--role`, `--db-path`)
2. Read `config/genesis.json`
3. Use `DependencyInjector` to create the right modules
4. Spin up 3 things in parallel threads:
   - **Mining loop** — checks for pending transactions every 5 seconds
   - **API server** — FastAPI on your chosen port (REST + WebSocket)
   - **P2P network** — connects to peers, listens for gossip
5. Keep running forever

---

## Summary

| Thing | What it is |
|---|---|
| ChainForge Platform | A website that generates blockchain code |
| `chain_core/` template | Master copy of the blockchain (all modules) |
| Generated ZIP | Your specific blockchain (only chosen modules) |
| `genesis.json` | Config file that controls how the node behaves |
| `di.py` | Wires everything together at startup |
| SDK | Auto-generated client library to interact with contracts |

---

*Next: [Topic 2 — The Blockchain Data Structures](./02_blockchain_data_structures.md)*
