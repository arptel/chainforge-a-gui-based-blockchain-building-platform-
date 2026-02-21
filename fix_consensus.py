import os
consensus_modules = [
    ('raft', 'RaftConsensus'),
    ('poa', 'PoAConsensus'), 
    ('pos', 'PoSConsensus'),
    ('pbft', 'PBFTConsensus'),
    ('tendermint', 'TendermintConsensus'),
    ('hotstuff', 'HotStuffConsensus'),
    ('paxos', 'PaxosConsensus'),
    ('none', 'NoConsensus')
]

for f, c in consensus_modules:
    path = f'chainforge/templates/chain_core/modules/consensus/{f}.py'
    with open(path, 'w') as fh:
        fh.write(f'from interfaces.consensus import ConsensusInterface\nclass {c}(ConsensusInterface):\n    def validate_block(self, block): return True\n')
