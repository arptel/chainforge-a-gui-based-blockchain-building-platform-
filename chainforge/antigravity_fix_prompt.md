You are working inside the ChainForge repository on Windows.

Your job is to fix specific incomplete or miswired parts of the generated blockchain/template codebase without changing the overall architecture, public behavior, or product flow.

Read this entire prompt carefully and follow it exactly.

Goal:
- Fix the incomplete and broken modules listed below.
- Preserve the existing design of ChainForge as a blockchain generator.
- Do not rewrite the project.
- Do not perform unrelated cleanup.
- Do not rename files unless explicitly told.
- Do not remove supported options from the frontend wizard or backend generator.
- Make the minimum safe changes needed so the broken paths become functionally correct and the already-working paths keep working.

Important constraints:
- Keep all existing module names, file paths, and route names unless explicitly required.
- Maintain backward compatibility with current configuration keys coming from `genesis.json`.
- Prefer additive or compatibility-preserving fixes over refactors.
- If a file already has working logic, do not redesign it.
- When you change transaction schemas, support both the current field names and the corrected field names if feasible.
- If the sample generated chain and the richer template differ, prioritize fixing the template in a way that still keeps the sample chain runnable.
- Do not edit frontend visuals or unrelated auth/project CRUD code.

Repository structure you must understand first:
- `platform-frontend/` = config wizard UI
- `platform-backend/` = auth, projects, generation, download/install
- `templates/chain_core/` = source template used to generate blockchains
- `test_generated_blockchain/` = example generated blockchain output

Primary objective:
Fix the following broken or incomplete areas:

1. Consensus constructor / dependency injection mismatch
- Problem:
  - `PoAConsensus` and `PoSConsensus` require `chain_state` in their constructors.
  - `DependencyInjector.get_consensus()` currently instantiates consensus classes with `cls()` only.
  - This can break runtime selection for `poa` and `pos`.
- Files to inspect:
  - `test_generated_blockchain/di.py`
  - `templates/chain_core/di.py`
  - `test_generated_blockchain/modules/consensus/poa.py`
  - `test_generated_blockchain/modules/consensus/pos.py`
  - matching files in `templates/chain_core/modules/consensus/`
- Required fix:
  - Make consensus instantiation compatible with PoA and PoS without breaking existing consensus modules.
  - Use a compatibility-safe pattern. Preferred approach:
    - Allow `PoAConsensus` and `PoSConsensus` to accept `chain_state=None` by default.
    - Ensure validation logic behaves safely when state is not yet injected.
    - If needed, attach the chain state after chain creation in a minimal way.
  - Do not require major lifecycle changes to the app boot path.

2. P2P networking is partially stubbed
- Problem:
  - `broadcast()` is not implemented.
  - `start_server()` in the sample P2P layer is stubbed.
  - Networking helpers are inconsistent between sample and template.
- Files to inspect:
  - `test_generated_blockchain/modules/network/p2p.py`
  - `templates/chain_core/modules/network/p2p.py`
  - `test_generated_blockchain/api/server.py`
  - `templates/chain_core/api/server.py`
- Required fix:
  - Implement `broadcast()` in a way that can route transaction and block messages to peers.
  - Preserve existing helper methods like `broadcast_transaction()` and `broadcast_block()`.
  - Do not introduce a full new network stack; use the current HTTP/WebSocket design.
  - If `start_server()` remains unnecessary because FastAPI handles inbound traffic, make that explicit and compatible instead of leaving it as a dead stub.
  - Ensure the network module can safely integrate with the current server endpoints.

3. Sync modules are mostly placeholders
- Problem:
  - `FullSync`, `FastSync`, `LightSync`, `RealtimeSync`, and related sync modes mostly print messages rather than actually applying data.
- Files to inspect:
  - `test_generated_blockchain/modules/sync/*.py`
  - `templates/chain_core/modules/sync/*.py`
  - chain and API files that expose `/blocks`, `/headers`, `/state`, or proof endpoints
- Required fix:
  - Implement minimal functional sync behavior without building a full production sync engine.
  - Minimum acceptable behavior:
    - `FullSync` should be able to fetch blocks from a peer and try to append/replace chain data.
    - `FastSync` should be able to fetch a state snapshot and recent headers/blocks in a minimal compatible way.
    - `LightSync` should fetch headers and store/use header-only information compatibly.
    - `RealtimeSync` should do meaningful polling or message handling instead of only printing.
  - Reuse existing endpoints if possible.
  - Avoid breaking the current node startup flow.

4. Smart contract route transaction schema mismatch
- Problem:
  - `api/contract_routes.py` queues contract transactions using `"sender": "user"` while runtimes generally expect `"from"`.
  - API key is accepted but not actually checked.
  - Some contract execution paths are inconsistent across Python/solidity/mock flows.
- Files to inspect:
  - `test_generated_blockchain/api/contract_routes.py`
  - `templates/chain_core/api/contract_routes.py`
  - runtime files in `modules/vm/`
  - generated SDK client logic in backend builder if required
- Required fix:
  - Ensure queued contract transactions use the field names expected by the runtimes.
  - Preserve backward compatibility by tolerating both `"sender"` and `"from"` where reasonable.
  - Implement API key validation against the generated contract registry where possible.
  - Keep the existing route shape `/execute/{contract_id}/{method}`.
  - Do not replace queued execution with direct execution; keep the “contract call becomes blockchain transaction” model.

5. Signature / nonce / transaction compatibility gaps
- Problem:
  - Richer template expects signatures/nonces/gas in some flows, but some generated/sample flows submit bare transactions.
  - This may reject valid demo flows unexpectedly.
- Files to inspect:
  - `templates/chain_core/core/chain.py`
  - `templates/chain_core/core/mempool.py`
  - API routes and generated SDK code
- Required fix:
  - Preserve secure behavior when signatures are required.
  - Preserve demo usability when signatures are disabled.
  - Make transaction handling robust and explicit:
    - If signatures are required, error messages should be clear.
    - If signatures are disabled, current demo transactions should still work.
    - Contract-call and transfer transaction paths should not silently break due to missing field aliases.
  - Do not weaken signature enforcement globally.

6. Make the sample generated blockchain and template consistent where practical
- Problem:
  - The template is richer than `test_generated_blockchain`, and some behavior diverges too much.
- Required fix:
  - Align important compatibility points:
    - constructor signatures
    - transaction field names
    - network/sync integration patterns
    - block deserialization or state-root compatibility if touched
  - Do not try to make the sample fully identical to the template.
  - Only align the pieces needed to prevent broken generated output and broken examples.

What not to change:
- Do not redesign frontend wizard steps.
- Do not change auth model or JWT flow unless absolutely necessary for compilation.
- Do not remove support for any consensus choice visible in the UI.
- Do not replace Gemini transpilation with a new system.
- Do not introduce external infrastructure dependencies beyond what is already used by the repo.
- Do not perform formatting-only mass edits.

Implementation guidance:
- Read these files first:
  - `platform-backend/generator/builder.py`
  - `templates/chain_core/main.py`
  - `templates/chain_core/core/chain.py`
  - `templates/chain_core/di.py`
  - `test_generated_blockchain/main.py`
  - `test_generated_blockchain/di.py`
- Then fix template files first.
- After template fixes, mirror only the necessary compatibility changes into `test_generated_blockchain/`.
- If builder-generated code must change, update `platform-backend/generator/builder.py` carefully and minimally.

Definition of done:
- The code should keep the current architecture intact.
- PoA and PoS should no longer fail due to constructor mismatch.
- Contract-route queued transactions should be compatible with runtime expectations.
- Network broadcast should no longer be an empty stub.
- Sync modes should do basic real work rather than just print.
- Existing simple transaction flow should still work.
- Existing generation flow should still work.

Required verification steps:
1. Run targeted static checks by reading changed files for import and call compatibility.
2. Run any lightweight local tests already present if they are relevant.
3. If no relevant automated tests exist, add a few focused tests for the fixed logic only.
4. Verify that your changes do not break:
   - project generation
   - node startup
   - transaction submission
   - block creation path
5. Summarize exactly what was fixed and any remaining prototype limitations.

Output format required from you:
- First, list the files you plan to change.
- Then make the changes.
- Then run verification.
- Then provide:
  - changed files
  - why each change was needed
  - what now works
  - what is still intentionally prototype-level

Do not stop after analysis. Make the code changes.
