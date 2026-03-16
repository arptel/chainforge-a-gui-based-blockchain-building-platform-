export class SPVLightClient {
    constructor(nodeUrls) {
        this.nodes = nodeUrls || ["http://localhost:8080"];
        this.headers = [];
    }

    async syncHeaders() {
        let synced = false;
        for (const url of this.nodes) {
            try {
                const res = await fetch(`${url}/headers`);
                if (res.ok) {
                    this.headers = await res.json();
                    const hwValid = await this._verifyHeaderHashes(this.headers);
                    if (!hwValid) throw new Error("Cryptographic header validation failed on sync!");
                    synced = true;
                    break;
                }
            } catch (err) { }
        }
        if (!synced) throw new Error("CRITICAL: Failed to sync SPV block headers from any known chain peers.");
    }

    async _sha256(message) {
        const msgBuffer = new TextEncoder().encode(message);
        const hashBuffer = await crypto.subtle.digest("SHA-256", msgBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
    }

    async _verifyHeaderHashes(headers) {
        for (let i = 1; i < headers.length; i++) {
            const current = headers[i];
            const previous = headers[i - 1];
            if (current.previous_hash !== previous.hash) return false;
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

    async _verifyMerkleProof(tx, proofList, expectedRoot) {
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
}
