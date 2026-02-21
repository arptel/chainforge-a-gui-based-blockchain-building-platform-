"use client";

import Link from "next/link"
import { useAuthStore } from "@/store/auth"
import { Button } from "@/components/ui/button"
import { useRouter } from "next/navigation"

export default function Header() {
    const { isAuthenticated, logout, user } = useAuthStore()
    const router = useRouter()

    const handleLogout = () => {
        logout()
        router.push("/login")
    }

    return (
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container mx-auto px-4 sm:px-6 lg:px-8 flex h-14 items-center">
                <div className="mr-4 hidden md:flex">
                    <Link href="/" className="mr-6 flex items-center space-x-2">
                        <span className="hidden font-bold sm:inline-block">ChainForge</span>
                    </Link>
                    <nav className="flex items-center space-x-6 text-sm font-medium">
                        <Link href="/dashboard" className="transition-colors hover:text-foreground/80 text-foreground/60">
                            Dashboard
                        </Link>
                        <Link href="/docs" className="transition-colors hover:text-foreground/80 text-foreground/60">
                            Documentation
                        </Link>
                    </nav>
                </div>
                <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
                    <div className="w-full flex-1 md:w-auto md:flex-none">
                        {/* Search or other items */}
                    </div>
                    <nav className="flex items-center space-x-2">
                        {isAuthenticated ? (
                            <>
                                <span className="text-sm text-muted-foreground mr-2">{user?.username}</span>
                                <Button variant="ghost" size="sm" onClick={handleLogout}>Logout</Button>
                            </>
                        ) : (
                            <>
                                <Link href="/login"><Button variant="ghost" size="sm">Login</Button></Link>
                                <Link href="/register"><Button size="sm">Get Started</Button></Link>
                            </>
                        )}
                    </nav>
                </div>
            </div>
        </header>
    )
}
