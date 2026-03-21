/**
 * ChainForge Network Simulator - Frontend Main Application
 * 
 * Orchestrates:
 * - WebSocket connection to backend
 * - Event dispatching and routing
 * - State management
 * - UI updates
 */

class SimulatorApp {
    constructor() {
        this.wsClient = null;
        this.eventDispatcher = null;
        this.config = null;
        this.state = this.createInitialState();
        this.apiUrl = 'http://localhost:8000';
    }

    /**
     * Initialize the application
     */
    async init() {
        // Set up event dispatcher
        this.eventDispatcher = new EventDispatcher();

        // Register all event handlers
        this.registerEventHandlers();

        // Set up UI event listeners
        this.setupUIListeners();

        // Set up WebSocket client
        this.wsClient = new WebSocketClient(this.apiUrl);
        this.wsClient.setDispatcher(this.eventDispatcher);

        console.log('[App] Simulator initialized');
    }

    /**
     * Create initial application state
     */
    createInitialState() {
        return {
            config: null,
            nodes: new Map(),
            blocks: [],
            pendingBlock: null,
            currentRound: 0,
            selectedNodeId: null,
            speedMultiplier: 1.0,
            metrics: {
                totalNodes: 0,
                totalBlocks: 0,
                totalTransactions: 0,
                currentTPS: 0,
                consensusType: null,
                averageBlockTimeMs: 0,
                consensusLatencyMs: 0,
                faultToleranceN: 0,
            },
            replayBuffer: [],
        };
    }

    /**
     * Load a blockchain project from path
     */
    async loadProject(configPath) {
        try {
            const response = await fetch(`${this.apiUrl}/load-project`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ config_path: configPath }),
            });

            if (!response.ok) {
                const err = await response.json();
                this.showError(err.detail || 'Failed to load project');
                return;
            }

            this.config = await response.json();
            this.state.config = this.config;
            this.state.metrics.consensusType = this.config.consensus;

            // Update config banner
            this.updateConfigBanner();

            // Enable buttons
            document.getElementById('btn-add-node').disabled = false;
            document.getElementById('btn-reset').disabled = false;
            document.getElementById('btn-export-trace').disabled = false;
            document.getElementById('speed-slider').disabled = false;

            // Connect WebSocket for live events
            this.wsClient.connect();

            // Update status
            const badge = document.getElementById('status-badge');
            const statusText = document.getElementById('status-text');
            badge.textContent = 'Loaded';
            badge.className = 'badge badge-success';
            statusText.textContent = `${this.config.consensus.toUpperCase()} consensus | ${this.config.network_type}`;

            console.log('[App] Project loaded:', this.config);
        } catch (error) {
            this.showError('Failed to connect to backend: ' + error.message);
        }
    }

    /**
     * Add a new node to the network
     */
    async addNode(role) {
        try {
            const response = await fetch(`${this.apiUrl}/nodes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role }),
            });

            if (!response.ok) {
                const err = await response.json();
                this.showError(err.detail || 'Failed to add node');
                return;
            }

            const result = await response.json();
            console.log('[App] Node added:', result);
        } catch (error) {
            this.showError('Failed to add node: ' + error.message);
        }
    }

    /**
     * Submit a transaction
     */
    async submitTransaction(fromNodeId, toNodeId, payload) {
        try {
            const response = await fetch(`${this.apiUrl}/transaction`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fromNodeId, toNodeId, payload }),
            });

            if (!response.ok) {
                const err = await response.json();
                this.showError(err.detail || 'Transaction failed');
                return;
            }

            const result = await response.json();
            console.log('[App] Transaction submitted:', result);
        } catch (error) {
            this.showError('Transaction failed: ' + error.message);
        }
    }

    /**
     * Reset simulator
     */
    async reset() {
        if (!confirm('Reset simulator? All nodes and blocks will be cleared.')) return;

        try {
            await fetch(`${this.apiUrl}/reset`, { method: 'POST' });
            this.state = this.createInitialState();
            this.state.config = this.config;
            this.updateUI();
            console.log('[App] Simulator reset');
        } catch (error) {
            this.showError('Reset failed: ' + error.message);
        }
    }

    /**
     * Register all event handlers with dispatcher
     */
    registerEventHandlers() {
        const d = this.eventDispatcher;

        d.on('NODE_JOINED', (event) => {
            const p = event.payload;
            this.state.nodes.set(p.nodeId, {
                nodeId: p.nodeId,
                role: p.role,
                address: p.address,
                blockHeight: 0,
                syncStatus: 'syncing',
                isLeader: false,
            });
            this.state.metrics.totalNodes = this.state.nodes.size;
            this.updateUI();
            console.log('[Event] NODE_JOINED:', p.nodeId);
        });

        d.on('NODE_OFFLINE', (event) => {
            const p = event.payload;
            if (this.state.nodes.has(p.nodeId)) {
                const node = this.state.nodes.get(p.nodeId);
                node.syncStatus = 'offline';
            }
            this.updateUI();
            console.log('[Event] NODE_OFFLINE:', p.nodeId);
        });

        d.on('SYNC_PROGRESS', (event) => {
            const p = event.payload;
            if (this.state.nodes.has(p.nodeId)) {
                const node = this.state.nodes.get(p.nodeId);
                node.blockHeight = p.currentHeight || 0;
                node.syncStatus = 'syncing';
            }
            this.updateUI();
        });

        d.on('SYNC_COMPLETE', (event) => {
            const p = event.payload;
            if (this.state.nodes.has(p.nodeId)) {
                const node = this.state.nodes.get(p.nodeId);
                node.blockHeight = p.finalHeight || 0;
                node.syncStatus = 'synced';
            }
            this.updateUI();
        });

        d.on('TX_BROADCAST', (event) => {
            this.state.metrics.totalTransactions++;
            this.state.replayBuffer.push(event);
            this.updateUI();
            console.log('[Event] TX_BROADCAST:', event.payload.txId);
        });

        d.on('BLOCK_PROPOSED', (event) => {
            const p = event.payload;
            this.state.pendingBlock = {
                blockHeight: p.blockHeight,
                proposerNodeId: p.proposerNodeId,
                txCount: p.txCount,
            };
            this.updateUI();
            console.log('[Event] BLOCK_PROPOSED: block #' + p.blockHeight);
        });

        d.on('CONSENSUS_PHASE', (event) => {
            this.state.currentRound = event.payload.round || this.state.currentRound;
            this.updateUI();
        });

        d.on('VOTE_CAST', (event) => {
            this.updateUI();
        });

        d.on('BLOCK_COMMITTED', (event) => {
            const p = event.payload;
            this.state.blocks.push({
                blockNumber: p.blockHeight,
                blockHash: p.hash,
                proposer: p.proposerNodeId,
                txCount: p.txCount,
                commitTime: p.commitTime,
                timestamp: event.timestamp,
            });
            this.state.metrics.totalBlocks = this.state.blocks.length;
            this.state.pendingBlock = null;

            // Update all node heights
            for (const [nid, node] of this.state.nodes) {
                if (node.syncStatus === 'synced' || node.syncStatus === 'syncing') {
                    node.blockHeight = p.blockHeight;
                }
            }

            this.updateUI();
            console.log('[Event] BLOCK_COMMITTED: block #' + p.blockHeight + ' hash=' + (p.hash || '').substring(0, 8));
        });

        d.on('BLOCK_REJECTED', (event) => {
            this.state.pendingBlock = null;
            this.updateUI();
            console.log('[Event] BLOCK_REJECTED:', event.payload.reason);
        });

        d.on('LEADER_ELECTED', (event) => {
            const p = event.payload;
            // Update leader status
            for (const [nid, node] of this.state.nodes) {
                node.isLeader = (nid === p.nodeId);
            }
            this.updateUI();
            console.log('[Event] LEADER_ELECTED:', p.nodeId);
        });
    }

    /**
     * Set up UI event listeners
     */
    setupUIListeners() {
        // Load project button
        document.getElementById('btn-load-project').addEventListener('click', () => {
            const path = prompt('Enter path to config.yaml:');
            if (path) this.loadProject(path);
        });

        // Reset button
        document.getElementById('btn-reset').addEventListener('click', () => {
            this.reset();
        });

        // Add node button
        document.getElementById('btn-add-node').addEventListener('click', () => {
            const roles = this.config ? this.config.node_roles : ['full'];
            const role = prompt(`Enter node role (${roles.join(', ')}):`);
            if (role) this.addNode(role.toLowerCase());
        });

        // Speed slider
        document.getElementById('speed-slider').addEventListener('input', (e) => {
            this.state.speedMultiplier = parseFloat(e.target.value);
            document.getElementById('speed-display').textContent = this.state.speedMultiplier + 'x';
        });

        // Export trace
        document.getElementById('btn-export-trace').addEventListener('click', async () => {
            try {
                const response = await fetch(`${this.apiUrl}/export-trace`);
                const data = await response.json();
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'event_trace.json';
                a.click();
            } catch (error) {
                this.showError('Export failed: ' + error.message);
            }
        });
    }

    /**
     * Update config banner display
     */
    updateConfigBanner() {
        if (!this.config) return;
        const banner = document.getElementById('config-banner');
        banner.innerHTML = `
            <div><strong>Network:</strong> ${this.config.network_type}</div>
            <div><strong>Governance:</strong> ${this.config.governance}</div>
            <div><strong>Consensus:</strong> ${this.config.consensus}</div>
            <div><strong>Roles:</strong> ${this.config.node_roles.join(', ')}</div>
            <div><strong>Sync Mode:</strong> ${this.config.sync_mode}</div>
            <div><strong>Max Nodes:</strong> ${this.config.max_nodes}</div>
            <div><strong>Block Time:</strong> ${this.config.block_time_ms}ms</div>
            <div><strong>Modules:</strong> ${this.config.modules.join(', ') || 'none'}</div>
        `;
    }

    /**
     * Update all UI elements with current state
     */
    updateUI() {
        this.updateMetrics();
        this.updateNodeList();
        this.updateBlockList();
    }

    /**
     * Update metrics display
     */
    updateMetrics() {
        const m = this.state.metrics;
        const el = (id) => document.getElementById(id);

        if (el('metric-nodes-count')) el('metric-nodes-count').textContent = m.totalNodes;
        if (el('metric-blocks-count')) el('metric-blocks-count').textContent = m.totalBlocks;
        if (el('metric-transactions-count')) el('metric-transactions-count').textContent = m.totalTransactions;
        if (el('metric-tps')) el('metric-tps').textContent = m.currentTPS.toFixed(1);
        if (el('metric-consensus')) el('metric-consensus').textContent = m.consensusType || '-';
    }

    /**
     * Update the node list in the network panel
     */
    updateNodeList() {
        const container = document.getElementById('node-list');
        if (!container) return;

        container.classList.remove('hidden');
        let html = '<table style="width:100%; border-collapse:collapse;">';
        html += '<tr><th>Node</th><th>Role</th><th>Height</th><th>Status</th></tr>';

        for (const [nid, node] of this.state.nodes) {
            const statusColor = node.syncStatus === 'synced' ? 'green' :
                node.syncStatus === 'syncing' ? 'orange' : 'red';
            html += `<tr>
                <td>${node.nodeId}${node.isLeader ? ' 👑' : ''}</td>
                <td>${node.role}</td>
                <td>${node.blockHeight}</td>
                <td style="color:${statusColor}">${node.syncStatus}</td>
            </tr>`;
        }
        html += '</table>';
        container.innerHTML = html;
    }

    /**
     * Update the block list in the chain panel
     */
    updateBlockList() {
        const container = document.getElementById('block-list');
        if (!container) return;

        if (this.state.blocks.length === 0) {
            container.innerHTML = '<p style="color:#888;">No blocks committed yet</p>';
            return;
        }

        let html = '';
        // Show last 10 blocks, most recent first
        const recent = this.state.blocks.slice(-10).reverse();
        for (const block of recent) {
            html += `<div class="block-card" style="border:1px solid #ccc; padding:8px; margin:4px 0; border-radius:4px;">
                <strong>Block #${block.blockNumber}</strong>
                <span style="color:#888; margin-left:8px;">${(block.blockHash || '').substring(0, 12)}...</span>
                <div style="font-size:0.9em; color:#666;">
                    Proposer: ${block.proposer} | Txs: ${block.txCount}
                </div>
            </div>`;
        }
        container.innerHTML = html;
    }

    /**
     * Show error message
     */
    showError(message) {
        const area = document.getElementById('error-area');
        if (area) {
            area.innerHTML = `<div style="color:red; padding:8px; border:1px solid red; margin:4px 0; border-radius:4px;">${message}</div>`;
            setTimeout(() => { area.innerHTML = ''; }, 10000);
        }
        console.error('[Error]', message);
    }
}

// Initialize app on page load
document.addEventListener('DOMContentLoaded', async () => {
    const app = new SimulatorApp();
    await app.init();
    window.app = app; // Make available globally for debugging
});
