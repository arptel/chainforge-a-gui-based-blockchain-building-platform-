import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CodeEditor } from './CodeEditor';
import { SMART_CONTRACT_TEMPLATES } from './templates';
import { Plus, Trash2, Code, Key, Play } from 'lucide-react';
// Checking package.json I didn't see uuid, so I'll use a simple generator
const generateId = () => Math.random().toString(36).substring(2, 9);
const generateApiKey = () => 'sk_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);

interface SmartContract {
    id: string;
    name: string;
    type: 'python' | 'solidity' | 'c++';
    code: string;
    apiKey: string;
    isSystem?: boolean;
}

interface SmartContractListProps {
    contracts: SmartContract[];
    onChange: (contracts: SmartContract[]) => void;
    projectConfig?: any;
}

export const SmartContractList: React.FC<SmartContractListProps> = ({ contracts = [], onChange, projectConfig }) => {
    const [selectedContractId, setSelectedContractId] = useState<string | null>(null);
    const [newContractName, setNewContractName] = useState("");
    const [newContractType, setNewContractType] = useState<'python' | 'solidity' | 'c++'>('python');
    const [defaultContracts, setDefaultContracts] = useState<SmartContract[]>([]);

    // Create a stable string representation of just the network configuration fields
    // This prevents infinite loops where onChange updates projectConfig.smartContracts, triggering re-fetches
    const networkConfigDeps = projectConfig ? JSON.stringify({
        networkType: projectConfig.networkType,
        publicConsensus: projectConfig.publicConsensus,
        centralizedConsensus: projectConfig.centralizedConsensus,
        consortiumConsensus: projectConfig.consortiumConsensus,
        publicSyncMode: projectConfig.publicSyncMode,
        centralizedSync: projectConfig.centralizedSync,
        consortiumSync: projectConfig.consortiumSync,
        permissionedType: projectConfig.permissionedType,
        publicToken: projectConfig.publicToken,
        publicRuntime: projectConfig.publicRuntime
    }) : "";

    const isWasm = projectConfig?.networkType === 'public' && projectConfig?.publicRuntime === 'wasm';

    useEffect(() => {
        if (isWasm && newContractType !== 'c++') {
            setNewContractType('c++');
        } else if (!isWasm && newContractType === 'c++') {
            setNewContractType('python');
        }
    }, [isWasm]);

    useEffect(() => {
        if (!projectConfig) return;
        const fetchDefaults = async () => {
            try {
                const res = await api.post("/generate/default-contracts", projectConfig);
                if (res.data && res.data.contracts) {
                    const fetchedDefaults = res.data.contracts;
                    setDefaultContracts(fetchedDefaults);

                    // Push the combined list of defaults + user contracts up to the parent form state
                    const userOnlyContracts = contracts.filter(c => !c.isSystem);

                    const currentDefaults = contracts.filter(c => c.isSystem);
                    if (JSON.stringify(fetchedDefaults) !== JSON.stringify(currentDefaults)) {
                        onChange([...fetchedDefaults, ...userOnlyContracts]);
                    }
                }
            } catch (err) {
                console.error("Failed to fetch default contracts", err);
            }
        };
        fetchDefaults();
    }, [networkConfigDeps]);

    const allContracts = [...contracts];
    const selectedContract = allContracts.find(c => c.id === selectedContractId);

    const handleAddContract = () => {
        if (!newContractName) return;

        // Simple Boilerplate
        let boilerplate = "";
        if (newContractType === 'c++') {
            boilerplate = `extern "C" {
    // Write your exported WASM functions here
    
}`;
        } else if (newContractType === 'python') {
            boilerplate = `class ${newContractName}:
    def __init__(self):
        pass`;
        } else {
            boilerplate = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ${newContractName} {
    constructor() {}
}`;
        }

        const newContract: SmartContract = {
            id: generateId(),
            name: newContractName,
            type: newContractType,
            code: boilerplate,
            apiKey: generateApiKey()
        };

        const updated = [...contracts, newContract];
        onChange(updated);
        setSelectedContractId(newContract.id);
        setNewContractName("");
    };

    const handleDelete = (id: string) => {
        const updated = contracts.filter(c => c.id !== id);
        onChange(updated);
        if (selectedContractId === id) {
            setSelectedContractId(null);
        }
    };

    const handleUpdateCode = (code: string) => {
        if (!selectedContractId) return;
        const updated = contracts.map(c => c.id === selectedContractId ? { ...c, code } : c);
        onChange(updated);
    };

    const handleApplyTemplate = (templateName: string) => {
        if (!selectedContract) return;
        const template = SMART_CONTRACT_TEMPLATES[selectedContract.type].find(t => t.name === templateName);
        if (template) {
            handleUpdateCode(template.code);
        }
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 h-[550px] min-h-[400px]">
            {/* Inject a script to aggressively kill Monaco's internal unhandled promise rejections before Next.js catches them */}
            <script dangerouslySetInnerHTML={{
                __html: `
                window.addEventListener('unhandledrejection', function(event) {
                    if (event.reason && typeof event.reason === 'object' && !event.reason.message && !event.reason.stack) {
                        event.preventDefault();
                        event.stopImmediatePropagation();
                    } else if (event.reason && (event.reason.name === 'Canceled' || event.reason.message === 'Canceled')) {
                        event.preventDefault();
                        event.stopImmediatePropagation();
                    }
                });
            ` }} />

            {/* Sidebar List */}
            <div className="md:col-span-1 border rounded-xl overflow-hidden flex flex-col bg-background h-full">
                <div className="p-4 border-b bg-muted/30">
                    <h3 className="font-semibold mb-2">My Contracts</h3>
                    <div className="space-y-2">
                        <Input
                            placeholder="Contract Name"
                            value={newContractName}
                            onChange={e => setNewContractName(e.target.value)}
                        />
                        <div className="flex gap-2">
                            <Select value={newContractType} onValueChange={(v: any) => setNewContractType(v)}>
                                <SelectTrigger className="w-[110px]">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    {isWasm ? (
                                        <SelectItem value="c++">C++</SelectItem>
                                    ) : (
                                        <>
                                            <SelectItem value="python">Python</SelectItem>
                                            <SelectItem value="solidity">Solidity</SelectItem>
                                        </>
                                    )}
                                </SelectContent>
                            </Select>
                            <Button onClick={handleAddContract} size="sm" className="flex-1" disabled={!newContractName}>
                                <Plus className="w-4 h-4 mr-1" /> Add
                            </Button>
                        </div>
                    </div>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-2">
                    {allContracts.length === 0 && (
                        <div className="text-center text-muted-foreground py-8 text-sm">
                            No contracts added yet.
                        </div>
                    )}
                    {allContracts.map(c => (
                        <div
                            key={c.id}
                            className={`p-3 rounded-lg border cursor-pointer flex justify-between items-center group transition-all ${selectedContractId === c.id ? 'border-primary bg-primary/5 shadow-sm' : 'hover:bg-accent'} ${c.isSystem ? 'border-dashed bg-muted/20' : ''}`}
                            onClick={() => setSelectedContractId(c.id)}
                        >
                            <div className="flex items-center gap-3 overflow-hidden">
                                <div className={`p-2 rounded-md ${c.type === 'python' ? 'bg-blue-100 text-blue-700' : c.type === 'c++' ? 'bg-purple-100 text-purple-700' : 'bg-slate-100 text-slate-700'}`}>
                                    <Code className="w-4 h-4" />
                                </div>
                                <div className="truncate flex flex-col items-start">
                                    <div className="font-medium truncate flex items-center gap-2">
                                        {c.name}
                                        {c.isSystem && (
                                            <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded uppercase font-semibold">System</span>
                                        )}
                                    </div>
                                    <div className="text-xs text-muted-foreground uppercase">{c.type}</div>
                                </div>
                            </div>
                            {!c.isSystem && (
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
                                    onClick={(e) => { e.stopPropagation(); handleDelete(c.id); }}
                                >
                                    <Trash2 className="w-4 h-4" />
                                </Button>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* Editor Area */}
            <div className="md:col-span-3 flex flex-col h-full overflow-hidden">
                {selectedContract ? (
                    <div className="space-y-4 flex flex-col h-full">
                        <div className="flex justify-between items-center">
                            <div>
                                <h3 className="text-lg font-bold flex items-center gap-2">
                                    {selectedContract.name}
                                    <span className="text-xs font-normal px-2 py-0.5 rounded-full bg-muted border border-muted-foreground/20">
                                        {selectedContract.type}
                                    </span>
                                </h3>
                                <div className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                                    <Key className="w-3 h-3" /> API Key: <code className="bg-muted px-1 rounded">{selectedContract.apiKey}</code>
                                </div>
                            </div>
                        </div>

                        {selectedContract.type === 'python' && !selectedContract.isSystem && (
                            <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/50 text-amber-800 dark:text-amber-200 text-xs px-3 py-2 rounded-md flex flex-col gap-1 shadow-sm">
                                <div className="flex items-start">
                                    <span className="mr-2 text-sm">⚠️</span>
                                    <div>
                                        <strong>Sandbox Mode Active:</strong> Ensure all logic is deterministic. Network requests and file accesses are strictly forbidden. The <code>import</code> keyword is globally disabled.
                                    </div>
                                </div>
                                <div className="ml-6 text-amber-700/80 dark:text-amber-300/80">
                                    <strong>Pre-loaded modules:</strong> The VM automatically injects <code>math</code> and <code>hashlib</code> into the global scope. Call them directly without importing (e.g., <code>result = math.sqrt(25)</code>).
                                </div>
                            </div>
                        )}

                        <div className="flex-1 relative">
                            {selectedContract.isSystem && (
                                <div className="absolute top-0 right-0 z-10 p-2 text-xs font-semibold text-muted-foreground bg-background/80 rounded-bl-lg border-l border-b">
                                    READ ONLY
                                </div>
                            )}
                            <CodeEditor
                                key={selectedContract.id}
                                value={selectedContract.code}
                                onChange={handleUpdateCode}
                                language={selectedContract.type}
                                readOnly={selectedContract.isSystem}
                            />
                        </div>
                    </div>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-muted-foreground border-2 border-dashed rounded-xl p-8 bg-muted/5 min-h-[400px]">
                        <Code className="w-12 h-12 mb-4 opacity-20" />
                        <p>Select a contract to edit or create a new one.</p>
                    </div>
                )}
            </div>
        </div>
    );
};
