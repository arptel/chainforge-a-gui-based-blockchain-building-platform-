# ChainForge Network Simulator — Project Rules

## Specification File
The full project specification lives at: ./chainforge_simulator_spec.docx
Read this file before starting any task. Every decision about architecture,
feature behavior, consensus logic, sync modes, and error messages is defined
there. Do not deviate from it.

## Non-negotiables
- The blockchain must actually run in the background. There is no simulation
  fallback. Real node processes must be spawned for every node added.
- All frontend state is driven exclusively by real WebSocket events from the
  backend. Never fabricate state or use timers to guess chain behavior.
- All 9 consensus types must be implemented: hotstuff, none, paxos, pbft,
  poa, pos, pow, raft, tendermint. No stubs.
- All 6 sync modes must be implemented: batch, fast, full, light, realtime,
  snapshot. Each has distinct animation behavior defined in the spec.
- All behavior is config-driven from config.yaml. Nothing is hardcoded.
- Permissions (node creation, transaction initiation) are enforced server-side
  in the backend. Frontend enforcement is cosmetic only.

## Architecture
- Backend is mandatory. It spawns node processes, proxies all chain calls,
  and streams events to the frontend over WebSocket.
- One IChainAdapter implementation per consensus type.
- Frontend is minimal — plain HTML/JS is acceptable. Focus on correctness
  of functionality, not visual polish.
- WebSocket event envelope: { type, timestamp, nodeId, payload }

## Error Messages
All errors must be specific and name the relevant field, role, or reason.
No generic errors. See Section 4.10 of the spec for the exact required messages.

## Before every task
1. Re-read the relevant section of the spec for what you are building.
2. If anything conflicts with these rules, the spec takes precedence.
3. Do not add features not in the spec without asking first.