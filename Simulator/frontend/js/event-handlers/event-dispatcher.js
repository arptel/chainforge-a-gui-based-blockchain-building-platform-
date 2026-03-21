/**
 * Event Dispatcher - Central hub for all chain events
 * Routes events to appropriate handlers based on type.
 * Supports all 11 spec-required event types.
 */

class EventDispatcher {
    constructor() {
        // All 11 spec-required event types
        this.handlers = {
            'NODE_JOINED': [],
            'NODE_OFFLINE': [],
            'SYNC_PROGRESS': [],
            'SYNC_COMPLETE': [],
            'TX_BROADCAST': [],
            'CONSENSUS_PHASE': [],
            'VOTE_CAST': [],
            'BLOCK_PROPOSED': [],
            'BLOCK_COMMITTED': [],
            'BLOCK_REJECTED': [],
            'LEADER_ELECTED': [],
        };
    }

    /**
     * Register handler for specific event type
     * 
     * @param {string} eventType - Event type (e.g., 'NODE_JOINED')
     * @param {Function} handler - Function (event: ChainEvent) => void
     */
    on(eventType, handler) {
        if (!(eventType in this.handlers)) {
            console.warn(`Unknown event type: ${eventType}. Registering anyway.`);
            this.handlers[eventType] = [];
        }
        if (typeof handler === 'function') {
            this.handlers[eventType].push(handler);
        }
    }

    /**
     * Unregister handler for specific event type
     * 
     * @param {string} eventType - Event type
     * @param {Function} handler - Handler to remove
     */
    off(eventType, handler) {
        if (eventType in this.handlers) {
            const idx = this.handlers[eventType].indexOf(handler);
            if (idx !== -1) {
                this.handlers[eventType].splice(idx, 1);
            }
        }
    }

    /**
     * Dispatch event to all registered handlers for that type
     * 
     * @param {object} event - ChainEvent object with type, timestamp, nodeId, payload
     */
    emit(event) {
        const handlers = this.handlers[event.type] || [];
        for (const handler of handlers) {
            try {
                handler(event);
            } catch (error) {
                console.error(`Error in handler for ${event.type}:`, error);
            }
        }
    }

    /**
     * Get all registered handlers for an event type
     * 
     * @param {string} eventType - Event type
     * @returns {Function[]} Array of handlers
     */
    getHandlers(eventType) {
        return this.handlers[eventType] || [];
    }

    /**
     * Clear all handlers for an event type
     * 
     * @param {string} eventType - Event type to clear
     */
    clear(eventType) {
        if (eventType in this.handlers) {
            this.handlers[eventType] = [];
        }
    }

    /**
     * Clear all handlers for all event types
     */
    clearAll() {
        for (const eventType in this.handlers) {
            this.handlers[eventType] = [];
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EventDispatcher;
}
