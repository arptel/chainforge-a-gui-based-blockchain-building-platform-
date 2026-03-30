/**
 * WebSocket Client - Manages connection to backend and event dispatching
 * 
 * Connects to ws://host/events (FastAPI backend on port 8000)
 * Receives ChainEvent envelopes and dispatches to EventDispatcher
 * Handles reconnection with exponential backoff
 */

class WebSocketClient {
    constructor(apiUrl = 'http://localhost:8000') {
        this.apiUrl = apiUrl;
        this.wsUrl = apiUrl.replace('http', 'ws') + '/events';
        this.ws = null;
        this.dispatcher = null; // EventDispatcher reference
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 15;
        this.reconnectDelay = 500; // ms base delay (faster initial retry)
        this.maxDelay = 5000; // cap at 5 seconds
        this.messageBuffer = [];
        this.onStatusChange = null; // callback: (status) => {}
    }

    /**
     * Set the event dispatcher for routing events
     * @param {EventDispatcher} dispatcher
     */
    setDispatcher(dispatcher) {
        this.dispatcher = dispatcher;
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        try {
            this.ws = new WebSocket(this.wsUrl);

            this.ws.onopen = () => {
                this.isConnected = true;
                this.reconnectAttempts = 0;
                console.log('[WS] Connected to', this.wsUrl);
                if (this.onStatusChange) this.onStatusChange('connected');

                // Drain any buffered messages
                while (this.messageBuffer.length > 0) {
                    const msg = this.messageBuffer.shift();
                    this.ws.send(msg);
                }
            };

            this.ws.onmessage = (msgEvent) => {
                this._handleMessage(msgEvent);
            };

            this.ws.onclose = () => {
                this._handleClose();
            };

            this.ws.onerror = (error) => {
                this._handleError(error);
            };
        } catch (error) {
            console.error('[WS] Connection error:', error);
            this._attemptReconnect();
        }
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.isConnected = false;
        console.log('[WS] Disconnected');
    }

    /**
     * Internal: handle incoming message from server
     */
    _handleMessage(msgEvent) {
        try {
            const event = JSON.parse(msgEvent.data);

            // Validate event structure
            if (!event.type) {
                console.warn('[WS] Received event without type:', event);
                return;
            }

            // Dispatch to EventDispatcher if available
            if (this.dispatcher) {
                this.dispatcher.emit(event);
            }
        } catch (error) {
            console.error('[WS] Failed to parse message:', error, msgEvent.data);
        }
    }

    /**
     * Internal: handle WebSocket close
     */
    _handleClose() {
        this.isConnected = false;
        console.log('[WS] Connection closed');
        if (this.onStatusChange) this.onStatusChange('disconnected');
        this._attemptReconnect();
    }

    /**
     * Internal: handle WebSocket error
     */
    _handleError(error) {
        console.error('[WS] Error:', error);
    }

    /**
     * Attempt to reconnect with exponential backoff
     */
    _attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('[WS] Max reconnect attempts reached. Giving up.');
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), this.maxDelay);
        console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        if (this.onStatusChange) this.onStatusChange('reconnecting');

        setTimeout(() => {
            this.connect();
        }, delay);
    }

    /**
     * Send message to backend
     */
    send(message) {
        const data = typeof message === 'string' ? message : JSON.stringify(message);
        if (this.isReady()) {
            this.ws.send(data);
        } else {
            this.messageBuffer.push(data);
        }
    }

    /**
     * Check if client is currently connected
     */
    isReady() {
        return this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketClient;
}
