/**
 * ChainForge Simulator — Frontend Application
 * ==============================================
 * Auto-loads chain config on page open, renders Kn graph on canvas,
 * handles node detail panel, consensus phase indicator, packet animations,
 * voting UI, and transaction submission.
 */

(() => {
    "use strict";

    // ================================================================
    // CONFIG & STATE
    // ================================================================
    const API = window.location.origin;
    const WS_URL = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/events`;

    const state = {
        chainInfo: null,
        nodes: [],           // [{node_id, role, status, height}]
        selectedNode: null,  // node_id currently shown in detail panel
        pendingJoins: [],
        ws: null,
        wsReconnectTimer: null,
    };

    // Canvas/graph state
    const graph = {
        canvas: null,
        ctx: null,
        nodePositions: {},   // node_id -> {x, y}
        animations: [],      // active packet animations
        animFrameId: null,
        nodeRadius: 28,
    };

    // Phase bar state
    const phaseState = {
        phases: [],
        currentIndex: -1,
        resetTimer: null,
    };

    // ================================================================
    // DOM ELEMENTS
    // ================================================================
    const $ = (id) => document.getElementById(id);

    const DOM = {
        statusLine:    $("status-line"),
        btnInfo:       $("btn-info"),
        btnAddNode:    $("btn-add-node"),
        addNodeMenu:   $("add-node-menu"),
        addNodeWrapper:$("add-node-wrapper"),
        btnReset:      $("btn-reset"),
        noChainMsg:    $("no-chain-msg"),
        loadingMsg:    $("loading-msg"),
        workspace:     $("workspace"),
        canvas:        $("graph-canvas"),
        phaseBar:      $("phase-bar"),
        phaseName:     $("phase-consensus-name"),
        phaseDots:     $("phase-dots"),
        detailPanel:   $("detail-panel"),
        detailContent: $("detail-content"),
        btnCloseDetail:$("btn-close-detail"),
        footer:        $("footer"),
        statNodes:     $("stat-nodes"),
        statBlocks:    $("stat-blocks"),
        statConsensus: $("stat-consensus"),
        infoOverlay:   $("info-modal-overlay"),
        infoBody:      $("info-modal-body"),
        btnCloseModal: $("btn-close-modal"),
    };

    // ================================================================
    // INIT
    // ================================================================
    document.addEventListener("DOMContentLoaded", init);

    async function init() {
        setupEventListeners();
        await loadChainInfo();
    }

    function setupEventListeners() {
        // Info modal
        DOM.btnInfo.addEventListener("click", showInfoModal);
        DOM.btnCloseModal.addEventListener("click", hideInfoModal);
        DOM.infoOverlay.addEventListener("click", (e) => {
            if (e.target === DOM.infoOverlay) hideInfoModal();
        });

        // Add node dropdown
        DOM.btnAddNode.addEventListener("click", toggleAddNodeMenu);
        document.addEventListener("click", (e) => {
            if (!DOM.addNodeWrapper.contains(e.target)) {
                DOM.addNodeMenu.classList.add("hidden");
            }
        });

        // Reset
        DOM.btnReset.addEventListener("click", resetNetwork);

        // Close detail panel
        DOM.btnCloseDetail.addEventListener("click", closeDetailPanel);

        // Canvas click — detect which node was clicked
        DOM.canvas.addEventListener("click", (e) => {
            const rect = DOM.canvas.getBoundingClientRect();
            const mx = e.clientX - rect.left;
            const my = e.clientY - rect.top;

            for (const node of state.nodes) {
                const pos = graph.nodePositions[node.node_id];
                if (!pos) continue;
                const dx = mx - pos.x;
                const dy = my - pos.y;
                if (dx * dx + dy * dy < (graph.nodeRadius + 8) ** 2) {
                    showNodeDetail(node.node_id);
                    return;
                }
            }
            // Click on empty space — close panel
            closeDetailPanel();
        });

        // Canvas resize
        window.addEventListener("resize", resizeCanvas);
    }


    // ================================================================
    // AUTO-LOAD
    // ================================================================
    async function loadChainInfo() {
        try {
            const resp = await fetch(`${API}/chain-info`);
            if (!resp.ok) throw new Error("No chain");
            state.chainInfo = await resp.json();
        } catch {
            DOM.loadingMsg.classList.add("hidden");
            DOM.noChainMsg.classList.remove("hidden");
            return;
        }

        DOM.loadingMsg.classList.add("hidden");
        DOM.workspace.classList.remove("hidden");

        // Update UI with chain info
        const ci = state.chainInfo;
        DOM.statusLine.textContent =
            `${ci.consensus.toUpperCase()} consensus | ${capitalize(ci.governance)} | Loading nodes…`;
        DOM.statConsensus.textContent = `Consensus: ${ci.consensus.toUpperCase()}`;

        // Enable buttons
        DOM.btnInfo.disabled = false;
        DOM.btnReset.disabled = false;

        // Build Add Node dropdown
        buildAddNodeMenu(ci);

        // Setup phase bar
        setupPhaseBar(ci);

        // Init canvas
        graph.canvas = DOM.canvas;
        graph.ctx = graph.canvas.getContext("2d");
        resizeCanvas();

        // Load existing nodes
        await refreshNodes();

        // Connect WebSocket
        connectWS();
    }

    function buildAddNodeMenu(ci) {
        DOM.addNodeMenu.innerHTML = "";

        // For centralized: Add-Node is via node-0 detail panel, disable toolbar button
        if (ci.governance === "centralized") {
            DOM.btnAddNode.disabled = true;
            DOM.btnAddNode.title = "Use the owner node (node-0) to add nodes";
            return;
        }

        ci.node_roles.forEach((role) => {
            const btn = document.createElement("button");
            btn.textContent = capitalize(role);
            btn.addEventListener("click", () => addNode(role));
            DOM.addNodeMenu.appendChild(btn);
        });
        DOM.btnAddNode.disabled = false;
    }

    // ================================================================
    // PHASE BAR
    // ================================================================
    function setupPhaseBar(ci) {
        phaseState.phases = ci.consensus_phases || ["COMMIT"];
        phaseState.currentIndex = -1;
        DOM.phaseName.textContent = `Consensus: ${ci.consensus.toUpperCase()}`;
        renderPhaseBar();
    }

    function renderPhaseBar() {
        DOM.phaseDots.innerHTML = "";
        phaseState.phases.forEach((name, i) => {
            if (i > 0) {
                const arrow = document.createElement("span");
                arrow.className = "phase-arrow";
                arrow.textContent = "→";
                DOM.phaseDots.appendChild(arrow);
            }
            const dot = document.createElement("span");
            dot.className = "phase-dot";
            dot.id = `phase-${i}`;
            if (i < phaseState.currentIndex) dot.classList.add("complete");
            if (i === phaseState.currentIndex) dot.classList.add("active");
            dot.innerHTML = `<span class="dot"></span> ${name}`;
            DOM.phaseDots.appendChild(dot);
        });
    }

    function advancePhase(phaseName) {
        const idx = phaseState.phases.findIndex(
            (p) => p.toLowerCase() === phaseName.toLowerCase()
        );
        if (idx === -1) return;
        phaseState.currentIndex = idx;
        renderPhaseBar();

        // If last phase, schedule reset
        if (idx === phaseState.phases.length - 1) {
            clearTimeout(phaseState.resetTimer);
            phaseState.resetTimer = setTimeout(() => {
                phaseState.currentIndex = -1;
                renderPhaseBar();
            }, 1500);
        }
    }

    // ================================================================
    // NODE OPERATIONS
    // ================================================================
    async function refreshNodes() {
        try {
            const resp = await fetch(`${API}/nodes`);
            const data = await resp.json();
            state.nodes = data.nodes || [];
        } catch {
            state.nodes = [];
        }
        updateFooter();
        drawGraph();

        // Also refresh pending joins
        try {
            const resp = await fetch(`${API}/pending-joins`);
            const data = await resp.json();
            state.pendingJoins = data.pending || [];
        } catch {
            state.pendingJoins = [];
        }

        // If detail panel is open, refresh it
        if (state.selectedNode) {
            showNodeDetail(state.selectedNode);
        }
    }

    async function addNode(role) {
        DOM.addNodeMenu.classList.add("hidden");
        try {
            const resp = await fetch(`${API}/nodes`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ role }),
            });
            const data = await resp.json();
            if (!resp.ok) { alert(data.detail || "Failed to add node"); return; }

            if (data.status === "pending") {
                await refreshNodes();
            } else {
                await refreshNodes();
            }
        } catch (e) {
            alert("Error adding node: " + e.message);
        }
    }

    async function removeNode(nodeId) {
        if (!confirm(`Remove ${nodeId}?`)) return;
        try {
            await fetch(`${API}/nodes/${nodeId}`, { method: "DELETE" });
            if (state.selectedNode === nodeId) closeDetailPanel();
            await refreshNodes();
        } catch (e) {
            alert("Error: " + e.message);
        }
    }

    async function submitTransaction(fromNodeId, text) {
        try {
            const resp = await fetch(`${API}/transaction`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ fromNodeId, text }),
            });
            const data = await resp.json();
            if (!resp.ok) { alert(data.detail || "Transaction failed"); return; }
            await refreshNodes();
        } catch (e) {
            alert("Error: " + e.message);
        }
    }

    async function voteOnJoin(voterNodeId, requestId, approve) {
        try {
            const resp = await fetch(`${API}/nodes/vote`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ voterNodeId, requestId, approve }),
            });
            if (!resp.ok) {
                const data = await resp.json();
                alert(data.detail || "Vote failed");
                return;
            }
            await refreshNodes();
        } catch (e) {
            alert("Error: " + e.message);
        }
    }

    async function resetNetwork() {
        if (!confirm("Reset the entire network? All nodes and data will be deleted.")) return;
        try {
            await fetch(`${API}/reset`, { method: "POST" });
            closeDetailPanel();
            await refreshNodes();
        } catch (e) {
            alert("Error: " + e.message);
        }
    }

    // ================================================================
    // WEBSOCKET
    // ================================================================
    function connectWS() {
        if (state.ws) { try { state.ws.close(); } catch {} }
        const ws = new WebSocket(WS_URL);

        ws.onopen = () => {
            console.log("[WS] Connected");
            clearTimeout(state.wsReconnectTimer);
        };

        ws.onmessage = (event) => {
            try {
                const ev = JSON.parse(event.data);
                handleEvent(ev);
            } catch {}
        };

        ws.onclose = () => {
            console.log("[WS] Disconnected, reconnecting in 2s…");
            state.wsReconnectTimer = setTimeout(connectWS, 2000);
        };

        ws.onerror = () => { ws.close(); };
        state.ws = ws;
    }

    function handleEvent(ev) {
        switch (ev.type) {
            case "NODE_JOINED":
            case "NODE_OFFLINE":
            case "SYNC_COMPLETE":
            case "NODE_OFFLINE":
            case "NODE_ONLINE":
                refreshNodes();
                break;

            case "TX_BROADCAST":
                // Animate blue dots from sender to all
                if (ev.payload && ev.payload.fromNodeId) {
                    animatePackets(ev.payload.fromNodeId, "#2563eb");
                }
                refreshNodes();
                break;

            case "BLOCK_PROPOSED":
                break;

            case "BLOCK_COMMITTED":
                // Animate green dots from proposer to all
                if (ev.payload && ev.payload.proposerNodeId) {
                    animatePackets(ev.payload.proposerNodeId, "#16a34a");
                }
                refreshNodes();
                break;

            case "VOTE_CAST":
                break;

            case "CONSENSUS_PHASE":
                if (ev.payload && ev.payload.phase) {
                    advancePhase(ev.payload.phase);
                }
                break;

            case "JOIN_REQUEST":
            case "JOIN_VOTE":
                refreshNodes();
                break;
        }
    }

    // ================================================================
    // CANVAS — Kn GRAPH
    // ================================================================
    function resizeCanvas() {
        if (!graph.canvas) return;
        const container = graph.canvas.parentElement;
        const dpr = window.devicePixelRatio || 1;
        graph.canvas.width = container.clientWidth * dpr;
        graph.canvas.height = container.clientHeight * dpr;
        graph.canvas.style.width = container.clientWidth + "px";
        graph.canvas.style.height = container.clientHeight + "px";
        graph.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        drawGraph();
    }

    function drawGraph() {
        const ctx = graph.ctx;
        if (!ctx) return;
        const w = graph.canvas.clientWidth;
        const h = graph.canvas.clientHeight;

        ctx.clearRect(0, 0, w, h);

        const nodes = state.nodes;
        if (!nodes.length) {
            ctx.fillStyle = "#999";
            ctx.font = "14px system-ui";
            ctx.textAlign = "center";
            ctx.fillText("No nodes running. Click '+ Add Node' to start.", w / 2, h / 2);
            return;
        }

        // Calculate positions: circular layout
        const cx = w / 2 - (state.selectedNode ? 160 : 0);
        const cy = h / 2;
        const maxR = Math.min(cx - 60, cy - 60, 220);
        const radius = nodes.length === 1 ? 0 : maxR;

        graph.nodePositions = {};
        nodes.forEach((node, i) => {
            const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
            graph.nodePositions[node.node_id] = {
                x: cx + radius * Math.cos(angle),
                y: cy + radius * Math.sin(angle),
            };
        });

        // Draw edges (Kn complete graph)
        ctx.strokeStyle = "#e0e0e0";
        ctx.lineWidth = 1;
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const a = graph.nodePositions[nodes[i].node_id];
                const b = graph.nodePositions[nodes[j].node_id];
                ctx.beginPath();
                ctx.moveTo(a.x, a.y);
                ctx.lineTo(b.x, b.y);
                ctx.stroke();
            }
        }

        // Draw nodes
        nodes.forEach((node) => {
            const pos = graph.nodePositions[node.node_id];
            drawNode(ctx, pos.x, pos.y, node);
        });
    }

    function drawNode(ctx, x, y, node) {
        const r = graph.nodeRadius;
        const isSelected = state.selectedNode === node.node_id;
        const isLight = node.role === "light";
        const isValidator = node.role === "validator" || node.role === "miner";
        const isOwner = node.node_id === "node-0" &&
            state.chainInfo && state.chainInfo.governance !== "decentralized";

        // Circle
        ctx.beginPath();
        ctx.arc(x, y, isLight ? r - 4 : (isValidator ? r + 2 : r), 0, 2 * Math.PI);

        const isOffline = node.status === "offline";

        // Fill
        ctx.fillStyle = isSelected ? "#eef2ff" : (isOffline ? "#e5e7eb" : "#fff");
        ctx.fill();

        // Border
        ctx.lineWidth = isValidator ? 2.5 : (isLight ? 1.5 : 2);
        if (isLight || isOffline) ctx.setLineDash([4, 3]);
        else ctx.setLineDash([]);

        ctx.strokeStyle = isOffline ? "#9ca3af" : (isSelected ? "#2563eb" :
            (isValidator ? "#2563eb" :
            (isLight ? "#aaa" : "#555")));
        ctx.stroke();
        ctx.setLineDash([]);

        // Owner badge (crown)
        if (isOwner) {
            ctx.font = "12px system-ui";
            ctx.textAlign = "center";
            ctx.fillStyle = "#ca8a04";
            ctx.fillText("👑", x, y - r - 6);
        }

        // Notification badge for pending join votes
        const hasPendingVote = state.pendingJoins.some(j =>
            !j.votes[node.node_id] && isVoter(node)
        );
        if (hasPendingVote) {
            ctx.beginPath();
            ctx.arc(x + r - 2, y - r + 2, 5, 0, 2 * Math.PI);
            ctx.fillStyle = "#dc2626";
            ctx.fill();
            ctx.strokeStyle = "#fff";
            ctx.lineWidth = 1.5;
            ctx.stroke();
        }

        // Node ID text
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.font = "bold 11px 'Segoe UI', system-ui";
        ctx.fillStyle = "#1a1a1a";
        ctx.fillText(node.node_id, x, y - 4);

        // Role text
        ctx.font = "10px 'Segoe UI', system-ui";
        ctx.fillStyle = "#888";
        ctx.fillText(node.role, x, y + 10);
    }

    function isVoter(node) {
        if (!state.chainInfo) return false;
        const mech = state.chainInfo.join_mechanism;
        if (mech === "ca" || mech === "owner") return node.node_id === "node-0";
        return node.role === "validator" || node.role === "miner";
    }

    // Canvas click handler is now in setupEventListeners()

    // ================================================================
    // PACKET ANIMATIONS
    // ================================================================
    function animatePackets(fromNodeId, color) {
        const fromPos = graph.nodePositions[fromNodeId];
        if (!fromPos) return;

        state.nodes.forEach((node) => {
            if (node.node_id === fromNodeId) return;
            const toPos = graph.nodePositions[node.node_id];
            if (!toPos) return;

            graph.animations.push({
                fromX: fromPos.x, fromY: fromPos.y,
                toX: toPos.x, toY: toPos.y,
                color,
                progress: 0,
                speed: 0.03,  // ~33 frames to complete
            });
        });

        if (!graph.animFrameId) {
            graph.animFrameId = requestAnimationFrame(tickAnimations);
        }
    }

    function tickAnimations() {
        drawGraph(); // Redraw base graph

        const ctx = graph.ctx;
        graph.animations.forEach((anim) => {
            anim.progress += anim.speed;
            const t = Math.min(anim.progress, 1);
            const x = anim.fromX + (anim.toX - anim.fromX) * t;
            const y = anim.fromY + (anim.toY - anim.fromY) * t;

            ctx.beginPath();
            ctx.arc(x, y, 4, 0, 2 * Math.PI);
            ctx.fillStyle = anim.color;
            ctx.globalAlpha = 1 - t * 0.4;
            ctx.fill();
            ctx.globalAlpha = 1;
        });

        // Remove completed
        graph.animations = graph.animations.filter((a) => a.progress < 1);

        if (graph.animations.length > 0) {
            graph.animFrameId = requestAnimationFrame(tickAnimations);
        } else {
            graph.animFrameId = null;
        }
    }

    // ================================================================
    // NODE DETAIL PANEL
    // ================================================================
    async function showNodeDetail(nodeId) {
        state.selectedNode = nodeId;
        DOM.detailPanel.classList.remove("hidden");
        drawGraph(); // Redraw to show selection

        let data;
        try {
            const resp = await fetch(`${API}/nodes/${nodeId}/data`);
            data = await resp.json();
        } catch {
            DOM.detailContent.innerHTML = `<p>Error loading node data.</p>`;
            return;
        }

        const ci = state.chainInfo;
        const canSendTx = ["validator", "miner", "full", "leader"].includes(data.role);
        const canRemove = !(data.node_id === "node-0" && ci.governance !== "decentralized");

        const isOffline = data.status === "offline";

        let html = "";

        // Header
        html += `<div class="detail-header">
            <div class="detail-header-top">
                <div>
                    <div class="detail-id">${data.node_id}</div>
                    <span class="detail-role role-${data.role}">${data.role}</span>
                </div>
                <div class="power-container ${isOffline ? 'power-off' : ''}">
                    ${isOffline ? 'OFFLINE' : 'ONLINE'}
                    <label class="switch">
                      <input type="checkbox" id="power-toggle" ${!isOffline ? 'checked' : ''} onchange="window.__togglePower('${nodeId}', this.checked)">
                      <span class="slider"></span>
                    </label>
                </div>
            </div>
        </div>`;

        // Stats
        html += `<div class="detail-stats">
            <div class="detail-stat"><label>Height</label><span>${data.height}</span></div>
            <div class="detail-stat"><label>Status</label><span>${data.status}</span></div>
            <div class="detail-stat"><label>Mempool</label><span>${data.mempool_size}</span></div>
            ${ci.show_balance ? `<div class="detail-stat"><label>Balance</label><span>${data.balance ?? 0}</span></div>` : ""}
        </div>`;

        // Pending join votes (for voters)
        const myPendingVotes = state.pendingJoins.filter(j =>
            !j.votes[nodeId] && isVoterById(nodeId)
        );
        if (myPendingVotes.length > 0) {
            myPendingVotes.forEach((j) => {
                html += `<div class="vote-section">
                    <p>🗳 Join request: <strong>${j.role}</strong> node wants to join
                    (${j.votes_accept}/${j.voters_needed} votes)</p>
                    <div class="vote-buttons">
                        <button class="btn btn-sm btn-accept" onclick="window.__vote('${nodeId}','${j.request_id}',true)" ${isOffline ? 'disabled title="Node is offline"' : ''}>Accept</button>
                        <button class="btn btn-sm btn-reject" onclick="window.__vote('${nodeId}','${j.request_id}',false)" ${isOffline ? 'disabled title="Node is offline"' : ''}>Reject</button>
                    </div>
                </div>`;
            });
        }

        // Centralized: owner can add nodes
        if (ci.governance === "centralized" && nodeId === "node-0") {
            html += `<div class="detail-section">
                <h3>Add Node (Owner)</h3>
                <div style="display:flex;gap:6px">
                    ${ci.node_roles.map(r => `<button class="btn btn-sm btn-primary" onclick="window.__addNodeDirect('${r}')" ${isOffline ? 'disabled title="Node is offline"' : ''}>${capitalize(r)}</button>`).join("")}
                </div>
            </div>`;
        }

        // Log
        html += `<div class="detail-section">
            <h3>📋 Event Log</h3>
            <ul class="log-list">
                ${data.event_log.slice().reverse().map(e =>
                    `<li><span class="log-time">${formatTime(e.time)}</span> ${escHtml(e.msg)}</li>`
                ).join("") || "<li>No events yet</li>"}
            </ul>
        </div>`;

        // Blocks
        html += `<div class="detail-section">
            <h3>📦 Blocks (${data.blocks.length})</h3>
            <ul class="block-list">
                ${data.blocks.slice().reverse().slice(0, 20).map(b =>
                    `<li><span>#${b.index} · ${b.tx_count} txs</span><span class="block-hash">${b.hash.slice(0,10)}…</span></li>`
                ).join("") || "<li>No blocks</li>"}
            </ul>
        </div>`;

        // Tx Log
        if (data.tx_log.length > 0) {
            html += `<div class="detail-section">
                <h3>💬 Transaction Log</h3>
                <ul class="log-list">
                    ${data.tx_log.slice().reverse().map(t =>
                        `<li><span class="log-time">${formatTime(t.time)}</span> "${escHtml(t.text)}" <span class="block-hash">${t.tx_hash.slice(0, 8)}…</span></li>`
                    ).join("")}
                </ul>
            </div>`;
        }

        // Transaction form
        if (canSendTx) {
            html += `<div class="detail-section">
                <h3>Add Transaction</h3>
                <div class="tx-form">
                    <input type="text" id="tx-input" placeholder="${isOffline ? 'Node is offline...' : 'Enter a statement…'}" maxlength="200" ${isOffline ? 'disabled' : ''}>
                    <button class="btn btn-sm btn-primary" id="btn-send-tx" ${isOffline ? 'disabled' : ''}>Send</button>
                </div>
            </div>`;
        }

        // Remove
        if (canRemove) {
            html += `<div class="remove-section">
                <button class="btn btn-sm btn-danger" onclick="window.__removeNode('${nodeId}')">Remove Node</button>
            </div>`;
        }

        DOM.detailContent.innerHTML = html;

        // Bind tx form
        const txInput = $("tx-input");
        const btnSend = $("btn-send-tx");
        if (txInput && btnSend) {
            btnSend.addEventListener("click", () => {
                const text = txInput.value.trim();
                if (text) {
                    submitTransaction(nodeId, text);
                    txInput.value = "";
                }
            });
            txInput.addEventListener("keydown", (e) => {
                if (e.key === "Enter") btnSend.click();
            });
        }
    }

    function isVoterById(nodeId) {
        const node = state.nodes.find(n => n.node_id === nodeId);
        return node ? isVoter(node) : false;
    }

    function closeDetailPanel() {
        state.selectedNode = null;
        DOM.detailPanel.classList.add("hidden");
        drawGraph();
    }

    // Global handlers for inline onclick
    window.__removeNode = removeNode;
    window.__vote = voteOnJoin;
    window.__addNodeDirect = (role) => addNode(role);

    window.__togglePower = async (nodeId, online) => {
        try {
            await fetch(`${API}/nodes/${nodeId}/toggle`, {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ online })
            });
            await refreshNodes();
        } catch (e) {
            console.error("Toggle failed", e);
        }
    };

    // ================================================================
    // INFO MODAL
    // ================================================================
    function showInfoModal() {
        const ci = state.chainInfo;
        if (!ci) return;

        let html = "";
        const row = (label, value, desc) =>
            `<div class="info-row">
                <div class="info-label">${label}</div>
                <div class="info-value">${value}${desc ? `<div class="info-desc">${desc}</div>` : ""}</div>
            </div>`;

        html += row("Network", capitalize(ci.network_type), ci.network_description);
        html += row("Governance", capitalize(ci.governance), ci.governance_description);
        html += row("Consensus", ci.consensus.toUpperCase(), ci.consensus_description);
        html += row("Sync Mode", capitalize(ci.sync_mode), ci.sync_description);
        html += row("Node Roles", ci.node_roles.map(capitalize).join(", "));
        html += row("Join Mechanism", capitalize(ci.join_mechanism), ci.join_description);
        html += row("Max Nodes", ci.max_nodes);
        html += row("Signatures", ci.require_signature ? "Required" : "Not required");
        html += row("Gas/Fees", ci.has_gas ? "Enabled" : "Disabled");

        if (ci.smart_contracts && ci.smart_contracts.length > 0) {
            html += `<div class="info-contracts">
                <h4>System Smart Contracts (${ci.smart_contracts.length})</h4>
                <ul>${ci.smart_contracts.map(sc =>
                    `<li>${sc.name} <span style="color:#999">(${sc.type}${sc.isSystem ? ", system" : ""})</span></li>`
                ).join("")}</ul>
            </div>`;
        }

        DOM.infoBody.innerHTML = html;
        DOM.infoOverlay.classList.remove("hidden");
    }

    function hideInfoModal() {
        DOM.infoOverlay.classList.add("hidden");
    }

    // ================================================================
    // DROPDOWN
    // ================================================================
    function toggleAddNodeMenu() {
        DOM.addNodeMenu.classList.toggle("hidden");
    }

    // ================================================================
    // FOOTER
    // ================================================================
    function updateFooter() {
        DOM.statNodes.textContent = `Nodes: ${state.nodes.length}`;
        const totalBlocks = state.nodes.reduce((s, n) => Math.max(s, n.height), 0);
        DOM.statBlocks.textContent = `Blocks: ${totalBlocks}`;

        if (state.chainInfo) {
            DOM.statusLine.textContent =
                `${state.chainInfo.consensus.toUpperCase()} | ` +
                `${capitalize(state.chainInfo.governance)} | ` +
                `${state.nodes.length} node${state.nodes.length !== 1 ? "s" : ""} running`;
        }
    }

    // ================================================================
    // HELPERS
    // ================================================================
    function capitalize(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : ""; }

    function formatTime(ts) {
        if (!ts) return "";
        const d = new Date(ts);
        return d.toLocaleTimeString("en-GB", { hour12: false });
    }

    function escHtml(s) {
        const div = document.createElement("div");
        div.textContent = s;
        return div.innerHTML;
    }
})();
