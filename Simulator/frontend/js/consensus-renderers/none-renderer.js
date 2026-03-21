/**
 * None (No Consensus) Renderer
 */

class NoneRenderer extends ConsensusRendererBase {
    constructor(container) {
        super('none', container);
    }

    renderPhase(consensusState) {
        /**
         * Render no-consensus mode: any node can propose
         * 
         * consensusState:
         * {
         *   consensus_type: "none",
         *   validator_count: N
         * }
         */
        // TODO: Implement no-consensus rendering:
        //   - Show yellow warning banner: "No consensus configured"
        //   - Display all nodes as equal proposers
        //   - No voting or consensus phases
        pass
    }

    renderVote(voteEvent) {
        /**
         * No voting in no-consensus mode
         */
        // TODO: This method should not be called in none mode
        pass
    }

    renderFaultTolerance(consensusState) {
        // TODO: Display: "N/A — no consensus mechanism active"
        pass
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NoneRenderer;
}
