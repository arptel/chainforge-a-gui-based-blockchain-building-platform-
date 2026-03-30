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
        this.apiUrl = window.location.origin;
    }

    /**
     * Initialize the application
     */
    async init() {
        // Guard: file:// protocol cannot reach the backend
        if (window.location.protocol === 'file:') {
            document.body.innerHTML = `
                <div style="display:flex;align-items:center;justify-content:center;height:100vh;background:#f5f5f5;font-family:sans-serif;">
                    <div style="text-align:center;max-width:500px;padding:40px;background:#fff;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
                        <div style="font-size:48px;margin-bottom:20px;">🔒</div>
                        <h2 style="margin-bottom:12px;color:#1a1a1a;">Browser Security Guard</h2>
                        <p style="color:#666;margin-bottom:24px;line-height:1.5;">
                            The simulator is running as a <b>file://</b> which blocks communication with the backend. 
                            You must use the web URL instead.
                        </p>
                        <p style="font-size:13px;color:#888;margin-bottom:8px;">Check your <b>PowerShell/Terminal</b> for a line like:</p>
                        <code style="display:block;padding:12px;background:#f8f9fa;border:1px solid #eee;border-radius:6px;font-size:14px;color:#2563eb;font-weight:bold;">
                            http://localhost:8000/static/index.html
                        </code>
                        <p style="margin-top:20px;font-size:12px;color:#aaa;">(The port might be 8000, 8001, or 8002 depending on availability)</p>
                    </div>
                </div>`;
            return;
        }

        // Set up event dispatcher
        this.eventDispatcher = new EventDispatcher();

        // Register all event handlers
        this.registerEventHandlers();

        // Set up UI event listeners
        this.setupUIListeners();

        // Set up WebSocket client
        this.wsClient = new WebSocketClient(this.apiUrl);
        this.wsClient.setDispatcher(this.eventDispatcher);

        // Wire connection status into the status banner
        this.wsClient.onStatusChange = (status) => {
            const badge = document.getElementById('status-badge');
            const statusText = document.getElementById('status-text');
            if (status === 'connected') {
                badge.textContent = 'Connected';
                badge.className = 'badge badge-success';
                statusText.textContent = this.config
                    ? `${this.config.consensus.toUpperCase()} consensus | ${this.config.network_type}`
                    : 'WebSocket connected';
            } else if (status === 'reconnecting') {
                badge.textContent = 'Connecting…';
                badge.className = 'badge badge-warning';
                statusText.textContent = 'Reconnecting to backend…';
            } else if (status === 'disconnected') {
                badge.textContent = 'Disconnected';
                badge.className = 'badge badge-danger';
                statusText.textContent = 'Lost connection to backend';
            }
        };

        // Check if project is already loaded in backend
        try {
            const resp = await fetch(`${this.apiUrl}/project`);
            if (resp.ok) {
                const data = await resp.json();
                if (data.status === 'loaded') {
                    this.config = data;
                    this.state.config = data;
                    this.state.metrics.consensusType = data.consensus;
                    this.updateConfigBanner();

                    // Enable buttons
                    document.getElementById('btn-add-node').disabled = false;
                    document.getElementById('btn-reset').disabled = false;
                    document.getElementById('btn-export-trace').disabled = false;
                    document.getElementById('speed-slider').disabled = false;

                    // Update status
                    const badge = document.getElementById('status-badge');
                    const statusText = document.getElementById('status-text');
                    badge.textContent = 'Loaded';
                    badge.className = 'badge badge-success';
                    statusText.textContent = `${data.consensus.toUpperCase()} consensus | ${data.network_type}`;

                    // Connect WebSocket
                    this.wsClient.connect();
                    console.log('[App] Auto-loaded existing project');
                }
            }
        } catch (e) {
            console.warn('[App] Could not check project status:', e);
        }

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
                blocks: [],
                logs: [{ time: event.timestamp, msg: `Node joined as ${p.role}` }],
                balance: 100, // Default initial balance
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
                node.logs.push({ time: event.timestamp, msg: 'Node went offline' });
            }
            this.updateUI();
            console.log('[Event] NODE_OFFLINE:', p.nodeId);
        });

        d.on('SYNC_PROGRESS', (event) => {
            const p = event.payload;
            if (this.state.nodes.has(p.nodeId)) {
                const node = this.state.nodes.get(p.nodeId);
                node.blockHeight = p.currentHeight || 0;
                
                if (p.blockData) {
                    node.blocks.push({
                        blockNumber: p.blockData.blockHeight,
                        blockHash: p.blockData.hash,
                        proposer: p.blockData.proposerNodeId,
                        txCount: p.blockData.txCount,
                        commitTime: p.blockData.commitTime,
                        timestamp: event.timestamp,
                    });
                }
                
                if (node.blockHeight >= (p.targetHeight || 0)) {
                    node.syncStatus = 'synced';
                } else {
                    node.syncStatus = 'syncing';
                }
                
                if (p.balances) {
                    for (const [addr, bal] of Object.entries(p.balances)) {
                        if (this.state.nodes.has(addr)) {
                            this.state.nodes.get(addr).balance = bal;
                        }
                    }
                }
                
                node.logs.push({ time: event.timestamp, msg: `Syncing... height=${p.currentHeight || 0} of ${p.targetHeight || 0}` });
            }
            this.updateUI();
        });

        d.on('SYNC_COMPLETE', (event) => {
            const p = event.payload;
            if (this.state.nodes.has(p.nodeId)) {
                const node = this.state.nodes.get(p.nodeId);
                node.blockHeight = p.finalHeight || 0;
                node.syncStatus = 'synced';
                node.logs.push({ time: event.timestamp, msg: `Sync complete at height=${p.finalHeight || 0}` });
            }
            this.updateUI();
        });

        d.on('TX_BROADCAST', (event) => {
            const p = event.payload;
            this.state.metrics.totalTransactions++;
            this.state.replayBuffer.push(event);
            // Log to sender node
            if (p.fromNodeId && this.state.nodes.has(p.fromNodeId)) {
                this.state.nodes.get(p.fromNodeId).logs.push({ time: event.timestamp, msg: `Broadcasted tx ${(p.txId || '').substring(0, 8)}` });
            }
            // Log to all other nodes as "received"
            for (const [nid, node] of this.state.nodes) {
                if (nid !== p.fromNodeId) {
                    node.logs.push({ time: event.timestamp, msg: `Received tx ${(p.txId || '').substring(0, 8)}` });
                }
            }
            this.updateUI();
            console.log('[Event] TX_BROADCAST:', p.txId);
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
            const blockData = {
                blockNumber: p.blockHeight,
                blockHash: p.hash,
                proposer: p.proposerNodeId,
                txCount: p.txCount,
                commitTime: p.commitTime,
                timestamp: event.timestamp,
            };
            this.state.blocks.push(blockData);
            this.state.metrics.totalBlocks = this.state.blocks.length;
            this.state.pendingBlock = null;

            // Update all nodes balances if provided
            if (p.balances) {
                for (const [addr, bal] of Object.entries(p.balances)) {
                    if (this.state.nodes.has(addr)) {
                        this.state.nodes.get(addr).balance = bal;
                    }
                }
            }

            // Update all node heights + per-node blocks and logs
            for (const [nid, node] of this.state.nodes) {
                if (node.syncStatus === 'synced' || node.syncStatus === 'syncing') {
                    node.blockHeight = p.blockHeight;
                    node.blocks.push(blockData);
                    if (nid === p.proposerNodeId) {
                        node.logs.push({ time: event.timestamp, msg: `Proposed & committed block #${p.blockHeight}` });
                    } else {
                        node.logs.push({ time: event.timestamp, msg: `Received block #${p.blockHeight} from ${p.proposerNodeId || 'unknown'}` });
                    }
                }
            }

            this.updateUI();
            console.log('[Event] BLOCK_COMMITTED: block #' + p.blockHeight + ' hash=' + (p.hash || '').substring(0, 8));
        });

        d.on('BLOCK_REJECTED', (event) => {
            const p = event.payload;
            this.state.pendingBlock = null;
            // Log rejection to all nodes
            for (const [nid, node] of this.state.nodes) {
                node.logs.push({ time: event.timestamp, msg: `Block rejected: ${p.reason || 'unknown reason'}` });
            }
            this.updateUI();
            console.log('[Event] BLOCK_REJECTED:', p.reason);
        });

        d.on('LEADER_ELECTED', (event) => {
            const p = event.payload;
            // Update leader status
            for (const [nid, node] of this.state.nodes) {
                node.isLeader = (nid === p.nodeId);
                if (nid === p.nodeId) {
                    node.logs.push({ time: event.timestamp, msg: 'Elected as leader' });
                }
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
            this.showLoadModal();
        });

        // Reset button
        document.getElementById('btn-reset').addEventListener('click', () => {
            this.reset();
        });

        // Add node button — dropdown menu
        const addNodeBtn = document.getElementById('btn-add-node');
        addNodeBtn.addEventListener('click', (e) => {
            if (!this.config) {
                this.showError('Load a project first before adding nodes.');
                return;
            }
            // Remove existing dropdown if open
            const existing = document.getElementById('role-dropdown');
            if (existing) { existing.remove(); return; }

            const roles = this.config ? this.config.node_roles : ['full'];
            const dropdown = document.createElement('div');
            dropdown.id = 'role-dropdown';
            dropdown.style.cssText = 'position:absolute; background:#2a2a2e; border:1px solid #555; border-radius:6px; padding:4px 0; z-index:100; min-width:130px; box-shadow:0 4px 12px rgba(0,0,0,0.4);';

            // Position below button
            const rect = addNodeBtn.getBoundingClientRect();
            dropdown.style.top = (rect.bottom + 4) + 'px';
            dropdown.style.left = rect.left + 'px';

            roles.forEach(r => {
                const item = document.createElement('div');
                item.textContent = r.charAt(0).toUpperCase() + r.slice(1);
                item.style.cssText = 'padding:8px 16px; cursor:pointer; color:#e0e0e0; font-size:0.9em;';
                item.addEventListener('mouseenter', () => item.style.background = '#444');
                item.addEventListener('mouseleave', () => item.style.background = 'none');
                item.addEventListener('click', () => {
                    dropdown.remove();
                    this.addNode(r.toLowerCase());
                });
                dropdown.appendChild(item);
            });

            document.body.appendChild(dropdown);

            // Close on outside click
            const closeHandler = (ev) => {
                if (!dropdown.contains(ev.target) && ev.target !== addNodeBtn) {
                    dropdown.remove();
                    document.removeEventListener('click', closeHandler);
                }
            };
            setTimeout(() => document.addEventListener('click', closeHandler), 0);
        });

        // Speed slider
        document.getElementById('speed-slider').addEventListener('input', (e) => {
            this.state.speedMultiplier = parseFloat(e.target.value);
            document.getElementById('speed-display').textContent = this.state.speedMultiplier + 'x';
        });

        // Close node detail panel
        document.getElementById('btn-close-detail').addEventListener('click', () => {
            this.state.selectedNodeId = null;
            this.updateNodeDetail();
            this.updateNodeList();
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
        if (el('metric-consensus')) el('metric-consensus').textContent = (this.config && this.config.consensus) ? this.config.consensus.toUpperCase() : '-';
    }

    /**
     * Update the node list in the network panel (visual cards)
     */
    updateNodeList() {
        const container = document.getElementById('network-view-container');
        if (!container) return;

        // Hide the canvas, use the container directly
        const canvas = document.getElementById('network-canvas');
        if (canvas) canvas.style.display = 'none';

        // Preserve or create the node-cards wrapper
        let wrapper = document.getElementById('node-cards-wrapper');
        if (!wrapper) {
            wrapper = document.createElement('div');
            wrapper.id = 'node-cards-wrapper';
            wrapper.style.cssText = 'display:flex; flex-wrap:wrap; gap:12px; padding:12px; align-items:flex-start; min-height:120px;';
            container.appendChild(wrapper);
        }

        if (this.state.nodes.size === 0) {
            wrapper.innerHTML = '<p style="color:#888; width:100%; text-align:center;">No nodes running. Click \"+ Add Node\" to start.</p>';
            return;
        }

        let html = '';
        for (const [nid, node] of this.state.nodes) {
            const statusColor = node.syncStatus === 'synced' ? '#4caf50' :
                node.syncStatus === 'syncing' ? '#ff9800' : '#f44336';
            const roleIcon = node.role === 'validator' ? '🔒' :
                node.role === 'miner' ? '⛏️' :
                node.role === 'light' ? '💡' : '🖥️';
            const leaderBadge = node.isLeader ? '<span style="margin-left:4px;" title="Leader">👑</span>' : '';

            const isSelected = nid === this.state.selectedNodeId;
            const borderCol = isSelected ? '#7c4dff' : '#444';

            html += `<div data-node-id="${nid}" style="background:#2a2a2e; border:2px solid ${borderCol}; border-radius:8px; padding:12px 16px; min-width:150px; cursor:pointer; transition:border-color 0.2s;"
                         onmouseenter="if(!this.dataset.selected) this.style.borderColor='#7c4dff'" onmouseleave="if(!this.dataset.selected) this.style.borderColor='#444'" ${isSelected ? 'data-selected="1"' : ''}>
                <div style="display:flex; align-items:center; gap:6px; margin-bottom:6px;">
                    <span style="font-size:1.3em;">${roleIcon}</span>
                    <strong style="color:#e0e0e0; font-size:0.95em;">${node.nodeId}</strong>
                    ${leaderBadge}
                </div>
                <div style="font-size:0.8em; color:#aaa; margin-bottom:4px;">Role: ${node.role}</div>
                <div style="font-size:0.8em; color:#aaa; margin-bottom:4px;">Height: ${node.blockHeight}</div>
                <div style="font-size:0.8em; color:#4db6ac; margin-bottom:6px; font-weight:bold;">Balance: ${node.balance} 🪙</div>
                <div style="display:flex; align-items:center; gap:4px; font-size:0.8em;">
                    <span style="width:8px; height:8px; border-radius:50%; background:${statusColor}; display:inline-block;"></span>
                    <span style="color:${statusColor};">${node.syncStatus}</span>
                </div>
            </div>`;
        }
        wrapper.innerHTML = html;

        // Attach click handlers to node cards
        wrapper.querySelectorAll('[data-node-id]').forEach(card => {
            card.addEventListener('click', () => {
                this.selectNode(card.dataset.nodeId);
            });
        });
    }

    /**
     * Select a node and show its details
     */
    selectNode(nodeId) {
        this.state.selectedNodeId = nodeId;
        this.updateNodeDetail();
        this.updateNodeList(); // refresh selection highlight
    }

    /**
     * Update node detail panel with selected node info and transaction form
     */
    updateNodeDetail() {
        const detailDiv = document.getElementById('node-detail');
        const actionsDiv = document.getElementById('node-actions');
        if (!detailDiv) return;

        const nodeId = this.state.selectedNodeId;
        if (!nodeId || !this.state.nodes.has(nodeId)) {
            detailDiv.innerHTML = '<p class="placeholder">Select a node to view details</p>';
            if (actionsDiv) actionsDiv.classList.add('hidden');
            return;
        }

        const node = this.state.nodes.get(nodeId);
        const statusColor = node.syncStatus === 'synced' ? '#4caf50' :
            node.syncStatus === 'syncing' ? '#ff9800' : '#f44336';

        // Build list of other nodes for the recipient dropdown
        let recipientOptions = '';
        for (const [nid] of this.state.nodes) {
            if (nid !== nodeId) {
                recipientOptions += `<option value="${nid}">${nid}</option>`;
            }
        }

        // Build per-node block list (last 10)
        const nodeBlocks = (node.blocks || []).slice(-10).reverse();
        let blocksHtml = '';
        if (nodeBlocks.length === 0) {
            blocksHtml = '<p style="color:#888; font-size:0.8em;">No blocks received yet</p>';
        } else {
            for (const b of nodeBlocks) {
                blocksHtml += `<div class="node-block-item">
                    <strong>#${b.blockNumber}</strong>
                    <span style="color:#888; margin-left:4px;">${(b.blockHash || '').substring(0, 10)}...</span>
                    <div style="font-size:0.75em; color:#666;">Proposer: ${b.proposer || '?'} | Txs: ${b.txCount || 0}</div>
                </div>`;
            }
        }

        // Build per-node log list (last 20)
        const nodeLogs = (node.logs || []).slice(-20).reverse();
        let logsHtml = '';
        if (nodeLogs.length === 0) {
            logsHtml = '<p style="color:#888; font-size:0.8em;">No log entries yet</p>';
        } else {
            for (const log of nodeLogs) {
                const t = new Date(log.time).toLocaleTimeString();
                logsHtml += `<div class="node-log-item"><span class="log-time">${t}</span> ${log.msg}</div>`;
            }
        }

        detailDiv.innerHTML = `
            <div style="margin-bottom:12px;">
                <div style="font-size:1.1em; font-weight:bold; margin-bottom:8px;">${node.nodeId}</div>
                <div style="font-size:0.85em; color:#666; margin-bottom:4px;"><strong>Role:</strong> ${node.role}</div>
                <div style="font-size:0.85em; color:#666; margin-bottom:4px;"><strong>Address:</strong> ${node.address || 'N/A'}</div>
                <div style="font-size:0.85em; color:#666; margin-bottom:4px;"><strong>Height:</strong> ${node.blockHeight}</div>
                <div style="font-size:0.85em; color:#4db6ac; margin-bottom:4px;"><strong>Balance:</strong> ${node.balance} 🪙</div>
                <div style="font-size:0.85em; margin-bottom:4px;">
                    <strong>Status:</strong> <span style="color:${statusColor};">${node.syncStatus}</span>
                </div>
            </div>
            <hr style="border-color:#ddd; margin:12px 0;">
            <div style="margin-bottom:8px; font-weight:bold;">Send Transaction</div>
            <div style="display:flex; flex-direction:column; gap:8px; margin-bottom:12px;">
                <select id="tx-recipient" style="padding:6px 8px; border:1px solid #ccc; border-radius:4px; font-size:12px;">
                    ${recipientOptions || '<option value="">No other nodes</option>'}
                </select>
                <input id="tx-amount" type="number" placeholder="Amount" value="10" style="padding:6px 8px; border:1px solid #ccc; border-radius:4px; font-size:12px;">
                <input id="tx-memo" type="text" placeholder="Memo (optional)" style="padding:6px 8px; border:1px solid #ccc; border-radius:4px; font-size:12px;">
                <button id="btn-send-tx" class="btn btn-primary" style="padding:8px;">Submit Transaction</button>
            </div>
            <hr style="border-color:#ddd; margin:12px 0;">
            <div style="font-weight:bold; margin-bottom:6px;">📦 Blocks (${(node.blocks || []).length})</div>
            <div class="node-block-list">${blocksHtml}</div>
            <hr style="border-color:#ddd; margin:12px 0;">
            <div style="font-weight:bold; margin-bottom:6px;">📋 Logs (${(node.logs || []).length})</div>
            <div class="node-log-list">${logsHtml}</div>
        `;

        // Wire up Send button
        document.getElementById('btn-send-tx').addEventListener('click', () => {
            const to = document.getElementById('tx-recipient').value;
            const amount = parseFloat(document.getElementById('tx-amount').value) || 0;
            const memo = document.getElementById('tx-memo').value || '';
            this.submitTransaction(nodeId, to, { amount, memo });
        });

        // Show attack actions
        if (actionsDiv) actionsDiv.classList.remove('hidden');
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
     * Show error message (auto-dismiss after 5s)
     */
    showError(message) {
        const area = document.getElementById('error-area');
        if (!area) return;
        area.textContent = message;
        area.classList.add('active');
        clearTimeout(this._errorTimer);
        this._errorTimer = setTimeout(() => area.classList.remove('active'), 5000);
        console.error('[Error]', message);
    }

    /**
     * Show the Load Project modal
     */
    showLoadModal() {
        const overlay = document.getElementById('load-project-modal');
        const input   = document.getElementById('modal-config-path');
        overlay.classList.remove('hidden');
        input.value = '';
        input.focus();

        const close = () => overlay.classList.add('hidden');

        // OK button
        document.getElementById('modal-ok').onclick = () => {
            const path = input.value.trim();
            if (path) { close(); this.loadProject(path); }
        };

        // Cancel button
        document.getElementById('modal-cancel').onclick = close;

        // Enter key submits
        input.onkeydown = (e) => {
            if (e.key === 'Enter') {
                const path = input.value.trim();
                if (path) { close(); this.loadProject(path); }
            }
        };

        // Click backdrop to cancel
        overlay.onclick = (e) => { if (e.target === overlay) close(); };
    }
}

// Initialize app on page load
document.addEventListener('DOMContentLoaded', async () => {
    const app = new SimulatorApp();
    await app.init();
    window.app = app; // Make available globally for debugging
});
