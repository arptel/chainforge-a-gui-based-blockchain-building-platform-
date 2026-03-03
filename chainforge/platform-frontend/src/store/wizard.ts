import { create } from 'zustand';

interface ChainConfig {
    networkType: "public" | "permissioned";
    // Public specific
    publicGovernance?: "open";
    publicConsensus?: "pow" | "poa" | "pos";
    publicNodeRoles?: ("miner" | "full" | "light")[];
    publicSyncMode?: "full" | "fast" | "light";
    publicRuntime?: "wasm" | "evm";
    publicToken?: "native" | "none";
    publicDeployment?: "docker" | "zip";
    publicMonitoring?: ("metrics" | "tls" | "ddos")[];

    // Permissioned specific
    permissionedType?: "centralized" | "consortium";

    // Permissioned -> Centralized
    centralizedAuthority?: "fixed" | "rotating";
    centralizedConsensus?: "raft" | "paxos" | "none";
    centralizedNodeRoles?: ("leader" | "reader" | "backup")[];
    centralizedSync?: "realtime" | "snapshot" | "batch";
    centralizedAccess?: "rbac" | "whitelist";
    centralizedContract?: "validation" | "workflow";
    centralizedDeployment?: "docker" | "zip";
    centralizedMonitoring?: ("logs" | "audit" | "keyrotation")[];
    centralizedBackup?: "snapshots" | "dr";

    // Permissioned -> Consortium
    consortiumValidatorStruct?: "equal" | "weighted";
    consortiumConsensus?: "pbft" | "hotstuff" | "tendermint";
    consortiumFaultTol?: "cft" | "bft";
    consortiumNodeRoles?: ("validator" | "observer" | "auditor")[];
    consortiumSync?: "full" | "snapshot" | "light";
    consortiumIdentity?: "ca" | "multisig";
    consortiumContract?: "policy" | "multiparty";
    consortiumDeployment?: "docker" | "zip";
    consortiumMonitoring?: ("distlogs" | "intrusion" | "slashing")[];
    consortiumBackup?: "distsnapshots" | "crossregion";

    // Common/Legacy (keeping for compatibility if needed, but likely replaced by above)
    nodeCount: number;
    requireSignature?: boolean; // Toggle for digital signatures

    // Gas & Fees
    enableGas?: boolean;
    minGasPrice?: number;
    defaultGasLimit?: number;

    // Sandbox Security
    allowedBuiltins?: string[];

    // Smart Contracts
    smartContracts?: {
        id: string;
        name: string;
        type: 'python' | 'solidity';
        code: string;
        apiKey: string;
        isSystem?: boolean;
    }[];
}

interface WizardState {
    step: number;
    config: ChainConfig;
    setConfig: (update: Partial<ChainConfig>) => void;
    nextStep: () => void;
    prevStep: () => void;
    reset: () => void;
    // Helper to clear irrelevant fields when switching types
    resetConfigForType: (type: "public" | "permissioned") => void;
}

const initialConfig: ChainConfig = {
    networkType: "public", // Default to public to show first screen, but subsequent selections are undefined
    nodeCount: 4,
    requireSignature: true, // Default to secure
    // No defaults for specific fields to force user selection
};

export const useWizardStore = create<WizardState>((set) => ({
    step: 1,
    config: initialConfig,
    setConfig: (update) => set((state) => ({ config: { ...state.config, ...update } })),
    nextStep: () => set((state) => ({ step: state.step + 1 })),
    prevStep: () => set((state) => ({ step: Math.max(1, state.step - 1) })),
    reset: () => set({ step: 1, config: initialConfig }),
    resetConfigForType: (type) => set((state) => {
        // Reset to initial config but with specific network type
        // This ensures previous selections are cleared when switching types at Step 1
        return {
            config: {
                networkType: type,
                nodeCount: 4,
                requireSignature: true
            }
        };
    })
}));
