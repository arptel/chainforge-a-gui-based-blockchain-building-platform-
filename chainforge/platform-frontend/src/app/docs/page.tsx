"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { 
  BookOpen, 
  Settings, 
  Code2, 
  Network, 
  Cpu, 
  ShieldCheck, 
  Zap, 
  Database,
  ArrowRight,
  Info
} from "lucide-react";
import Mermaid from "@/components/ui/mermaid";
import { motion } from "framer-motion";

const flowChart = `
flowchart TD
    A["🏠 Landing Page\n(/)"] -->|"Get Started"| B["🔐 Login\n(/login)"]
    A -->|"(has account)"| B
    B -->|"No account? Register"| C["📝 Register\n(/register)"]
    C -->|"After registration"| B
    B -->|"Authenticated"| D["📊 Dashboard\n(/dashboard)"]

    D -->|"Create New Project"| STEP1

    subgraph STEP1["Step 1 — Network Type & Security"]
        S1A["🌐 Public"]
        S1B["🔒 Permissioned"]
        S1C["🛡️ Require Digital Signatures"]
        S1D["🗝️ Implicit Trust (No Sigs)"]
    end

    S1A -->|"Next"| PUB_STEP2
    S1B -->|"Next"| PERM_STEP2

    subgraph PUB_STEP2["Step 2 — Consensus Mechanism (Public)"]
        P2A["⛏️ Proof of Work"]
        P2B["✅ Proof of Authority"]
        P2C["🪙 Proof of Stake"]
    end
    PUB_STEP2 -->|"Next"| PUB_STEP3

    subgraph PUB_STEP3["Step 3 — Smart Contract Runtime (Public)"]
        P3A["📦 WASM Runtime"]
        P3B["🔷 EVM Compatible"]
    end
    PUB_STEP3 -->|"Next"| PUB_STEP4

    subgraph PUB_STEP4["Step 4 — Synchronization Mode (Public)"]
        P4A["🗄️ Full Sync"]
        P4B["⚡ Fast Sync"]
        P4C["💡 Light Sync"]
    end
    PUB_STEP4 -->|"Next"| PUB_STEP5

    subgraph PUB_STEP5["Step 5 — Network Economy / Token (Public)"]
        P5A["🪙 Native Token"]
        P5B["🔒 No Token"]
    end
    PUB_STEP5 -->|"Next"| PUB_STEP6

    subgraph PUB_STEP6["Step 6 — Gas & Transaction Fees (Public)"]
        P6A["💰 Enable Gas Fees"]
        P6B["⚡ Gasless (Free)"]
    end
    PUB_STEP6 -->|"Next"| PUB_STEP7

    subgraph PUB_STEP7["Step 7 — Smart Contracts (Public)"]
        P7A["📄 Add / Configure Contracts (optional)"]
    end
    PUB_STEP7 -->|"Next"| PUB_REVIEW

    PUB_REVIEW["✅ Step 8 — Review & Create (Public)"] -->|"Create & Generate"| D2

    subgraph PERM_STEP2["Step 2 — Governance Model (Permissioned)"]
        Q2A["🏛️ Centralized"]
        Q2B["🏢 Consortium"]
    end

    Q2A -->|"Next"| CENT_STEP3
    Q2B -->|"Next"| CONS_STEP3

    subgraph CENT_STEP3["Step 3 — Central Authority Structure"]
        C3A["👑 Fixed Leader"]
        C3B["🔄 Rotating Leader"]
    end
    CENT_STEP3 -->|"Next"| CENT_STEP4

    subgraph CENT_STEP4["Step 4 — Consensus Algorithm (Centralized)"]
        C4A["🗄️ Raft (CFT)"]
        C4B["📄 Paxos (CFT)"]
        C4C["📝 None (Single-Writer)"]
    end
    CENT_STEP4 -->|"Next"| CENT_STEP5

    subgraph CENT_STEP5["Step 5 — Access Control (Centralized)"]
        C5A["🔑 Role-Based (RBAC)"]
        C5B["📋 Certificate Whitelist"]
    end
    CENT_STEP5 -->|"Next"| CENT_STEP6

    subgraph CENT_STEP6["Step 6 — Replication Mode (Centralized)"]
        C6A["⏱️ Real-Time"]
        C6B["📷 Snapshot"]
        C6C["📦 Batch"]
    end
    CENT_STEP6 -->|"Next"| PERM_STEP7

    subgraph CONS_STEP3["Step 3 — Validator Structure (Consortium)"]
        D3A["⚖️ Equal Validators"]
        D3B["👑 Weighted Validators"]
    end
    CONS_STEP3 -->|"Next"| CONS_STEP4

    subgraph CONS_STEP4["Step 4 — BFT Consensus (Consortium)"]
        D4A["🌐 PBFT"]
        D4B["⚡ HotStuff"]
        D4C["🔮 Tendermint"]
    end
    CONS_STEP4 -->|"Next"| CONS_STEP5

    subgraph CONS_STEP5["Step 5 — Member Identity (Consortium)"]
        D5A["✅ Certificate Authority (CA)"]
        D5B["🤝 Multi-Sig Approval"]
    end
    CONS_STEP5 -->|"Next"| CONS_STEP6

    subgraph CONS_STEP6["Step 6 — Synchronization (Consortium)"]
        D6A["🗄️ Full State"]
        D6B["📷 Snapshot"]
        D6C["💡 Light (SPV)"]
    end
    CONS_STEP6 -->|"Next"| PERM_STEP7

    subgraph PERM_STEP7["Step 7 — Gas & Transaction Fees (Permissioned)"]
        G1["💰 Enable Gas Fees"]
        G2["⚡ Gasless (Free)"]
    end
    PERM_STEP7 -->|"Next"| PERM_STEP8

    subgraph PERM_STEP8["Step 8 — Smart Contracts (Permissioned)"]
        SC["📄 Add / Configure Contracts (optional)"]
    end
    PERM_STEP8 -->|"Next"| PERM_REVIEW

    PERM_REVIEW["✅ Step 9 — Review & Create (Permissioned)"] -->|"Create & Generate"| D2

    D2["📊 Dashboard\n(/dashboard)\n(project now listed)"] -->|"Open Project"| PROJ["🔍 Project Detail\n(/projects/{id})"]

    classDef page fill:#1e293b,stroke:#6366f1,color:#f1f5f9,rx:8
    classDef action fill:#0f172a,stroke:#22d3ee,color:#f1f5f9,rx:4
    class A,B,C,D,D2,PROJ,PUB_REVIEW,PERM_REVIEW page
`;

export default function DocsPage() {
  return (
    <div className="container mx-auto py-10 px-4 md:px-8">
      <div className="flex flex-col lg:flex-row gap-8">
        {/* Sidebar Navigation */}
        <aside className="lg:w-64 hidden lg:block">
          <div className="sticky top-24 space-y-4">
            <h4 className="font-bold flex items-center gap-2"><BookOpen className="w-4 h-4" /> Documentation</h4>
            <nav className="flex flex-col space-y-2 text-sm">
              <a href="#overview" className="text-muted-foreground hover:text-primary transition-colors">Overview</a>
              <a href="#workflow" className="text-muted-foreground hover:text-primary transition-colors font-medium">Creation Wizard Flow</a>
              <a href="#network-types" className="text-muted-foreground hover:text-primary transition-colors">Network Types</a>
              <a href="#consensus" className="text-muted-foreground hover:text-primary transition-colors">Consensus Algorithms</a>
              <a href="#runtime" className="text-muted-foreground hover:text-primary transition-colors">Smart Contract Runtime</a>
            </nav>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 max-w-4xl space-y-12">
          {/* Hero Section */}
          <section id="overview" className="space-y-4">
            <Badge variant="outline" className="text-primary border-primary/20 bg-primary/5">Documentation</Badge>
            <h1 className="text-4xl font-bold tracking-tight">Understanding ChainForge</h1>
            <p className="text-xl text-muted-foreground leading-relaxed">
              ChainForge is a modular blockchain generation platform that allows you to design, test, and deploy custom distributed ledgers without manual consensus or networking code.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-6">
              {[
                { icon: <Zap className="text-amber-500" />, title: "Instant Generation", desc: "Turn configurations into production-ready Go/Python code instantly." },
                { icon: <ShieldCheck className="text-green-500" />, title: "Secure Defaults", desc: "Built-in ECDSA signatures and role-based access control." }
              ].map((item, i) => (
                <Card key={i} className="bg-secondary/20 border-border/50">
                  <CardContent className="p-4 flex gap-4 items-start">
                    <div className="p-2 rounded-lg bg-background border">{item.icon}</div>
                    <div>
                      <h4 className="font-semibold">{item.title}</h4>
                      <p className="text-sm text-muted-foreground">{item.desc}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <Separator />

          {/* Workflow Section */}
          <section id="workflow" className="space-y-6">
            <div className="flex items-center gap-2">
              <Network className="w-6 h-6 text-primary" />
              <h2 className="text-2xl font-bold">The Creation Wizard Flow</h2>
            </div>
            <p className="text-muted-foreground">
              The project creation process is structured as a multi-step wizard. Depending on your initial selection (Public vs. Permissioned), the platform branches into specific configuration paths.
            </p>

            <Card className="border-2 border-primary/10 overflow-hidden bg-slate-950/50">
              <CardHeader className="bg-secondary/10 border-b">
                <CardTitle className="text-lg">Interactive Flow Diagram</CardTitle>
                <CardDescription>Visual representation of the wizard logic and all available options.</CardDescription>
              </CardHeader>
              <CardContent className="p-0 sm:p-6">
                <div className="p-4 bg-slate-900/50 rounded-xl border border-slate-800">
                  <Mermaid chart={flowChart} id="main-flow" />
                </div>
              </CardContent>
            </Card>

            <div className="bg-blue-500/10 border border-blue-500/20 p-4 rounded-xl flex gap-4 items-start">
              <Info className="w-5 h-5 text-blue-500 mt-0.5" />
              <div className="text-sm">
                <p className="font-semibold text-blue-500">Pro Tip</p>
                <p className="text-blue-400">All configurations are validated in real-time. For example, selecting "POW" in a public network will automatically prompt for difficulty settings in the generated config.</p>
              </div>
            </div>
          </section>

          <Separator />

          {/* Detailed Features */}
          <section id="network-types" className="space-y-8">
            <div className="space-y-2">
              <h2 className="text-2xl font-bold">Configuration Deep Dive</h2>
              <p className="text-muted-foreground">Detailed breakdown of the core modules provided by ChainForge.</p>
            </div>

            <Tabs defaultValue="public" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="public">Public Networks</TabsTrigger>
                <TabsTrigger value="permissioned">Permissioned Networks</TabsTrigger>
              </TabsList>
              <TabsContent value="public" className="pt-6 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card className="p-4 bg-secondary/10">
                    <Cpu className="w-5 h-5 mb-2 text-orange-500" />
                    <h4 className="font-bold">Consensus</h4>
                    <p className="text-xs text-muted-foreground">Choose between POW for decentralization or POA for energy efficiency.</p>
                  </Card>
                  <Card className="p-4 bg-secondary/10">
                    <Database className="w-5 h-5 mb-2 text-blue-500" />
                    <h4 className="font-bold">Sync Modes</h4>
                    <p className="text-xs text-muted-foreground">Full Sync for archival nodes or Light Sync for client devices.</p>
                  </Card>
                  <Card className="p-4 bg-secondary/10">
                    <Zap className="w-5 h-5 mb-2 text-yellow-500" />
                    <h4 className="font-bold">Economy</h4>
                    <p className="text-xs text-muted-foreground">Enable native tokens with automated gas calculation and fee distribution.</p>
                  </Card>
                </div>
              </TabsContent>
              <TabsContent value="permissioned" className="pt-6 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card className="p-4 bg-secondary/10 border-l-4 border-l-red-500">
                    <h4 className="font-bold flex items-center justify-between">
                      Centralized Model <ArrowRight className="w-4 h-4" />
                    </h4>
                    <p className="text-xs text-muted-foreground mt-2">Optimized for high-throughput enterprise applications where a single authority manages the ledger with CFT (Crash Fault Tolerant) consensus like Raft.</p>
                  </Card>
                  <Card className="p-4 bg-secondary/10 border-l-4 border-l-purple-500">
                    <h4 className="font-bold flex items-center justify-between">
                      Consortium Model <ArrowRight className="w-4 h-4" />
                    </h4>
                    <p className="text-xs text-muted-foreground mt-2">Designed for multi-org collaboration. Uses BFT (Byzantine Fault Tolerant) algorithms like PBFT or Tendermint to handle adversarial environments.</p>
                  </Card>
                </div>
              </TabsContent>
            </Tabs>
          </section>

          <Separator />

          {/* API Documentation Section */}
          <section id="api" className="space-y-6">
            <div className="flex items-center gap-2">
              <Code2 className="w-6 h-6 text-primary" />
              <h2 className="text-2xl font-bold">Smart Contract API</h2>
            </div>
            <p className="text-muted-foreground">
              Interact with your generated smart contracts in seconds. ChainForge automatically generates REST API endpoints and secure API Keys for every contract you deploy.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h4 className="font-semibold flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-green-500" /> API Benefits</h4>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex gap-2">
                    <Badge variant="outline" className="h-5 px-1 bg-green-500/10 text-green-500">Secure</Badge>
                    <span>Enforced API Key authentication for every call.</span>
                  </li>
                  <li className="flex gap-2">
                    <Badge variant="outline" className="h-5 px-1 bg-blue-500/10 text-blue-500">Agnostic</Badge>
                    <span>Call from React, Python, Go, or any HTTP client.</span>
                  </li>
                  <li className="flex gap-2">
                    <Badge variant="outline" className="h-5 px-1 bg-purple-500/10 text-purple-500">Remote</Badge>
                    <span>Access your node from anywhere without direct imports.</span>
                  </li>
                </ul>
              </div>

              <div className="bg-slate-900 rounded-xl border p-4 font-mono text-xs overflow-x-auto space-y-4">
                <div className="flex justify-between items-center border-b border-slate-800 pb-2 mb-2">
                  <span className="text-slate-400">Example Request (Python)</span>
                  <Badge className="bg-emerald-500/20 text-emerald-400 border-none">POST</Badge>
                </div>
                <pre className="text-slate-300">
{`import requests

url = "http://node:8000/api/v1/execute"
headers = {"x-api-key": "sk_test_123"}
payload = {
  "contract_id": "storage_01",
  "method": "store",
  "args": {"value": 42}
}

resp = requests.post(url, json=payload, headers=headers)
print(resp.json())`}
                </pre>
              </div>
            </div>
          </section>

          <footer className="pt-12 pb-6 text-center text-sm text-muted-foreground border-t">
            <p>© 2026 ChainForge Platform. All educational documentation and diagrams are generated based on actual platform architecture.</p>
          </footer>
        </main>
      </div>
    </div>
  );
}
