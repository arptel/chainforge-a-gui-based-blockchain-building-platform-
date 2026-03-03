"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/store/auth";
import axios from "axios";
import {
    Download, Package, Server, Activity, Settings, Globe, Cpu, Layers, RefreshCw,
    Coins, Cloud, Shield, Crown, Database, Key, Timer, Scale, Network, BadgeCheck, ChevronLeft
} from "lucide-react";
import Link from "next/link";

import { IntegrationModal } from "@/components/smart-contracts/IntegrationModal";
import { FileCode, Code, Terminal } from "lucide-react";

export default function ProjectDetailsPage() {
    const { id } = useParams();
    const { token } = useAuthStore();
    const [project, setProject] = useState<any>(null);
    const [selectedContract, setSelectedContract] = useState<any>(null);
    const [modalTab, setModalTab] = useState<'code' | 'integration' | 'uses'>('code');

    useEffect(() => {
        if (token && id) {
            axios.get(`http://localhost:8000/projects/${id}`, {
                headers: { Authorization: `Bearer ${token}` }
            }).then(res => setProject(res.data));
        }
    }, [id, token]);

    const [isInstalling, setIsInstalling] = useState(false);

    const handleDownload = async () => {
        try {
            const response = await axios.post(`http://localhost:8000/generate/${id}/download`, {}, {
                headers: { Authorization: `Bearer ${token}` },
                responseType: 'blob'
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `chain_${id}.zip`);
            document.body.appendChild(link);
            link.click();
        } catch (e) {
            console.error("Download failed", e);
        }
    };

    const handleInstall = async () => {
        setIsInstalling(true);
        try {
            const res = await axios.post(`http://localhost:8000/generate/${id}/install`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            });
            alert(`Success: ${res.data.message}`);
        } catch (e: any) {
            console.error("Install failed", e);
            alert(`Install failed: ${e.response?.data?.detail || e.message}`);
        } finally {
            setIsInstalling(false);
        }
    };

    if (!project) return <div className="container py-20 flex justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

    return (
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-10 max-w-7xl">
            <div className="mb-8">
                <Link href="/dashboard" className="text-sm text-muted-foreground hover:text-foreground flex items-center mb-4 transition-colors">
                    <ChevronLeft className="h-4 w-4 mr-1" /> Back to Dashboard
                </Link>
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div>
                        <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
                            {project.name}
                        </h1>
                        <p className="text-muted-foreground mt-2 flex items-center">
                            <span className="bg-secondary px-2 py-0.5 rounded text-xs font-mono mr-2">ID: {project.id}</span>
                            Created on {new Date(project.created_at).toLocaleDateString()}
                        </p>
                    </div>
                </div>
            </div>

            <div className="grid gap-8 md:grid-cols-3">
                {/* Left Column: Actions & Status */}
                <div className="md:col-span-1 space-y-6">
                    <Card className="border-2 shadow-md overflow-hidden">
                        <div className="bg-gradient-to-br from-primary/10 via-primary/5 to-background p-6">
                            <h2 className="text-xl font-semibold mb-2 flex items-center">
                                <Package className="mr-2 h-5 w-5 text-primary" />
                                Actions
                            </h2>
                            <p className="text-sm text-muted-foreground mb-6">
                                Get your blockchain up and running.
                            </p>

                            <div className="space-y-3">
                                <Button
                                    className="w-full justify-start h-12 text-base font-medium"
                                    onClick={handleInstall}
                                    disabled={isInstalling}
                                >
                                    {isInstalling ? (
                                        <>Processing...</>
                                    ) : (
                                        <><Server className="mr-2 h-5 w-5" /> Install to Docker</>
                                    )}
                                </Button>
                                <Button
                                    variant="secondary"
                                    className="w-full justify-start h-12 text-base font-medium border"
                                    onClick={handleDownload}
                                >
                                    <Download className="mr-2 h-5 w-5" /> Download ZIP
                                </Button>
                            </div>
                        </div>
                        <div className="bg-muted/30 p-4 border-t text-xs text-muted-foreground">
                            <div className="flex items-start gap-2 mb-2">
                                <div className="min-w-4 mt-0.5"><span className="flex h-4 w-4 items-center justify-center rounded-full bg-primary/20 text-primary text-[10px] font-bold">1</span></div>
                                <p>Use <b>Install to Docker</b> to automatically build and run the network locally.</p>
                            </div>
                            <div className="flex items-start gap-2">
                                <div className="min-w-4 mt-0.5"><span className="flex h-4 w-4 items-center justify-center rounded-full bg-secondary text-secondary-foreground text-[10px] font-bold">2</span></div>
                                <p>Use <b>Download ZIP</b> to get the genesis block and config files for manual deployment.</p>
                            </div>
                        </div>
                    </Card>

                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-lg flex items-center"><Activity className="mr-2 h-5 w-5 text-green-500" /> System Status</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex items-center space-x-2 text-sm">
                                <span className="relative flex h-3 w-3">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                                </span>
                                <span className="font-medium text-green-600">Configuration Ready</span>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Right Column: Configuration Details */}
                <div className="md:col-span-2">
                    <Card className="h-full border shadow-sm">
                        <CardHeader>
                            <CardTitle className="flex items-center text-xl">
                                <Settings className="mr-2 h-5 w-5 text-gray-500" />
                                Network Configuration
                            </CardTitle>
                            <CardDescription>
                                Technical specifications for <b>{project.name}</b>
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <ConfigItem label="Network Type" value={project.config.networkType} icon={<Globe className="text-blue-500" />} />

                                {project.config.networkType === 'public' && (
                                    <>
                                        <ConfigItem label="Consensus" value={project.config.publicConsensus} icon={<Cpu className="text-orange-500" />} />
                                        <ConfigItem label="Runtime" value={project.config.publicRuntime} icon={<Layers className="text-indigo-500" />} />
                                        <ConfigItem label="Sync Mode" value={project.config.publicSyncMode} icon={<RefreshCw className="text-green-500" />} />
                                        <ConfigItem label="Token Model" value={project.config.publicToken} icon={<Coins className="text-amber-500" />} />
                                        <ConfigItem label="Deployment" value={project.config.publicDeployment} icon={<Cloud className="text-sky-500" />} />
                                    </>
                                )}

                                {project.config.networkType === 'permissioned' && (
                                    <>
                                        <ConfigItem label="Permissioned Type" value={project.config.permissionedType} icon={<Shield className="text-red-500" />} />

                                        {project.config.permissionedType === 'centralized' ? (
                                            <>
                                                <ConfigItem label="Authority" value={project.config.centralizedAuthority} icon={<Crown className="text-yellow-500" />} />
                                                <ConfigItem label="Consensus" value={project.config.centralizedConsensus} icon={<Database className="text-emerald-500" />} />
                                                <ConfigItem label="Access Control" value={project.config.centralizedAccess} icon={<Key className="text-purple-500" />} />
                                                <ConfigItem label="Sync Mode" value={project.config.centralizedSync} icon={<Timer className="text-pink-500" />} />
                                                <ConfigItem label="Deployment" value={project.config.centralizedDeployment} icon={<Cloud className="text-sky-500" />} />
                                            </>
                                        ) : (
                                            <>
                                                <ConfigItem label="Validators" value={project.config.consortiumValidatorStruct} icon={<Scale className="text-indigo-500" />} />
                                                <ConfigItem label="Consensus" value={project.config.consortiumConsensus} icon={<Network className="text-cyan-500" />} />
                                                <ConfigItem label="Identity" value={project.config.consortiumIdentity} icon={<BadgeCheck className="text-blue-600" />} />
                                                <ConfigItem label="Sync Mode" value={project.config.consortiumSync} icon={<Activity className="text-lime-500" />} />
                                                <ConfigItem label="Deployment" value={project.config.consortiumDeployment} icon={<Cloud className="text-sky-500" />} />
                                            </>
                                        )}
                                    </>
                                )}
                            </div>

                            {/* Gas & Economy Section */}
                            <div className="mt-6 pt-6 border-t">
                                <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-widest mb-4 flex items-center">
                                    <Coins className="text-amber-500 w-4 h-4 mr-2" />
                                    Transaction Fees & Gas
                                </h3>
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                    <div className="p-3 border rounded-lg bg-card text-center">
                                        <div className="text-xs text-muted-foreground uppercase tracking-widest mb-1">Status</div>
                                        <div className="font-semibold">{project.config.enableGas !== false ? 'Enabled' : 'Free (Gasless)'}</div>
                                    </div>
                                    {project.config.enableGas !== false && (
                                        <>
                                            <div className="p-3 border rounded-lg bg-card text-center">
                                                <div className="text-xs text-muted-foreground uppercase tracking-widest mb-1">Min Price</div>
                                                <div className="font-semibold">{project.config.minGasPrice || 0} wei</div>
                                            </div>
                                            <div className="p-3 border rounded-lg bg-card text-center">
                                                <div className="text-xs text-muted-foreground uppercase tracking-widest mb-1">Contract Limit</div>
                                                <div className="font-semibold">{project.config.defaultGasLimit || 100000} ops</div>
                                            </div>
                                        </>
                                    )}
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
                {/* Smart Contracts Section */}
                {project.config.smartContracts && project.config.smartContracts.length > 0 && (
                    <div className="md:col-span-3 mt-8 space-y-8">
                        {/* Default Ecosystem Contracts */}
                        {project.config.smartContracts.filter((c: any) => c.isSystem).length > 0 && (
                            <Card className="border shadow-sm">
                                <CardHeader className="bg-primary/5 pb-4 border-b">
                                    <CardTitle className="flex items-center text-xl text-primary">
                                        <BadgeCheck className="mr-2 h-5 w-5" />
                                        Default System Contracts
                                    </CardTitle>
                                    <CardDescription>
                                        Pre-built infrastructure contracts included in your network.
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="pt-6">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {project.config.smartContracts.filter((c: any) => c.isSystem).map((c: any) => (
                                            <div key={c.id} className="flex flex-col p-4 border rounded-xl bg-card hover:border-primary/50 transition-colors">
                                                <div className="flex items-center space-x-4 mb-4">
                                                    <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                                                        <FileCode className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                                                    </div>
                                                    <div>
                                                        <h4 className="font-semibold">{c.name}</h4>
                                                        <div className="flex items-center space-x-2 text-xs text-muted-foreground mt-1">
                                                            <span className="uppercase bg-secondary px-1.5 py-0.5 rounded">{c.type}</span>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex space-x-2 mt-auto">
                                                    <Button variant="ghost" size="sm" className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/20" onClick={() => { setSelectedContract(c); setModalTab('uses'); }}>
                                                        Function Uses
                                                    </Button>
                                                    <Button variant="outline" size="sm" onClick={() => { setSelectedContract(c); setModalTab('code'); }}>
                                                        <Code className="h-4 w-4 mr-1" /> Code
                                                    </Button>
                                                    <Button variant="secondary" size="sm" onClick={() => { setSelectedContract(c); setModalTab('integration'); }}>
                                                        <Terminal className="h-4 w-4 mr-1" /> API
                                                    </Button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        )}

                        {/* Custom Contracts */}
                        {project.config.smartContracts.filter((c: any) => !c.isSystem).length > 0 && (
                            <Card className="border shadow-sm">
                                <CardHeader>
                                    <CardTitle className="flex items-center text-xl">
                                        <FileCode className="mr-2 h-5 w-5 text-purple-500" />
                                        Custom Smart Contracts
                                    </CardTitle>
                                    <CardDescription>
                                        Custom user-defined contracts deployed to the network.
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {project.config.smartContracts.filter((c: any) => !c.isSystem).map((c: any) => (
                                            <div key={c.id} className="flex flex-col p-4 border rounded-xl bg-card hover:border-primary/50 transition-colors">
                                                <div className="flex items-center space-x-4 mb-4">
                                                    <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                                                        <FileCode className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                                                    </div>
                                                    <div>
                                                        <h4 className="font-semibold">{c.name}</h4>
                                                        <div className="flex items-center space-x-2 text-xs text-muted-foreground mt-1">
                                                            <span className="uppercase bg-secondary px-1.5 py-0.5 rounded">{c.type}</span>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex space-x-2 mt-auto">
                                                    <Button variant="outline" size="sm" onClick={() => { setSelectedContract(c); setModalTab('code'); }}>
                                                        <Code className="h-4 w-4 mr-1" /> View Code
                                                    </Button>
                                                    <Button variant="secondary" size="sm" onClick={() => { setSelectedContract(c); setModalTab('integration'); }}>
                                                        <Terminal className="h-4 w-4 mr-1" /> How to Use
                                                    </Button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        )}
                    </div>
                )}
            </div>

            <IntegrationModal
                isOpen={!!selectedContract}
                onClose={() => setSelectedContract(null)}
                contract={selectedContract}
                initialTab={modalTab}
            />
        </div>
    );
}

function ConfigItem({ label, value, icon }: { label: string, value: string, icon: React.ReactNode }) {
    return (
        <div className="flex items-center p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors">
            <div className="mr-3 p-2 rounded-full bg-secondary/50">
                {/* Clone icon to enforce size if needed, or just rely on passed icon sizing */}
                <div className="h-5 w-5 flex items-center justify-center [&>svg]:h-5 [&>svg]:w-5">
                    {icon}
                </div>
            </div>
            <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider truncate">{label}</p>
                <p className="font-semibold capitalize text-foreground break-words">{value || "N/A"}</p>
            </div>
        </div>
    )
}
