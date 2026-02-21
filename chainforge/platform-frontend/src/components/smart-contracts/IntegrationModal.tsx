import React, { useState } from 'react';
import { Modal } from '../ui/modal';
import { Button } from '../ui/button';
import { FileCode, Copy, Check, Terminal, Code, Key, HelpCircle } from 'lucide-react';

interface IntegrationModalProps {
    isOpen: boolean;
    onClose: () => void;
    contract: any;
    initialTab?: 'code' | 'integration' | 'uses';
}

export function IntegrationModal({ isOpen, onClose, contract, initialTab = 'code' }: IntegrationModalProps) {
    const [activeTab, setActiveTab] = useState<'code' | 'integration' | 'uses'>(initialTab);
    const [copied, setCopied] = useState(false);

    // Reset tab when opening with a new initialTab
    React.useEffect(() => {
        if (isOpen) {
            setActiveTab(initialTab);
        }
    }, [isOpen, initialTab]);

    if (!contract) return null;

    const safeName = contract.name.replace(/[^a-zA-Z0-9_]/g, "");

    const pythonCode = `
# 1. Install dependencies
# pip install requests

# 2. Use the generated SDK (recommended)
from sdk.client import Client

client = Client(base_url="http://localhost:8000")

# Call method on '${contract.name}'
# Arguments must match your contract's method signature
result = client.${safeName}.your_method_name(arg1="value")
print(result)
`.trim();

    const curlCode = `
curl -X POST http://localhost:8000/api/v1/contracts/execute/${contract.id}/your_method_name \\
  -H "Content-Type: application/json" \\
  -H "x-api-key: ${contract.apiKey}" \\
  -d '{"args": {"arg1": "value"}}'
`.trim();

    const handleCopy = (text: string) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const renderCodeBlock = (code: string) => (
        <div className="relative group">
            <pre className="bg-slate-950 text-slate-50 p-4 rounded-lg text-xs overflow-x-auto max-h-[400px]">
                <code>{code}</code>
            </pre>
            <Button
                variant="secondary"
                size="icon"
                className="absolute top-2 right-2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => handleCopy(code)}
            >
                {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
            </Button>
        </div>
    );

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={contract.name}>
            <div className="flex border-b mb-4">
                <button
                    className={`px-4 py-2 text-sm font-medium ${activeTab === 'code' ? 'border-b-2 border-primary text-primary' : 'text-muted-foreground hover:text-foreground'}`}
                    onClick={() => setActiveTab('code')}
                >
                    <div className="flex items-center"><Code className="w-4 h-4 mr-2" /> Source Code</div>
                </button>
                <button
                    className={`px-4 py-2 text-sm font-medium ${activeTab === 'integration' ? 'border-b-2 border-primary text-primary' : 'text-muted-foreground hover:text-foreground'}`}
                    onClick={() => setActiveTab('integration')}
                >
                    <div className="flex items-center"><Terminal className="w-4 h-4 mr-2" /> How to Use</div>
                </button>
                <button
                    className={`px-4 py-2 text-sm font-medium ${activeTab === 'uses' ? 'border-b-2 border-primary text-primary' : 'text-muted-foreground hover:text-foreground'}`}
                    onClick={() => setActiveTab('uses')}
                >
                    <div className="flex items-center"><HelpCircle className="w-4 h-4 mr-2" /> Function Uses</div>
                </button>
            </div>

            <div className="mt-4">
                {activeTab === 'code' && (
                    <div className="space-y-4">
                        <p className="text-sm text-muted-foreground">Smart Contract Logic ({contract.type})</p>
                        {renderCodeBlock(contract.code || "# No source code available")}
                    </div>
                )}

                {activeTab === 'integration' && (
                    <div className="space-y-6">
                        <div>
                            <h4 className="text-sm font-medium mb-2 flex items-center">
                                <Key className="w-4 h-4 mr-2" /> API Key
                            </h4>
                            <div className="relative group">
                                <pre className="bg-slate-950 text-slate-50 p-4 rounded-lg text-xs overflow-x-auto font-mono">
                                    {contract.apiKey}
                                </pre>
                                <Button
                                    variant="secondary"
                                    size="sm"
                                    className="absolute top-2 right-2 h-7 opacity-0 group-hover:opacity-100 transition-opacity"
                                    onClick={() => handleCopy(contract.apiKey)}
                                >
                                    {copied ? <Check className="h-3 w-3 mr-1" /> : <Copy className="h-3 w-3 mr-1" />}
                                    <span className="text-xs">Copy</span>
                                </Button>
                            </div>
                        </div>

                        <div>
                            <h4 className="text-sm font-medium mb-2 flex items-center">
                                <FileCode className="w-4 h-4 mr-2" /> Python SDK (Recommended)
                            </h4>
                            {renderCodeBlock(pythonCode)}
                        </div>

                        <div>
                            <h4 className="text-sm font-medium mb-2">cURL / Raw API</h4>
                            {renderCodeBlock(curlCode)}
                        </div>

                        <div className="text-xs text-muted-foreground p-3 bg-secondary/50 rounded-md">
                            <strong>Note:</strong> The SDK is included in the project ZIP file under the <code>sdk/</code> directory.
                        </div>
                    </div>
                )}

                {activeTab === 'uses' && (
                    <div className="space-y-4">
                        <h4 className="font-semibold text-lg border-b pb-2">What can {contract.name} be used for?</h4>
                        {contract.name === 'DataStore' && (
                            <div className="space-y-4 text-sm text-muted-foreground">
                                <p><strong>DataStore</strong> provides a simple key-value database on the blockchain.</p>
                                <ul className="list-disc pl-5 space-y-2 text-foreground">
                                    <li><code>store(key, value)</code>: Saves a string value to a specific string key. <em>Useful for storing user preferences, document hashes, or configuration flags.</em></li>
                                    <li><code>retrieve(key)</code>: Fetches the stored value for a given key. <em>Useful for verifying off-chain data against on-chain records.</em></li>
                                </ul>
                            </div>
                        )}
                        {contract.name === 'Governance' && (
                            <div className="space-y-4 text-sm text-muted-foreground">
                                <p><strong>Governance</strong> allows for decentralized decision-making through voting.</p>
                                <ul className="list-disc pl-5 space-y-2 text-foreground">
                                    <li><code>propose(proposalId, description)</code>: Creates a new proposal for users to vote on. <em>Useful for protocol upgrades, treasury spending, or rule changes.</em></li>
                                    <li><code>vote(proposalId)</code>: Casts a vote in favor of a specific proposal. <em>Used by community members to approve actions.</em></li>
                                    <li><code>getProposal(proposalId)</code>: Returns the description and current vote count of a proposal.</li>
                                </ul>
                            </div>
                        )}
                        {contract.name === 'SimpleToken' && (
                            <div className="space-y-4 text-sm text-muted-foreground">
                                <p><strong>SimpleToken</strong> implements a basic digital asset.</p>
                                <ul className="list-disc pl-5 space-y-2 text-foreground">
                                    <li><code>mint(to, amount)</code>: Creates new tokens and assigns them to an address. <em>Useful for rewarding users or initial distribution.</em></li>
                                    <li><code>transfer(to, amount)</code>: Sends tokens from your balance to another address. <em>Used for payments, trading, or transferring value.</em></li>
                                </ul>
                            </div>
                        )}
                        {!['DataStore', 'Governance', 'SimpleToken'].includes(contract.name) && (
                            <div className="space-y-4 text-sm text-muted-foreground">
                                <p>This is a custom contract. Its functions and use cases depend entirely on the logic you have written in the source code.</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </Modal>
    );
}
