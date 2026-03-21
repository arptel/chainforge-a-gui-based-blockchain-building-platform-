/**
 * ConsensusRendererBase - Base class for consensus-type-specific renderers
 * 
 * Each consensus type has its own animation and visualization logic.
 * All renderers inherit from this base class.
 */

class ConsensusRendererBase {
    /**
     * Initialize renderer
     * 
     * @param {string} consensusType - Consensus type (pow, pos, pbft, etc.)
     * @param {HTMLElement} container - DOM element to render into
     */
    constructor(consensusType, container) {
        this.consensusType = consensusType;
        this.container = container;
        this.state = {};
    }

    /**
     * Render consensus phase information
     * Must be implemented by subclass
     * 
     * @param {object} consensusState - Current consensus state
     */
    renderPhase(consensusState) {
        throw new Error('renderPhase() must be implemented by subclass');
    }

    /**
     * Render vote visualization
     * Must be implemented by subclass
     * 
     * @param {object} voteEvent - Vote cast event
     */
    renderVote(voteEvent) {
        throw new Error('renderVote() must be implemented by subclass');
    }

    /**
     * Render fault tolerance information
     * Optional for subclasses
     * 
     * @param {object} consensusState - Current consensus state
     */
    renderFaultTolerance(consensusState) {
        // Default implementation - can be overridden
    }

    /**
     * Clear animations and reset state
     * Optional for subclasses
     */
    reset() {
        this.state = {};
    }

    /**
     * Utility: Create DOM element for phase display
     * 
     * @param {string} phaseName - Phase name
     * @returns {HTMLElement}
     */
    createPhaseElement(phaseName) {
        // TODO: Create styled phase display element
        pass
    }

    /**
     * Utility: Create DOM element for vote tally
     * 
     * @param {number} accepted - Votes accepted
     * @param {number} rejected - Votes rejected
     * @param {number} pending - Votes pending
     * @returns {HTMLElement}
     */
    createVoteTallyElement(accepted, rejected, pending) {
        // TODO: Create styled vote tally display
        pass
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConsensusRendererBase;
}
