import sys, json, hashlib
sys.path.insert(0, '.')
from core.chain import Blockchain
from core.block import Block
from modules.consensus.pow import PoWConsensus
from modules.vm.python_vm import PythonVM

consA = PoWConsensus(target_difficulty=2)
vmA = PythonVM()
chain_a = Blockchain(consensus=consA, runtime=vmA, require_signature=False)

# Mine and add blocks exactly as test does
for i in range(3):
    chain_a.add_transaction({'from':'x','to':'y','amount':i,'type':'transfer'})
    b = chain_a.consensus.propose_block(chain_a.pending_transactions, chain_a.last_block.hash, len(chain_a.chain), 'miner')
    chain_a.add_block(b)

print("=== CHECK AFTER add_block ===")
for blk in chain_a.chain[1:]:
    d = blk.to_dict()
    # Verify original block
    d_copy = {k:v for k, v in d.items() if k != 'hash'}
    direct_hash = hashlib.sha256(json.dumps(d_copy, sort_keys=True).encode()).hexdigest()
    print(f"Block {blk.index}: nonce={d['nonce']} stored_hash={d['hash'][:12]} direct_from_dict_hash={direct_hash[:12]} match={d['hash']==direct_hash}")

print()
print("=== RECONSTRUCTED AFTER JSON ROUND-TRIP ===")
for blk in chain_a.chain[1:]:
    d = blk.to_dict()
    d_rt = json.loads(json.dumps(d))
    rec = Block(index=d_rt['index'], transactions=d_rt['transactions'], timestamp=d_rt['timestamp'], previous_hash=d_rt['previous_hash'], validator=d_rt.get('validator'))
    rec.nonce = d_rt.get('nonce', 0)
    rec.hash = d_rt.get('hash')
    recomp = rec.compute_hash()
    print(f"Block {rec.index}: nonce={rec.nonce} stored={rec.hash[:12]} recomputed={recomp[:12]} match={rec.hash==recomp}")
    if rec.hash != recomp:
        print(f"  MISMATCH FOUND! d_rt keys: {list(d_rt.keys())}")
        print(f"  rec.__dict__ keys: {list(rec.__dict__.keys())}")
        compute_data = {k:v for k, v in rec.__dict__.items() if k != 'hash'}
        print(f"  compute_data: {json.dumps(compute_data, sort_keys=True)[:200]}")
