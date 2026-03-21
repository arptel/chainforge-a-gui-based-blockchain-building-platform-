/**
 * Config Parser - Frontend validation and parsing of config.yaml
 */

class ConfigParser {
    /**
     * Parse config from backend
     * 
     * @param {object} configData - Config object from backend
     * @returns {object} Parsed and validated config
     */
    static parse(configData) {
        // TODO: Validate config structure
        //   - Check required fields
        //   - Validate enum values
        //   - Store in global app state
        pass
    }

    /**
     * Validate config structure
     * 
     * @param {object} config - Config object
     * @throws {Error} If config is invalid
     */
    static validate(config) {
        const required = [
            'network_type',
            'governance',
            'consensus',
            'node_roles',
            'sync_mode',
            'max_nodes',
            'block_time_ms'
        ];

        for (const field of required) {
            if (!(field in config)) {
                throw new Error(`Missing required config field: ${field}`);
            }
        }

        // TODO: Validate enum values
        //   - consensus in valid types
        //   - sync_mode in valid modes
        //   - network_type valid
        //   - governance valid
    }

    /**
     * Create config summary for UI display
     * 
     * @param {object} config - Config object
     * @returns {object} Summary with readable fields
     */
    static createSummary(config) {
        // TODO: Format config for UI display
        //   - Network type, Governance
        //   - Consensus algorithm
        //   - Available node roles
        //   - Sync mode
        //   - Block time
        //   - Modules loaded
        pass
    }

    /**
     * Get consensus-specific details
     * 
     * @param {string} consensusType - Consensus type
     * @returns {object} Consensus type details
     */
    static getConsensusDetails(consensusType) {
        const details = {
            'pow': {
                name: 'Proof of Work',
                description: 'Miners compete to solve computational puzzle',
                phases: ['Mining', 'Block Proposal', 'Commit']
            },
            'pos': {
                name: 'Proof of Stake',
                description: 'Validators selected proportionally to stake',
                phases: ['Validator Selection', 'Proposal', 'Voting', 'Commit']
            },
            'poa': {
                name: 'Proof of Authority',
                description: 'Pre-approved authority nodes validate',
                phases: ['Authority Stamping', 'Finalization']
            },
            'pbft': {
                name: 'Practical Byzantine Fault Tolerance',
                description: 'Three-phase Byzantine consensus',
                phases: ['Pre-Prepare', 'Prepare', 'Commit']
            },
            'raft': {
                name: 'Raft',
                description: 'Leader-based consensus with elections',
                phases: ['Leader Election', 'Log Replication', 'Commit']
            },
            'tendermint': {
                name: 'Tendermint',
                description: 'Round-based BFT with deterministic proposers',
                phases: ['Propose', 'Prevote', 'Precommit', 'Commit']
            },
            'hotstuff': {
                name: 'HotStuff',
                description: 'Linear BFT with pipelined phases',
                phases: ['Prepare', 'Pre-Commit', 'Commit']
            },
            'paxos': {
                name: 'Paxos',
                description: 'Two-phase consensus on single value',
                phases: ['Prepare', 'Accept']
            },
            'none': {
                name: 'None',
                description: 'No consensus - any node can propose',
                phases: ['Direct Proposal', 'Commit']
            }
        };
        
        return details[consensusType] || null;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConfigParser;
}
