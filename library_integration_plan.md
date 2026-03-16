# Libraries to Integrate Instead of Custom Implementations

## 1. Virtual Machines (VM)
### File: chainforge/templates/chain_core/modules/vm/wasm.py
- **Current Status**: Mock WASM runtime simulation
- **Library**: wasmer (https://github.com/wasmerio/wasmer-python)
- **Benefits**: High-performance WebAssembly runtime with full spec compliance
- **Integration**: Replace WASMRuntime with wasmer.Instance
- **Dependencies**: Add to requirements.txt: wasmer, wasmer-compiler-cranelift
- **Status**: Not available on Windows platform

## 2. Merkle Tree
### File: chainforge/templates/chain_core/core/merkle.py
- **Current Status**: Custom binary Merkle tree implementation (working correctly)
- **Library Attempted**: pymerkle (https://github.com/AntonisChristofides/pymerkle)
- **Integration Status**: Failed - API incompatible with existing interface
- **Issue**: pymerkle uses different tree construction algorithm, producing different root hashes
- **Dependencies**: pymerkle installed but not used
- **Note**: merkletools was attempted but requires C++ compilation not available on Windows
- **Resolution**: Kept custom implementation (correct and tested)

## 3. Consensus Algorithms (Advanced)
### File: chainforge/templates/chain_core/modules/consensus/pbft.py
- **Current Status**: Mock 3-phase PBFT simulation
- **Library**: bft (https://github.com/initc3/bft) or custom implementation
- **Benefits**: Real Byzantine Fault Tolerance with network communication
- **Integration**: Implement actual PBFT protocol with message passing
- **Dependencies**: May require additional networking libraries

### File: chainforge/templates/chain_core/modules/consensus/paxos.py
- **Current Status**: Mock Paxos with roles (Proposer/Acceptor/Learner)
- **Library**: paxos (https://github.com/cocagne/paxos) or similar
- **Benefits**: Distributed consensus with fault tolerance
- **Integration**: Replace mock with real Paxos implementation
- **Dependencies**: paxos library if available

### File: chainforge/templates/chain_core/modules/consensus/tendermint.py
- **Current Status**: Mock 3-phase Tendermint simulation
- **Library**: tendermint (Go-based, but Python bindings possible)
- **Benefits**: Production-ready BFT consensus
- **Integration**: Complex - may require Tendermint Core integration
- **Dependencies**: tendermint-python or similar

### File: chainforge/templates/chain_core/modules/consensus/hotstuff.py
- **Current Status**: Mock HotStuff simulation
- **Library**: hotstuff (research implementations available)
- **Benefits**: Linear communication complexity BFT
- **Integration**: Implement HotStuff protocol
- **Dependencies**: Custom implementation or research library

## 4. Smart Contract Compilation/Execution
### Files: smart_contracts/*.py
- **Current Status**: Python-based smart contracts
- **Library**: vyper (https://github.com/vyperlang/vyper) or solidity compiler
- **Benefits**: Compile-time type checking and optimization
- **Integration**: Add Vyper/Solidity compilation to deployment process
- **Dependencies**: vyper, solc (Solidity compiler)

## Priority Recommendations:
1. **High Priority**: ~~Merkle Tree (pymerkle)~~ - Custom implementation retained with comprehensive unit tests (20 tests passing)
2. **Medium Priority**: ~~Smart Contract compilation~~ - Vyper integration completed (vyper_engine.py)
3. **Low Priority**: ~~Advanced consensus~~ - ALL consensus protocols (PBFT, Paxos, Tendermint, HotStuff) now use real P2P protocol logic

## Notes:
- ✅ All consensus algorithms use real protocol logic with P2P message passing (completed March 16, 2026)
- ✅ Vyper smart contract VM integrated and registered in DI container
- ✅ Merkle tree has comprehensive unit tests (20 tests)
- VM implementations: Python VM (full), EVM (py-evm wrapper), Vyper (new), WASM (simulation)
- Network and crypto modules already use appropriate libraries (websockets, ecdsa)
- Sync modules now use aiohttp for async HTTP operations (completed)