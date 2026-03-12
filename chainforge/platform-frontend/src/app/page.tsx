"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";

export default function Home() {
  return (
    <div className="flex flex-col min-h-[calc(100vh-4rem)]">
      <main className="flex-1">
        <section className="space-y-6 pb-8 pt-6 md:pb-12 md:pt-10 lg:py-32">
          <div className="container mx-auto px-4 flex max-w-[64rem] flex-col items-center gap-4 text-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
            >
              <h1 className="font-heading text-3xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight bg-gradient-to-r dark:from-white dark:to-gray-500 from-gray-900 to-gray-500 bg-clip-text text-transparent">
                Build Your Own Blockchain <br /> in Minutes
              </h1>
            </motion.div>
            <p className="max-w-[42rem] leading-normal text-muted-foreground sm:text-xl sm:leading-8">
              ChainForge is the ultimate platform for designing, generating, and deploying custom blockchain networks without writing a single line of consensus code.
            </p>
            <div className="space-x-4">
              <Link href="/login">
                <Button size="lg" className="h-11 px-8">Get Started</Button>
              </Link>
              <Link href="/docs">
                <Button variant="outline" size="lg" className="h-11 px-8">Documentation</Button>
              </Link>
            </div>
          </div>
        </section>

        <section className="container mx-auto px-4 space-y-6 py-8 md:py-12 lg:py-24 bg-secondary/20 rounded-xl my-8">
          <div className="mx-auto flex max-w-[58rem] flex-col items-center space-y-4 text-center">
            <h2 className="font-heading text-3xl leading-[1.1] sm:text-3xl md:text-6xl font-bold">
              Features
            </h2>
            <p className="max-w-[85%] leading-normal text-muted-foreground sm:text-lg sm:leading-7">
              Everything you need to verify, build, and deploy.
            </p>
          </div>
          <div className="mx-auto grid justify-center gap-4 sm:grid-cols-2 md:max-w-[64rem] md:grid-cols-3">
            {[
              { title: "Visual Designer", desc: "Configure consensus, nodes, and governance via UI." },
              { title: "One-Click Deploy", desc: "Generate Docker-ready packages instantly." },
              { title: "Modular Core", desc: "Swap consensus algorithms and sync methods easily." }
            ].map((feature, i) => (
              <motion.div
                key={i}
                whileHover={{ y: -5 }}
                className="relative overflow-hidden rounded-lg border bg-background p-2"
              >
                <div className="flex h-[180px] flex-col justify-between rounded-md p-6">
                  <div className="space-y-2">
                    <h3 className="font-bold">{feature.title}</h3>
                    <p className="text-sm text-muted-foreground">{feature.desc}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
