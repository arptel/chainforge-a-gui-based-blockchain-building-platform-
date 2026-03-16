import unittest
import hashlib
import json
from core.merkle import compute_merkle_root, generate_merkle_proof, verify_merkle_proof, _hash_tx

class TestMerkleTree(unittest.TestCase):
    def setUp(self):
        self.txs = [
            {"from": "alice", "to": "bob", "amount": 10},
            {"from": "bob", "to": "charlie", "amount": 5},
            {"from": "charlie", "to": "alice", "amount": 2},
            {"from": "dave", "to": "eve", "amount": 8}
        ]

    def test_compute_root_consistency(self):
        """Root should be deterministic."""
        root1 = compute_merkle_root(self.txs)
        root2 = compute_merkle_root(self.txs)
        self.assertEqual(root1, root2)
        self.assertTrue(isinstance(root1, str))
        self.assertEqual(len(root1), 64)

    def test_empty_transactions(self):
        """Empty list should return a specific sentinel hash or handle gracefullly."""
        # Current implementation returns sha256("empty")
        root = compute_merkle_root([])
        expected = hashlib.sha256(b"empty").hexdigest()
        self.assertEqual(root, expected)

    def test_single_transaction(self):
        """Single transaction root should be its own hash (or a specific padding)."""
        tx = [{"from": "a", "to": "b", "amount": 1}]
        root = compute_merkle_root(tx)
        # In this implementation, a single leaf is processed in a tree
        # level 0: [hash_a] -> padding level 0: [hash_a, hash_a] -> level 1: [hash(hash_a+hash_a)]
        self.assertNotEqual(root, _hash_tx(tx[0]))

    def test_proof_verification_success(self):
        """Valid proofs should verify against the root."""
        root = compute_merkle_root(self.txs)
        for i in range(len(self.txs)):
            proof = generate_merkle_proof(self.txs, i)
            self.assertTrue(verify_merkle_proof(self.txs[i], proof, root))

    def test_proof_verification_failure(self):
        """Tampered transactions or roots should fail verification."""
        root = compute_merkle_root(self.txs)
        proof = generate_merkle_proof(self.txs, 0)
        
        # Tamper with the transaction
        fake_tx = self.txs[0].copy()
        fake_tx["amount"] = 999
        self.assertFalse(verify_merkle_proof(fake_tx, proof, root))
        
        # Tamper with the root
        self.assertFalse(verify_merkle_proof(self.txs[0], proof, "0"*64))

    def test_odd_transaction_count(self):
        """Standard Bitcoin-style padding (duplicate last leaf) should work for odd counts."""
        odd_txs = self.txs[:3]
        root = compute_merkle_root(odd_txs)
        for i in range(len(odd_txs)):
            proof = generate_merkle_proof(odd_txs, i)
            self.assertTrue(verify_merkle_proof(odd_txs[i], proof, root))

if __name__ == '__main__':
    unittest.main()
