# Blockchain Architecture & Smart Contracts

This document clarifies how the generated blockchain operates, how smart contracts interact with it, and how different configurations (Consensus, Network, Node Types) affect the system.

## 1. The Application Flow: Developer vs. End User
*This section clarifies the roles of the conceptual "Developer" vs the "End User" when interacting with the ChainForge platform.*

> *"Correct me if I am wrong. So what the dev does is that whenever someone signs up to his website or app, he makes them a client and later calls these smart contracts using that?"*

Almost! There is a slight mix-up in terminology between the "Client SDK" and the "End User".

Here is how a real-world integration works:

1. **The SDK Client represents the SERVER, not the User.**
   When the Developer builds their website (let's say they build a Web3 Game), they import the `ChainForgeClient` (the SDK) into their **Backend Server** or their **Frontend React App**. 
   There is only ONE `ChainForgeClient` instance running for the entire application. It acts as the "bridge" between the Developer's website and the Blockchain Node.

2. **How Users Interact:**
   When "Alice" (an End User) signs up on the Developer's game, the Developer doesn't create a new SDK Client for her. Instead:
   * Alice clicks "Buy Sword" on the website.
   * The website's code uses its single `ChainForgeClient` to call the smart contract: 
     `client.GameContract.buyItem(user="Alice", item="Sword")`
   * The transaction is sent to the blockchain, queued, and mined.

3. **Authentication & The "Sender":**
   Right now, in our MVP template code (inside `builder.py`), every transaction is hardcoded with `"sender": "user"`. 
   In a production Web3 environment, the Developer would pass the End User's **public wallet address** or **digital signature** as part of the transaction so the Smart Contract knows *who* is actually executing the action (this is why we added `msg.sender` support for Solidity earlier!).

---

## 2. Handling Different Configurations (PoW, Full/Light Nodes, Public/Private)

> *"How does it work under different testcases like if it is a PoW full node public... or PoA light node... etc.?"*

The beauty of the ChainForge architecture (and blockchains in general) is the **separation of concerns**. 

**Smart contracts DO NOT involve or care about the blockchain infrastructure logic.** 
A smart contract writing `"storage_value" = 42` will execute exactly the same way regardless of whether the blockchain is running Proof-of-Work, Raft, or PBFT. 

The blockchain features are handled entirely by the underlying **Blockchain Core Code** (the modules in `chain_core`):

*   **Consensus (PoW, PoA, Raft, etc.):** This determines **who** gets to create the next block and **how** nodes agree it's valid.
    *   *If PoW:* Nodes compete to solve a cryptographic puzzle to mine the block.
    *   *If Raft (Centralized):* One elected "Leader" node batches transactions into blocks and distributes them to follower nodes.
*   **Network (Public vs. Permissioned):** This determines **who can join**.
    *   *If Public:* Nodes use a P2P discovery protocol to find anyone else on the internet running the software.
    *   *If Permissioned:* Nodes verify cryptographic certificates or use an explicit allowlist before accepting connections.
*   **Sync Mode (Full vs. Light vs. Snapshot):** This determines **how data is stored**.
    *   *Full Node:* Downloads every block since the Genesis block, executes every transaction in history, and stores the full, verified `state`.
    *   *Light Node:* Only downloads Block Headers (to verify PoW hashes or signatures) and requests specific pieces of state from Full Nodes when a user asks for it. It does not execute smart contracts itself.

### How Different Nodes React to a Smart Contract Call:
If I send a transaction to a **Light Node**, it will just forward the transaction to the P2P network. Eventually, a **Full Node** (acting as a Miner in PoW, or a Leader in Raft) will receive it, execute the smart contract, create a block, and broadcast the block back to the Light Node.

## 3. How Do We Check/Test All These Features?

Because the Smart Contract logic and Blockchain Infrastructure are separate, we test them separately:

1.  **Testing Infrastructure (The "Combinations"):** We use scripts like `test_scenarios.py` in the ChainForge backend. This script defines predefined scenarios (e.g., Scenario 1: Public + PoW + Full, Scenario 3: Permissioned + Raft). It generates the blockchain code for each combination and ensures that the Dependency Injector (`di.py`) successfully wires the requested modules together without crashing.
2.  **Testing Smart Contracts:** We test the Virtual Machine natively (as we did in `verify_smart_contracts.py`), ensuring that when a transaction is placed in a block, the VM executes it properly and updates the state.
3.  **End-to-End Network Tests (Future Integration):** To truly test that consensus algorithms behave perfectly at scale, we would deploy multiple generated nodes (e.g., 5 nodes running PoW) in Docker containers, send diverging transactions to them, and verify that they eventually synchronize on the same longest chain.
