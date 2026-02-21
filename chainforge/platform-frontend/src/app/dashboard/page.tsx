"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/store/auth";
import axios from "axios";
import { Plus, Server } from "lucide-react";
import { motion } from "framer-motion";

interface Project {
    id: number;
    name: string;
    description: string;
    created_at: string;
}

export default function DashboardPage() {
    const [projects, setProjects] = useState<Project[]>([]);
    const { token, isAuthenticated } = useAuthStore();

    const handleDelete = async (id: number) => {
        if (!confirm("Are you sure you want to delete this project? This action cannot be undone.")) return;

        try {
            await axios.delete(`http://localhost:8000/projects/${id}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setProjects(projects.filter(p => p.id !== id));
        } catch (error) {
            console.error("Failed to delete project:", error);
            alert("Failed to delete project");
        }
    };

    useEffect(() => {
        if (token) {
            axios.get("http://localhost:8000/projects/", {
                headers: { Authorization: `Bearer ${token}` }
            }).then(res => setProjects(res.data))
                .catch(err => console.error(err));
        }
    }, [token]);

    // Auth Bypass for demo
    // if (!isAuthenticated) { ... }

    return (
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-10">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
                    <p className="text-muted-foreground">Manage your blockchain networks.</p>
                </div>
                <Link href="/projects/create">
                    <Button>
                        <Plus className="mr-2 h-4 w-4" /> New Project
                    </Button>
                </Link>
            </div>

            {projects.length === 0 ? (
                <div className="flex flex-col items-center justify-center min-h-[300px] border rounded-lg border-dashed">
                    <Server className="h-10 w-10 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-medium">No projects yet</h3>
                    <p className="text-sm text-muted-foreground mb-4">Create your first blockchain network to get started.</p>
                    <Link href="/projects/create">
                        <Button variant="outline">Create Project</Button>
                    </Link>
                </div>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {projects.map((project) => (
                        <motion.div key={project.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                            <Card>
                                <CardHeader>
                                    <CardTitle>{project.name}</CardTitle>
                                    <CardDescription>{project.description || "No description"}</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-xs text-muted-foreground">
                                        Created: {new Date(project.created_at).toLocaleDateString()}
                                    </div>
                                </CardContent>
                                <CardFooter className="flex justify-between">
                                    <Link href={`/projects/${project.id}`}>
                                        <Button variant="secondary" size="sm">Download</Button>
                                    </Link>
                                    <Button variant="ghost" size="sm" className="text-destructive" onClick={() => handleDelete(project.id)}>Delete</Button>
                                </CardFooter>
                            </Card>
                        </motion.div>
                    ))}
                </div>
            )}
        </div>
    );
}
