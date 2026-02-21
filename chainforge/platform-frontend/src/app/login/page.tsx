"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { motion } from "framer-motion";
import axios from "axios";

export default function LoginPage() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const login = useAuthStore((state) => state.login);
    const router = useRouter();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            // In a real app, use env var for API URL
            const response = await axios.post("http://localhost:8000/auth/token",
                new URLSearchParams({
                    username: username,
                    password: password,
                }), {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            }
            );

            const { access_token } = response.data;
            login(access_token, username);
            router.push("/dashboard");
        } catch (err) {
            setError("Invalid credentials. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-[calc(100vh-4rem)] bg-background">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <Card className="w-[350px] border-border/50 shadow-lg backdrop-blur-sm bg-card/50">
                    <CardHeader>
                        <CardTitle>Welcome Back</CardTitle>
                        <CardDescription>Enter your credentials to access your projects.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleLogin}>
                            <div className="grid w-full items-center gap-4">
                                <div className="flex flex-col space-y-1.5">
                                    <Label htmlFor="username">Username</Label>
                                    <Input id="username" placeholder="Enter your username" value={username} onChange={(e) => setUsername(e.target.value)} required />
                                </div>
                                <div className="flex flex-col space-y-1.5">
                                    <Label htmlFor="password">Password</Label>
                                    <Input id="password" type="password" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} required />
                                </div>
                            </div>
                            {error && <p className="text-sm text-red-500 mt-2">{error}</p>}
                            <div className="mt-4">
                                <Button className="w-full" type="submit" disabled={loading}>
                                    {loading ? "Logging in..." : "Login"}
                                </Button>
                            </div>
                        </form>
                    </CardContent>
                    <CardFooter className="flex justify-center">
                        <p className="text-xs text-muted-foreground">
                            Don&apos;t have an account? <Link href="/register" className="text-primary hover:underline">Sign up</Link>
                        </p>
                    </CardFooter>
                </Card>
            </motion.div>
        </div>
    );
}
