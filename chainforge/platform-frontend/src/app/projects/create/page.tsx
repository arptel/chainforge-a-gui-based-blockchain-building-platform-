"use client";

import { useWizardStore } from "@/store/wizard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import api from "@/lib/api";
import {
    CheckCircle2, ChevronRight, ChevronLeft, Globe, Lock, Shield, Users,
    Cpu, Server, Activity, Zap, Coins, BadgeCheck, Crown, RefreshCw,
    Scale, Network, FileText, FileEdit, Database, Layers, Timer,
    Download, Cloud, Boxes, Key, Fingerprint, FileKey, Share2, Camera, Settings, FileCode
} from "lucide-react";
import { SelectionCard } from "@/components/ui/selection-card";
import { SmartContractList } from "@/components/smart-contracts/SmartContractList";

export default function CreateProjectPage() {
    const { step, config, setConfig, nextStep, prevStep, reset, resetConfigForType } = useWizardStore();
    const { token } = useAuthStore();
    const router = useRouter();
    const [projectName, setProjectName] = useState("");
    const [loading, setLoading] = useState(false);

    const handleCreate = async () => {
        setLoading(true);
        console.log("Submitting Config:", config);
        try {
            await api.post("/projects/", {
                name: projectName || "My Blockchain",
                config: config
            });
            router.push("/dashboard");
            reset();
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const handleBack = () => {
        if (step === 1) {
            router.push("/dashboard");
        } else {
            prevStep();
        }
    };

    // Helper to determine total steps based on path
    const getTotalSteps = () => {
        // Updated to 9 steps to include Gas & Fees
        return 9;
    };

    const renderStep = () => {
        console.log("Current Config:", config);

        // STEP 1: Network Type
        if (step === 1) {
            return (
                <div className="space-y-6">
                    <div className="space-y-2">
                        <Label>Project Name</Label>
                        <Input placeholder="E.g. Supply Chain Net" value={projectName} onChange={e => setProjectName(e.target.value)} />
                    </div>

                    <div className="space-y-2">
                        <Label>Select Network Type</Label>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <SelectionCard
                                title="Public"
                                description="Permissionless, Open Network. Anyone can join."
                                icon={<Globe className="w-8 h-8 text-blue-500" />}
                                selected={config.networkType === 'public'}
                                onClick={() => resetConfigForType('public')}
                            />
                            <SelectionCard
                                title="Permissioned"
                                description="Private or Consortium. Controlled access."
                                icon={<Lock className="w-8 h-8 text-amber-500" />}
                                selected={config.networkType === 'permissioned'}
                                onClick={() => resetConfigForType('permissioned')}
                            />
                        </div>
                    </div>

                    <div className="space-y-3 pt-4 border-t">
                        <Label className="text-base">Security Configuration</Label>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <SelectionCard
                                title="Require Digital Signatures"
                                description="Verify ECDSA signatures on all transactions. Essential for value transfers."
                                icon={<Shield className="w-8 h-8 text-green-500" />}
                                selected={config.requireSignature !== false}
                                onClick={() => setConfig({ requireSignature: true })}
                            />
                            <SelectionCard
                                title="Implicit Trust (No Signatures)"
                                description="Accept all transactions. Suitable if an API Gateway handles authentication."
                                icon={<FileKey className="w-8 h-8 text-gray-500" />}
                                selected={config.requireSignature === false}
                                onClick={() => setConfig({ requireSignature: false })}
                            />
                        </div>
                    </div>
                </div>
            );
        }

        // ==========================================================================================
        // PATH: PUBLIC
        // ==========================================================================================
        if (config.networkType === 'public') {
            switch (step) {
                case 2: // Consensus
                    return (
                        <div className="space-y-6">
                            <h3 className="text-lg font-medium text-primary">Consensus Mechanism</h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <SelectionCard title="Proof of Work" description="High Security, Mining based" icon={<Cpu className="w-8 h-8 text-orange-500" />} selected={config.publicConsensus === 'pow'} onClick={() => setConfig({ publicConsensus: 'pow' })} />
                                <SelectionCard title="Proof of Authority" description="Validator based, Efficient" icon={<BadgeCheck className="w-8 h-8 text-purple-500" />} selected={config.publicConsensus === 'poa'} onClick={() => setConfig({ publicConsensus: 'poa' })} />
                                <SelectionCard title="Proof of Stake" description="Asset based (Future)" icon={<Coins className="w-8 h-8 text-green-500" />} selected={config.publicConsensus === 'pos'} onClick={() => setConfig({ publicConsensus: 'pos' })} />
                            </div>
                        </div>
                    );
                case 3: // Node Roles
                    return (
                        <div className="space-y-6">
                            <h3 className="text-lg font-medium text-primary">Participating Node Roles</h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {['miner', 'full', 'light'].map((role: any) => (
                                    <div key={role}
                                        className={`cursor-pointer border-2 rounded-xl p-4 transition-all hover:bg-accent flex flex-col items-center text-center space-y-3 ${config.publicNodeRoles?.includes(role) ? 'border-primary bg-accent/50' : 'border-muted bg-card'}`}
                                        onClick={() => {
                                            const roles = config.publicNodeRoles || [];
                                            const newRoles = roles.includes(role) ? roles.filter(r => r !== role) : [...roles, role];
                                            setConfig({ publicNodeRoles: newRoles as any });
                                        }}
                                    >
                                        <div className={`p-3 rounded-full ${config.publicNodeRoles?.includes(role) ? 'bg-background text-primary' : 'bg-secondary'}`}>
                                            <Server className="w-6 h-6" />
                                        </div>
                                        <div>
                                            <span className="capitalize font-semibold block">{role} Node</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    );
                case 4: // Runtime
                    return (
                        <div className="space-y-6">
                            <h3 className="text-lg font-medium text-primary">Smart Contract Runtime</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <SelectionCard title="WASM Runtime" description="WebAssembly for high performance contracts" icon={<Boxes className="w-8 h-8 text-indigo-500" />} selected={config.publicRuntime === 'wasm'} onClick={() => setConfig({ publicRuntime: 'wasm' })} />
                                <SelectionCard title="EVM Compatible" description="Ethereum Virtual Machine compatibility" icon={<Layers className="w-8 h-8 text-slate-500" />} selected={config.publicRuntime === 'evm'} onClick={() => setConfig({ publicRuntime: 'evm' })} />
                            </div>
                        </div>
                    );
                case 5: // Sync
                    return (
                        <div className="space-y-6">
                            <h3 className="text-lg font-medium text-primary">Synchronization Mode</h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <SelectionCard title="Full Sync" description="Download entire history" icon={<Database className="w-8 h-8 text-blue-500" />} selected={config.publicSyncMode === 'full'} onClick={() => setConfig({ publicSyncMode: 'full' })} />
                                <SelectionCard title="Fast Sync" description="Download recent state only" icon={<Zap className="w-8 h-8 text-yellow-500" />} selected={config.publicSyncMode === 'fast'} onClick={() => setConfig({ publicSyncMode: 'fast' })} />
                                <SelectionCard title="Light Sync" description="Header-only verification" icon={<Activity className="w-8 h-8 text-green-500" />} selected={config.publicSyncMode === 'light'} onClick={() => setConfig({ publicSyncMode: 'light' })} />
                            </div>
                        </div>
                    );
                case 6: // Token
                    return (
                        <div className="space-y-6">
                            <h3 className="text-lg font-medium text-primary">Network Economy</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <SelectionCard title="Native Token" description="Built-in currency for fees & rewards" icon={<Coins className="w-8 h-8 text-amber-500" />} selected={config.publicToken === 'native'} onClick={() => setConfig({ publicToken: 'native' })} />
                                <SelectionCard title="No Token" description="Free-for-all (Not recommended for public)" icon={<Lock className="w-8 h-8 text-gray-500" />} selected={config.publicToken === 'none'} onClick={() => setConfig({ publicToken: 'none' })} />
                            </div>
                        </div>
                    );
                case 7: // Gas & Fees
                    return renderGasFees();
                case 8: // Smart Contracts
                    return (
                        <div className="space-y-6">
                            <h3 className="text-lg font-medium text-primary">Smart Contracts</h3>
                            <p className="text-sm text-muted-foreground">Define smart contracts to be deployed on genesis or available in the project.</p>
                            <SmartContractList
                                contracts={config.smartContracts || []}
                                onChange={(contracts) => setConfig({ smartContracts: contracts })}
                                projectConfig={config}
                            />
                        </div>
                    );
                case 9:
                    return renderReview();
            }
        }

        // ==========================================================================================
        // PATH: PERMISSIONED -> CENTRALIZED
        // ==========================================================================================
        if (config.networkType === 'permissioned') { // This covers both centralized and consortium
            switch (step) {
                case 2: // Subtype (Already selected Permissioned, now switch to Centralized view if needed, but wait, step 2 is usually drill down for perm type)
                    // Actually Step 2 for Permissioned needs to be the "Centralized vs Consortium" choice first.
                    return (
                        <div className="space-y-6">
                            <h3 className="text-lg font-medium text-primary">Permissioned Governance Model</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <SelectionCard title="Centralized" description="Single Authority" icon={<Shield className="w-8 h-8 text-red-500" />} selected={config.permissionedType === 'centralized'} onClick={() => setConfig({ permissionedType: 'centralized' })} />
                                <SelectionCard title="Consortium" description="Multi-Organization" icon={<Users className="w-8 h-8 text-purple-500" />} selected={config.permissionedType === 'consortium'} onClick={() => setConfig({ permissionedType: 'consortium' })} />
                            </div>
                        </div>
                    );
                case 3: // Authority (Centralized) or Validator Struct (Consortium)
                    if (config.permissionedType === 'centralized') {
                        return (
                            <div className="space-y-6">
                                <h3 className="text-lg font-medium text-primary">Central Authority Structure</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <SelectionCard title="Fixed Leader" description="Static Leader Node" icon={<Crown className="w-8 h-8 text-yellow-500" />} selected={config.centralizedAuthority === 'fixed'} onClick={() => setConfig({ centralizedAuthority: 'fixed' })} />
                                    <SelectionCard title="Rotating Leader" description="Dynamic Leader Node" icon={<RefreshCw className="w-8 h-8 text-blue-500" />} selected={config.centralizedAuthority === 'rotating'} onClick={() => setConfig({ centralizedAuthority: 'rotating' })} />
                                </div>
                            </div>
                        );
                    } else if (config.permissionedType === 'consortium') {
                        return (
                            <div className="space-y-6">
                                <h3 className="text-lg font-medium text-primary">Validator Structure</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <SelectionCard title="Equal Validators" description="All nodes have equal weight" icon={<Scale className="w-8 h-8 text-indigo-500" />} selected={config.consortiumValidatorStruct === 'equal'} onClick={() => setConfig({ consortiumValidatorStruct: 'equal' })} />
                                    <SelectionCard title="Weighted Validators" description="Voting power by stake/reputation" icon={<Crown className="w-8 h-8 text-rose-500" />} selected={config.consortiumValidatorStruct === 'weighted'} onClick={() => setConfig({ consortiumValidatorStruct: 'weighted' })} />
                                </div>
                            </div>
                        );
                    }
                    break;
                case 4: // Consensus (Centralized) or BFT Consensus (Consortium)
                    if (config.permissionedType === 'centralized') {
                        return (
                            <div className="space-y-6">
                                <h3 className="text-lg font-medium text-primary">Consensus Algorithm</h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <SelectionCard title="Raft" description="Crash Fault Tolerance (CFT)" icon={<Database className="w-8 h-8 text-emerald-500" />} selected={config.centralizedConsensus === 'raft'} onClick={() => setConfig({ centralizedConsensus: 'raft' })} />
                                    <SelectionCard title="Paxos" description="Proven CFT Protocol" icon={<FileText className="w-8 h-8 text-slate-500" />} selected={config.centralizedConsensus === 'paxos'} onClick={() => setConfig({ centralizedConsensus: 'paxos' })} />
                                    <SelectionCard title="None" description="Single-Writer Mode" icon={<FileEdit className="w-8 h-8 text-gray-500" />} selected={config.centralizedConsensus === 'none'} onClick={() => setConfig({ centralizedConsensus: 'none' })} />
                                </div>
                            </div>
                        );
                    } else if (config.permissionedType === 'consortium') {
                        return (
                            <div className="space-y-6">
                                <h3 className="text-lg font-medium text-primary">BFT Consensus</h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <SelectionCard title="PBFT" description="Practical Byzantine Fault Tolerance" icon={<Network className="w-8 h-8 text-cyan-500" />} selected={config.consortiumConsensus === 'pbft'} onClick={() => setConfig({ consortiumConsensus: 'pbft' })} />
                                    <SelectionCard title="HotStuff" description="Chained BFT (Libra/Diem)" icon={<Zap className="w-8 h-8 text-yellow-500" />} selected={config.consortiumConsensus === 'hotstuff'} onClick={() => setConfig({ consortiumConsensus: 'hotstuff' })} />
                                    <SelectionCard title="Tendermint" description="Fast Finality (Cosmos)" icon={<Activity className="w-8 h-8 text-fuchsia-500" />} selected={config.consortiumConsensus === 'tendermint'} onClick={() => setConfig({ consortiumConsensus: 'tendermint' })} />
                                </div>
                            </div>
                        );
                    }
                    break;
                case 5: // Access Control (Centralized) or Member Identity (Consortium)
                    if (config.permissionedType === 'centralized') {
                        return (
                            <div className="space-y-6">
                                <h3 className="text-lg font-medium text-primary">Access Control</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <SelectionCard title="Role-Based (RBAC)" description="Permissions per role" icon={<Key className="w-8 h-8 text-orange-500" />} selected={config.centralizedAccess === 'rbac'} onClick={() => setConfig({ centralizedAccess: 'rbac' })} />
                                    <SelectionCard title="Certificate Whitelist" description="PKI Identity Management" icon={<FileKey className="w-8 h-8 text-teal-500" />} selected={config.centralizedAccess === 'whitelist'} onClick={() => setConfig({ centralizedAccess: 'whitelist' })} />
                                </div>
                            </div>
                        );
                    } else if (config.permissionedType === 'consortium') {
                        return (
                            <div className="space-y-6">
                                <h3 className="text-lg font-medium text-primary">Member Identity</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <SelectionCard title="Certificate Authority" description="Centralized CA issues certs" icon={<BadgeCheck className="w-8 h-8 text-blue-600" />} selected={config.consortiumIdentity === 'ca'} onClick={() => setConfig({ consortiumIdentity: 'ca' })} />
                                    <SelectionCard title="Multi-Sig Approval" description="Existing members vote in new ones" icon={<Share2 className="w-8 h-8 text-violet-500" />} selected={config.consortiumIdentity === 'multisig'} onClick={() => setConfig({ consortiumIdentity: 'multisig' })} />
                                </div>
                            </div>
                        );
                    }
                    break;
                case 6: // Sync (Centralized) or Synchronization (Consortium)
                    if (config.permissionedType === 'centralized') {
                        return (
                            <div className="space-y-6">
                                <h3 className="text-lg font-medium text-primary">Replication Mode</h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <SelectionCard title="Real-Time" description="Immediate Replication" icon={<Timer className="w-8 h-8 text-purple-500" />} selected={config.centralizedSync === 'realtime'} onClick={() => setConfig({ centralizedSync: 'realtime' })} />
                                    <SelectionCard title="Snapshot" description="Periodic States" icon={<Camera className="w-8 h-8 text-pink-500" />} selected={config.centralizedSync === 'snapshot'} onClick={() => setConfig({ centralizedSync: 'snapshot' })} />
                                    <SelectionCard title="Batch" description="High Throughput" icon={<Layers className="w-8 h-8 text-blue-500" />} selected={config.centralizedSync === 'batch'} onClick={() => setConfig({ centralizedSync: 'batch' })} />
                                </div>
                            </div>
                        );
                    } else if (config.permissionedType === 'consortium') {
                        return (
                            <div className="space-y-6">
                                <h3 className="text-lg font-medium text-primary">Synchronization</h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <SelectionCard title="Full State" description="Full validation of all blocks" icon={<Database className="w-8 h-8 text-emerald-600" />} selected={config.consortiumSync === 'full'} onClick={() => setConfig({ consortiumSync: 'full' })} />
                                    <SelectionCard title="Snapshot" description="State snapshots + catchup" icon={<Timer className="w-8 h-8 text-orange-500" />} selected={config.consortiumSync === 'snapshot'} onClick={() => setConfig({ consortiumSync: 'snapshot' })} />
                                    <SelectionCard title="Light" description="SPV / Light Client support" icon={<Activity className="w-8 h-8 text-lime-500" />} selected={config.consortiumSync === 'light'} onClick={() => setConfig({ consortiumSync: 'light' })} />
                                </div>
                            </div>
                        );
                    }
                    break;
                case 7: // Gas & Fees
                    return renderGasFees();
                case 8: // Smart Contracts
                    return (
                        <div className="space-y-6">
                            <h3 className="text-lg font-medium text-primary">Smart Contracts</h3>
                            <p className="text-sm text-muted-foreground">Define smart contracts to be deployed on genesis or available in the project.</p>
                            <SmartContractList
                                contracts={config.smartContracts || []}
                                onChange={(contracts) => setConfig({ smartContracts: contracts })}
                                projectConfig={config}
                            />
                        </div>
                    );
                case 9:
                    return renderReview();
            }
        }

    };

    const renderGasFees = () => {
        return (
            <div className="space-y-6">
                <h3 className="text-lg font-medium text-primary">Transaction Fees & Gas</h3>
                <p className="text-sm text-muted-foreground">Configure the economic cost and resource limits for executing transactions and smart contracts on your network.</p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <SelectionCard
                        title="Enable Gas Fees"
                        description="Transactions cost tokens. Prevents spam and infinite loops."
                        icon={<Coins className="w-8 h-8 text-amber-500" />}
                        selected={config.enableGas === true}
                        onClick={() => setConfig({ enableGas: true, minGasPrice: config.minGasPrice || 1, defaultGasLimit: config.defaultGasLimit || 100000 })}
                    />
                    <SelectionCard
                        title="Gasless (Free)"
                        description="No fees. Execution is free but still bounded by strict limits."
                        icon={<Zap className="w-8 h-8 text-green-500" />}
                        selected={config.enableGas === false}
                        onClick={() => setConfig({ enableGas: false, minGasPrice: 0, defaultGasLimit: config.defaultGasLimit || 100000 })}
                    />
                </div>

                {config.enableGas !== undefined && (
                    <div className="space-y-4 p-4 border rounded-xl bg-card">
                        <div className="space-y-2">
                            <Label>Minimum Gas Price</Label>
                            <Input
                                type="number"
                                value={config.minGasPrice || 0}
                                onChange={(e) => setConfig({ minGasPrice: parseInt(e.target.value) || 0 })}
                                disabled={!config.enableGas}
                                className="font-mono"
                            />
                            <p className="text-xs text-muted-foreground">The minimum fee a user must pay per unit of gas to have their transaction processed by miners/validators.</p>
                        </div>
                        <div className="space-y-2 mt-4">
                            <Label>Default Contract Gas Limit</Label>
                            <Input
                                type="number"
                                value={config.defaultGasLimit || 100000}
                                onChange={(e) => setConfig({ defaultGasLimit: parseInt(e.target.value) || 100000 })}
                                className="font-mono"
                            />
                            <p className="text-xs text-muted-foreground">The absolute maximum number of operations a smart contract can execute before triggering an OutOfGas halt (Halting Problem protection).</p>
                        </div>
                    </div>
                )}
            </div>
        );
    };

    const renderReview = () => (
        <div className="space-y-4">
            <div className="p-4 border rounded-xl bg-secondary/10 mt-6">
                <h4 className="font-semibold mb-3 flex items-center text-lg"><CheckCircle2 className="w-5 h-5 mr-2 text-primary" /> Review Configuration</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="p-3 bg-background rounded-lg border">
                        <span className="text-muted-foreground block text-xs uppercase tracking-wider">Type</span>
                        <span className="font-medium capitalize">{config.networkType}</span>
                    </div>
                    <div className="p-3 bg-background rounded-lg border">
                        <span className="text-muted-foreground block text-xs uppercase tracking-wider">Security</span>
                        <span className="font-medium">{config.requireSignature !== false ? 'Signatures Required' : 'Implicit Trust'}</span>
                    </div>
                    {config.networkType === 'public' && (
                        <>
                            <div className="p-3 bg-background rounded-lg border">
                                <span className="text-muted-foreground block text-xs uppercase tracking-wider">Consensus</span>
                                <span className="font-medium uppercase">{config.publicConsensus}</span>
                            </div>
                            <div className="p-3 bg-background rounded-lg border">
                                <span className="text-muted-foreground block text-xs uppercase tracking-wider">Runtime</span>
                                <span className="font-medium uppercase">{config.publicRuntime}</span>
                            </div>
                            <div className="p-3 bg-background rounded-lg border">
                                <span className="text-muted-foreground block text-xs uppercase tracking-wider">Sync Mode</span>
                                <span className="font-medium capitalize">{config.publicSyncMode}</span>
                            </div>
                            <div className="p-3 bg-background rounded-lg border">
                                <span className="text-muted-foreground block text-xs uppercase tracking-wider">Token</span>
                                <span className="font-medium capitalize">{config.publicToken}</span>
                            </div>
                        </>
                    )}
                    {config.networkType === 'permissioned' && (
                        <>
                            <div className="p-3 bg-background rounded-lg border">
                                <span className="text-muted-foreground block text-xs uppercase tracking-wider">Model</span>
                                <span className="font-medium capitalize">{config.permissionedType}</span>
                            </div>
                            {config.permissionedType === 'centralized' ? (
                                <>
                                    <div className="p-3 bg-background rounded-lg border">
                                        <span className="text-muted-foreground block text-xs uppercase tracking-wider">Authority</span>
                                        <span className="font-medium capitalize">{config.centralizedAuthority}</span>
                                    </div>
                                    <div className="p-3 bg-background rounded-lg border">
                                        <span className="text-muted-foreground block text-xs uppercase tracking-wider">Consensus</span>
                                        <span className="font-medium uppercase">{config.centralizedConsensus}</span>
                                    </div>
                                    <div className="p-3 bg-background rounded-lg border">
                                        <span className="text-muted-foreground block text-xs uppercase tracking-wider">Access Control</span>
                                        <span className="font-medium capitalize">{config.centralizedAccess}</span>
                                    </div>
                                    <div className="p-3 bg-background rounded-lg border">
                                        <span className="text-muted-foreground block text-xs uppercase tracking-wider">Sync Mode</span>
                                        <span className="font-medium capitalize">{config.centralizedSync}</span>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <div className="p-3 bg-background rounded-lg border">
                                        <span className="text-muted-foreground block text-xs uppercase tracking-wider">Validators</span>
                                        <span className="font-medium capitalize">{config.consortiumValidatorStruct}</span>
                                    </div>
                                    <div className="p-3 bg-background rounded-lg border">
                                        <span className="text-muted-foreground block text-xs uppercase tracking-wider">Consensus</span>
                                        <span className="font-medium uppercase">{config.consortiumConsensus}</span>
                                    </div>
                                    <div className="p-3 bg-background rounded-lg border">
                                        <span className="text-muted-foreground block text-xs uppercase tracking-wider">Identity</span>
                                        <span className="font-medium capitalize">{config.consortiumIdentity}</span>
                                    </div>
                                    <div className="p-3 bg-background rounded-lg border">
                                        <span className="text-muted-foreground block text-xs uppercase tracking-wider">Sync Mode</span>
                                        <span className="font-medium capitalize">{config.consortiumSync}</span>
                                    </div>
                                </>
                            )}
                        </>
                    )}

                    <div className="p-3 bg-background rounded-lg border col-span-2">
                        <span className="text-muted-foreground block text-xs uppercase tracking-wider mb-2">Gas & Economy</span>
                        <div className="grid grid-cols-3 gap-2">
                            <div>
                                <span className="text-xs text-muted-foreground block">Enabled</span>
                                <span className="font-medium">{config.enableGas ? 'Yes' : 'No (Free)'}</span>
                            </div>
                            <div>
                                <span className="text-xs text-muted-foreground block">Min Price</span>
                                <span className="font-medium">{config.minGasPrice || 0}</span>
                            </div>
                            <div>
                                <span className="text-xs text-muted-foreground block">Default Limit</span>
                                <span className="font-medium">{config.defaultGasLimit || 100000}</span>
                            </div>
                        </div>
                    </div>

                    <div className="p-3 bg-background rounded-lg border col-span-2">
                        <span className="text-muted-foreground block text-xs uppercase tracking-wider mb-2">Smart Contracts Configured</span>
                        {config.smartContracts && config.smartContracts.length > 0 ? (
                            <div className="flex flex-col gap-2 mt-2">
                                {config.smartContracts.map(c => (
                                    <div key={c.id} className="flex justify-between items-center bg-secondary/30 p-2 rounded text-sm">
                                        <span className="font-medium">{c.name}</span>
                                        <span className="text-xs uppercase text-muted-foreground">{c.type}</span>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <span className="text-sm text-muted-foreground">No smart contracts configured.</span>
                        )}
                    </div>

                    <div className="p-3 bg-background rounded-lg border">
                        <span className="text-muted-foreground block text-xs uppercase tracking-wider">Project</span>
                        <span className="font-medium">{projectName || "My Blockchain"}</span>
                    </div>
                </div>
            </div>

            {config.smartContracts && config.smartContracts.length > 0 && (
                <div className="p-4 border rounded-xl bg-secondary/10 mt-6">
                    <h4 className="font-semibold mb-3 flex items-center text-lg"><FileCode className="w-5 h-5 mr-2 text-primary" /> Smart Contracts</h4>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b">
                                    <th className="text-left font-medium text-muted-foreground pb-2">Name</th>
                                    <th className="text-left font-medium text-muted-foreground pb-2">Type</th>
                                    <th className="text-left font-medium text-muted-foreground pb-2">API Key</th>
                                </tr>
                            </thead>
                            <tbody>
                                {config.smartContracts.map((c: any) => (
                                    <tr key={c.id} className="border-b last:border-0">
                                        <td className="py-2 font-medium">{c.name}</td>
                                        <td className="py-2 uppercase text-xs">{c.type}</td>
                                        <td className="py-2"><code className="bg-muted px-1 rounded text-xs">{c.apiKey}</code></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );

    // Helper to check if current step is valid (selection made)
    const isStepValid = () => {
        if (step === 1) return !!config.networkType;

        if (config.networkType === 'public') {
            switch (step) {
                case 2: return !!config.publicConsensus;
                case 3: return !!config.publicNodeRoles && config.publicNodeRoles.length > 0;
                case 4: return !!config.publicRuntime;
                case 5: return !!config.publicSyncMode;
                case 6: return !!config.publicToken;
                case 7: return config.enableGas !== undefined; // Gas Fees must be selected
                case 8: return true; // Smart Contracts are optional
                default: return true;
            }
        }

        if (config.networkType === 'permissioned') {
            switch (step) {
                case 2: return !!config.permissionedType;
                case 3: // Authority or Validators
                    if (config.permissionedType === 'centralized') return !!config.centralizedAuthority;
                    return !!config.consortiumValidatorStruct;
                case 4: // Consensus
                    if (config.permissionedType === 'centralized') return !!config.centralizedConsensus;
                    return !!config.consortiumConsensus;
                case 5: // Access/Identity
                    if (config.permissionedType === 'centralized') return !!config.centralizedAccess;
                    return !!config.consortiumIdentity;
                case 6: // Sync
                    if (config.permissionedType === 'centralized') return !!config.centralizedSync;
                    return !!config.consortiumSync;
                case 7: return config.enableGas !== undefined; // Gas Fees must be selected
                case 8: return true; // Smart Contracts are optional
                default: return true;
            }
        }
        return false;
    };

    // Helper to check if step is optional
    const isStepOptional = () => {
        return false;
    };

    const handleNext = () => {
        if (!isStepValid()) return;
        nextStep();
    }

    const getNextButtonState = () => {
        const valid = isStepValid();
        const optional = isStepOptional();

        if (optional) {
            return {
                disabled: false,
                text: valid ? "Next" : "Skip",
                icon: valid ? <ChevronRight className="ml-2 h-4 w-4" /> : <ChevronRight className="ml-2 h-4 w-4" opacity={0.5} />
            };
        } else {
            return {
                disabled: !valid,
                text: "Next",
                icon: <ChevronRight className="ml-2 h-4 w-4" />
            };
        }
    };

    const nextBtn = getNextButtonState();

    return (
        <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center py-10 px-4">
            <Card className="w-full max-w-4xl shadow-lg border-2">
                <CardHeader>
                    <CardTitle>Create New Blockchain</CardTitle>
                    <CardDescription>Step {step} of {getTotalSteps()}: Configuration</CardDescription>
                </CardHeader>
                <CardContent className="min-h-[400px]">
                    {renderStep()}
                </CardContent>
                <CardFooter className="flex justify-between gap-4 pt-6">
                    <Button variant="outline" onClick={handleBack} className="w-32">
                        <ChevronLeft className="mr-2 h-4 w-4" />
                        {step === 1 ? 'Cancel' : 'Back'}
                    </Button>

                    {step < getTotalSteps() ? (
                        <Button onClick={handleNext} disabled={nextBtn.disabled} className={`w-32 ${nextBtn.text === 'Skip' ? 'bg-secondary text-secondary-foreground hover:bg-secondary/80' : ''}`}>
                            {nextBtn.text} {nextBtn.icon}
                        </Button>
                    ) : (
                        <Button onClick={handleCreate} disabled={loading} className="min-w-40 bg-green-600 hover:bg-green-700">
                            {loading ? "Generating..." : "Create & Generate"} <CheckCircle2 className="ml-2 h-4 w-4" />
                        </Button>
                    )}
                </CardFooter>
            </Card>
        </div>
    )
}
