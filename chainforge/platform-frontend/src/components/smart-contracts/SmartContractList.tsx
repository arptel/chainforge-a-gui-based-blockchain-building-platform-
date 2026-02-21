import React, { useState } from 'react';
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
    type: 'python' | 'solidity';
    code: string;
    apiKey: string;
}

interface SmartContractListProps {
    contracts: SmartContract[];
    onChange: (contracts: SmartContract[]) => void;
}

export const SmartContractList: React.FC<SmartContractListProps> = ({ contracts = [], onChange }) => {
    const [selectedContractId, setSelectedContractId] = useState<string | null>(null);
    const [newContractName, setNewContractName] = useState("");
    const [newContractType, setNewContractType] = useState<'python' | 'solidity'>('python');

    const selectedContract = contracts.find(c => c.id === selectedContractId);

    const handleAddContract = () => {
        if (!newContractName) return;

        // Simple Boilerplate
        const boilerplate = newContractType === 'python' ?
            `class ${newContractName}:
    def __init__(self):
        pass` :
            `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ${newContractName} {
    constructor() {}
}`;

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
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 h-full min-h-[400px]">
            {/* Sidebar List */}
            <div className="md:col-span-1 border rounded-xl overflow-hidden flex flex-col bg-background">
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
                                    <SelectItem value="python">Python</SelectItem>
                                    <SelectItem value="solidity">Solidity</SelectItem>
                                </SelectContent>
                            </Select>
                            <Button onClick={handleAddContract} size="sm" className="flex-1" disabled={!newContractName}>
                                <Plus className="w-4 h-4 mr-1" /> Add
                            </Button>
                        </div>
                    </div>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-2">
                    {contracts.length === 0 && (
                        <div className="text-center text-muted-foreground py-8 text-sm">
                            No contracts added yet.
                        </div>
                    )}
                    {contracts.map(c => (
                        <div
                            key={c.id}
                            className={`p-3 rounded-lg border cursor-pointer flex justify-between items-center group transition-all ${selectedContractId === c.id ? 'border-primary bg-primary/5 shadow-sm' : 'hover:bg-accent'}`}
                            onClick={() => setSelectedContractId(c.id)}
                        >
                            <div className="flex items-center gap-3 overflow-hidden">
                                <div className={`p-2 rounded-md ${c.type === 'python' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-700'}`}>
                                    <Code className="w-4 h-4" />
                                </div>
                                <div className="truncate">
                                    <div className="font-medium truncate">{c.name}</div>
                                    <div className="text-xs text-muted-foreground uppercase">{c.type}</div>
                                </div>
                            </div>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
                                onClick={(e) => { e.stopPropagation(); handleDelete(c.id); }}
                            >
                                <Trash2 className="w-4 h-4" />
                            </Button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Editor Area */}
            <div className="md:col-span-3 flex flex-col">
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

                        <div className="flex-1">
                            <CodeEditor
                                value={selectedContract.code}
                                onChange={handleUpdateCode}
                                language={selectedContract.type}
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
