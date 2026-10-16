import type { Metadata } from 'next';
import './globals.css';
import Link from 'next/link';
import React from 'react';

export const metadata: Metadata = {
  title: 'GraphSRE: Autonomous SRE & Code Brain',
  description: 'FalkorDB GraphBLAS, Multi-Agent Central Blackboard, Interactive Cytoscape.js SRE War Room',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#090D16] text-[#F8FAFC] min-h-screen flex flex-col">
        {/* Top Header */}
        <header className="border-b border-[#1E293B] bg-[#0F172A] px-6 py-3 flex justify-between items-center sticky top-0 z-50">
          <div className="flex items-center space-x-3">
            <Link href="/" className="flex items-center space-x-2">
              <span className="text-xl font-black bg-gradient-to-r from-blue-400 via-indigo-300 to-emerald-400 bg-clip-text text-transparent tracking-tight">
                GraphSRE
              </span>
            </Link>
            <span className="text-xs bg-[#1E293B] text-blue-400 font-mono px-2.5 py-0.5 rounded-full border border-blue-500/20 flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse inline-block" />
              <span>FalkorDB Central Blackboard</span>
            </span>
          </div>

          <nav className="flex items-center space-x-6 text-xs font-medium text-gray-400">
            <Link href="/" className="hover:text-white transition flex items-center space-x-1.5">
              <span>War Room</span>
            </Link>
            <Link href="/postmortems" className="hover:text-white transition flex items-center space-x-1.5">
              <span>Vector Memory & Postmortems</span>
            </Link>
            <Link href="/cicd-blast-gate" className="hover:text-white transition flex items-center space-x-1.5">
              <span>CI/CD Blast Gate</span>
            </Link>
          </nav>

          <div className="flex items-center space-x-3 text-xs">
            <span className="px-2.5 py-1 bg-red-950/80 border border-red-500/40 text-red-300 rounded font-semibold flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-ping inline-block" />
              <span>Active Sev: 1 (Outage)</span>
            </span>
            <span className="px-2.5 py-1 bg-emerald-950/80 border border-emerald-500/40 text-emerald-300 rounded font-mono">
              FalkorDB: Connected (GraphBLAS)
            </span>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 p-6 max-w-[1600px] w-full mx-auto">
          {children}
        </main>
      </body>
    </html>
  );
}
