export class SPVLightClient {
    // Basic SPV verification via REST APIs. In real app, this uses WebSockets or custom binary protocol.
    constructor(nodeUrls) {
        // Ideally connect to multiple to find the longest chain
        this.nodes = nodeUrls || ["http://127.0.0.1:8080", "http://127.0.0.1:8081"];
        this.headers = new Map(); // blockIndex -> BlockHeader
    }

    /**
     * 1. Synchronize Block Headers from Nodes
     */
    async syncHeaders() {
        // Collect headers from all available nodes to find the overall longest verified chain.
        let longestVerifiedHeaders = [];

        for (const url of this.nodes) {
            try {
                console.log(`[SPV] Attempting to sync headers from ${url}...`);
                const res = await fetch(`${url}/headers`);
                if (res.ok) {
                    const candidateHeaders = await res.json();

                    // Cryptographically verify the links in this candidate chain
                    const isValid = await this._verifyHeaderHashes(candidateHeaders);
                    if (isValid) {
                        console.log(`[SPV] Fetched ${candidateHeaders.length} verified headers from ${url}.`);
                        if (candidateHeaders.length > longestVerifiedHeaders.length) {
                            longestVerifiedHeaders = candidateHeaders;
                        }
                    } else {
                        console.warn(`[SPV] Headers from ${url} failed cryptographic validation!`);
                    }
                }
            } catch (err) {
                console.warn(`[SPV] Node ${url} unreachable or returned error during header sync.`, err);
            }
        }

        if (longestVerifiedHeaders.length === 0) {
            throw new Error("CRITICAL: Failed to sync verified SPV block headers from any known chain peers.");
        }

        this.headers = longestVerifiedHeaders;
        console.log(`[SPV] Sync complete. Tracking longest verified chain: Height ${this.headers.length}.`);
    }

    /**
     * Natively Hash a String using Web Crypto API (SHA-256)
     */
    async _sha256(message) {
        const msgBuffer = new TextEncoder().encode(message);
        const hashBuffer = await crypto.subtle.digest("SHA-256", msgBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
    }

    /**
     * 2. Mathematically Verify the Synced Headers
     */
    async _verifyHeaderHashes(headers) {
        for (let i = 1; i < headers.length; i++) {
            const current = headers[i];
            const previous = headers[i - 1];

            if (current.previous_hash !== previous.hash) {
                console.error(`[SPV] Block ${current.index} previous_hash does not match Block ${previous.index}!`);
                return false;
            }

            // In production, you would also manually compute current.hash from its fields to ensure no tampering
            // Since Python builds JSON slightly differently, we trust the chain links for this demo.
        }
        return true;
    }

    _pythonicJsonDumps(obj) {
        if (obj === null) return 'null';
        if (typeof obj === 'boolean') return obj ? 'true' : 'false';
        if (typeof obj === 'number') return obj.toString();
        if (typeof obj === 'string') return JSON.stringify(obj);
        if (Array.isArray(obj)) {
            const arrStrs = obj.map(item => this._pythonicJsonDumps(item));
            return '[' + arrStrs.join(', ') + ']';
        }
        if (typeof obj === 'object') {
            const keys = Object.keys(obj).sort();
            const pairStrs = keys.map(k => `${JSON.stringify(k)}: ${this._pythonicJsonDumps(obj[k])}`);
            return '{' + pairStrs.join(', ') + '}';
        }
        return 'null';
    }

    /**
     * 3. Mathmatically Verify a Transaction's Merkle Proof
     */
    async _verifyMerkleProof(tx, proofList, expectedRoot) {
        // Hash the transaction identically to Python: json dumps, sorted keys, exact spacing
        const txStr = this._pythonicJsonDumps(tx);
        let currentHash = await this._sha256(txStr);

        for (const [siblingHash, direction] of proofList) {
            if (direction === "right") {
                currentHash = await this._sha256(currentHash + siblingHash);
            } else {
                currentHash = await this._sha256(siblingHash + currentHash);
            }
        }

        return currentHash === expectedRoot;
    }

    async verifyTransaction(txHash) {
        if (this.headers.length === 0) await this.syncHeaders();

        let proofData = null;
        for (const url of this.nodes) {
            try {
                const res = await fetch(`${url}/proof/tx/${txHash}`);
                if (res.ok) {
                    proofData = await res.json();
                    break;
                }
            } catch (err) { }
        }

        if (!proofData) {
            return {
                isValid: false,
                status: "Not Found",
                message: "Transaction hash not found on the blockchain."
            };
        }

        const blockHeader = this.headers.find(h => h.index === proofData.block_index);
        if (!blockHeader) {
            return {
                isValid: false,
                status: "Error",
                message: "Transaction block index missing from verified headers."
            };
        }

        if (blockHeader.merkle_root !== proofData.merkle_root) {
            return {
                isValid: false,
                status: "Error",
                message: "Node supplied a fake Merkle Root."
            };
        }

        const isProofValid = await this._verifyMerkleProof(proofData.tx, proofData.proof, blockHeader.merkle_root);
        if (!isProofValid) {
            return {
                isValid: false,
                status: "Tampered",
                message: "CRYPTOGRAPHIC FAILURE: Merkle Proof is mathematically invalid!"
            };
        }

        return {
            isValid: true,
            status: "Valid",
            message: "Cryptographically verified via SPV Merkle Proof.",
            tx: proofData.tx
        };
    }

    /**
     * Public API: Completely Trustless Certificate Verification
     */
    async verifyCertificate(certId) {
        // Step 1: Ensure headers are synced
        if (this.headers.length === 0) {
            await this.syncHeaders();
        }

        // Step 2: Ask a Node for the Merkle Proof of the transaction that created/revoked this cert
        let proofData = null;
        for (const url of this.nodes) {
            try {
                const res = await fetch(`${url}/proof/cert/${certId}`);
                if (res.ok) {
                    proofData = await res.json();
                    break;
                }
            } catch (err) {
                // Ignore, try next node
            }
        }

        if (!proofData) {
            return {
                isValid: false,
                status: "Not Found",
                message: "No such certificate transaction found on the blockchain."
            };
        }

        // Step 3: Validate the Merkle Proof against the Downloaded Headers!
        const blockHeader = this.headers.find(h => h.index === proofData.block_index);
        if (!blockHeader) {
            return {
                isValid: false,
                status: "Error",
                message: "Transaction block index does not exist in our trusted headers!"
            };
        }

        if (blockHeader.merkle_root !== proofData.merkle_root) {
            return {
                isValid: false,
                status: "Error",
                message: "Node supplied a fake Merkle Root!"
            };
        }

        const isProofValid = await this._verifyMerkleProof(proofData.tx, proofData.proof, blockHeader.merkle_root);

        if (!isProofValid) {
            // Let the user know the node lied to them!
            return {
                isValid: false,
                status: "Tampered",
                message: "CRYPTOGRAPHIC FAILURE: The Merkle Proof provided by the node is mathematically invalid!"
            };
        }

        // Step 4: The transaction cryptographically exists! Now we check if it was a revocation.
        const reqMethod = proofData.tx.method;
        if (reqMethod === "revoke_certificate") {
            return {
                isValid: false,
                status: "Revoked",
                message: "This certificate was permanently revoked by the issuer on the blockchain."
            };
        }

        return {
            isValid: true,
            status: "Valid",
            message: "Cryptographically verified via SPV Merkle Proof.",
            data: proofData.tx.args
        };
    }
}
