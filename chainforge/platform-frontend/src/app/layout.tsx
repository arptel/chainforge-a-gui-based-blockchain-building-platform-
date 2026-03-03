import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Header from "@/components/layout/header";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ChainForge - Blockchain Platform",
  description: "Design, Generate, and Deploy Custom Blockchains",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
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
            }, true);
            `
        }} />
      </head>
      <body className={inter.className}>
        <div className="relative flex min-h-screen flex-col">
          <Header />
          <div className="flex-1">{children}</div>
        </div>
      </body>
    </html>
  );
}
