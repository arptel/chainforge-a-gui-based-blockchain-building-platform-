# ChainForge: Project Summary & Overview

ChainForge is a comprehensive **Blockchain-as-a-Service (BaaS) factory** designed to democratize web3 technology. It allows users to design, configure, and spawn custom decentralized blockchain networks through a user-friendly GUI, without requiring deep expertise in cryptography or peer-to-peer networking.

## 🎯 Project Goals

1.  **Lower the Entry Barrier**: Provide a "No-Code/Low-Code" platform for building custom blockchains.
2.  **Modular Blockchain Building**: Allow users to "pick and choose" core components like consensus mechanisms (PoW, PBFT, Raft) and synchronization modes.
3.  **Real-world Utility**: Focus on practical applications like the **Certificate Verification System**, enabling decentralized issuance and validation of academic/professional credentials.
4.  **Educational Resource**: Serve as a tool for learning blockchain internals through simplified architecture and clear documentation (found in `theory/`).

---

## 📂 Directory Structure Overview

The project is organized into two primary pillars: the **Platform** (the creator) and the **System** (a practical implementation).

### 🛠️ `chainforge/` (The Factory)
This is the core of the project, containing the logic to build other blockchains.
-   **`platform-frontend/`**: A modern **Next.js** application. This is the "Builder GUI" where users configure their blockchain's parameters (consensus, smart contracts, etc.).
-   **`platform-backend/`**: A **FastAPI (Python)** server that handles:
    -   User Authentication and Profile management.
    -   Blockchain Project CRUD operations (stored in [chainforge.db](file:///c:/Users/ARTH%20PATEL/OneDrive/Desktop/ARTH/Sem-6/Blockchain/chainforge/platform-backend/chainforge.db)).
    -   **`generator/`**: The "engine" that takes a configuration and bundles a set of files into a downloadable **ZIP** file containing a full, standalone blockchain node.
-   **`templates/`**: Contains the source code blueprints used by the generator to build custom nodes.

### 🎓 `certificate_verification_system/` (The Application)
A real-world implementation built using ChainForge.
-   **Issuers (Colleges)**: Use Full Nodes to sign and "Add" certificates to the blockchain.
-   **Verifiers (Companies)**: Use Nodes (Full or Light) to independently verify the authenticity of certificates.
-   **SPV Architecture**: Implements Simplified Payment Verification to allow light clients to verify transactions without downloading the entire chain history.

### 📚 `theory/`
A collection of markdown files explaining blockchain fundamentals, from PBFT consensus to Merkle Trees, used both for development reference and user education.

---

## 💻 Technology Stack

| Layer | Technology |
| :--- | :--- |
| **GUI Frontend** | React, Next.js, TypeScript, Tailwind CSS |
| **Platform Backend** | Python, FastAPI, SQLAlchemy (SQLite) |
| **Blockchain Nodes** | Python (Vanilla + standard libraries for portability) |
| **Networking** | WebSockets (P2P Gossip & Real-time Sync) |
| **Database** | SQLite (Per-node persistence and platform metadata) |
| **Consensus** | Plug-and-play modules: PoW, PBFT, PoA, Raft |

---

## 🏗️ Architecture Highlights

-   **Dynamic Dependency Injection**: Generated nodes use a modular `di.py` system to wire components together at runtime based on the user's selected configuration.
-   **Web3 SPV Support**: A custom "Light Service" that interacts with "AU" (Authenticated) nodes to verify transactions via Merkle proofs, ensuring scalability.
-   **P2P Gossip Protocol**: A custom implementation over WebSockets that handles peer discovery, handshaking, transaction propagation, and block broadcast.
-   **World State Consistency**: Every node independently executes smart contract logic to ensure all actors in the network reach the same database state (Consensus).

---

> [!NOTE]
> The project is currently in an active development phase, with recent work focusing on refining the **SPV verification flow** and improving **node synchronization** between College and Company nodes.
